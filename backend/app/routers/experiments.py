"""
Experiment Prediction API Routes
"""
import csv
import json
from io import StringIO
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, AliasChoices
from backend.app.core.config import settings
from backend.app.core.dependencies import get_db
from backend.app.core.parameter_spec import (
    get_parameter_validator,
    ParameterValidationError,
)
from backend.app.services.experiment_service import ExperimentService
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


DEFAULT_COLUMN_MAPPING = {
    'biomolecule_type': 'Substance Category',
    'biomolecule_name': 'Substance Name',
    'property': 'Property',
    'experiment_type': 'Experiment Type',
    'pH': 'pH',
    'temperature_c': 'Temperature',
    'concentration_mg_ml': 'Concentration',
    'ionic_strength_mM': 'Ion Concentration',
    'time_min': 'Time',
    'additive': 'Additives',
    'shear_rate_s1': 'Shear Rate',
    'pressure_bar': 'Pressure'
}


def _build_validation_error_detail(exc: ParameterValidationError) -> Dict[str, Any]:
    detail = exc.to_dict()
    detail.update({
        "status": "error",
        "message": detail.get("message", "Parameter validation failed"),
    })
    return detail


def get_ml_predictor():
    """Get ML predictor instance"""
    try:
        from ml_engine.prediction.unified_predictor import UnifiedPredictor
        predictor = UnifiedPredictor(
            models_dir='models',
            iqr_file='models/iqr_statistics.json'
        )
        return predictor
    except Exception as e:
        print(f"Warning: Failed to load ML predictor: {e}")
        return None


# Pydantic model definitions
class ExperimentInput(BaseModel):
    """Experiment input model"""
    biomolecule_type: str = Field(..., description="Biomolecule type: protein, peptide, polysaccharide")
    biomolecule_name: str = Field(..., description="Biomolecule name, e.g. lysozyme")
    property: str = Field(
        ...,
        description="Experiment property: stability, solubility, aggregation",
        validation_alias=AliasChoices('property', 'experiment_type'),
    )

    # Optional 8 parameters
    pH: Optional[float] = Field(None, description="pH value")
    temperature_c: Optional[float] = Field(None, description="Temperature (°C)")
    concentration_mg_ml: Optional[float] = Field(None, description="Concentration (mg/mL)")
    ionic_strength_mM: Optional[float] = Field(None, description="Ionic strength (mM)")
    additive: Optional[str] = Field(None, description="Additive")
    time_min: Optional[float] = Field(None, description="Time (minutes)")
    shear_rate_s1: Optional[float] = Field(None, description="Shear rate (s⁻¹)")
    pressure_bar: Optional[float] = Field(None, description="Pressure (bar)")

    class Config:
        json_schema_extra = {
            "example": {
                "biomolecule_type": "protein",
                "biomolecule_name": "lysozyme",
                "property": "stability",
                "pH": 7.0,
                "temperature_c": 25.0,
                "concentration_mg_ml": 10.0,
                "ionic_strength_mM": 150.0,
                "additive": "glycerol",
                "time_min": 60.0,
                "shear_rate_s1": 100.0,
                "pressure_bar": 1.0
            }
        }


class ParameterPredictionRequest(BaseModel):
    """Parameter prediction request model"""
    input: ExperimentInput = Field(..., description="User input experimental conditions")
    predict_parameters: List[str] = Field(
        ...,
        description="List of parameters to predict. Valid values: pH, temperature_c, concentration_mg_ml, ionic_strength_mM, additive, time_min, shear_rate_s1, pressure_bar",
        min_items=1,
        validation_alias=AliasChoices('predict_parameters', 'recommend_parameters'),
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Number of most similar literature records to return")

    class Config:
        json_schema_extra = {
            "example": {
                "input": {
                    "biomolecule_type": "protein",
                    "biomolecule_name": "lysozyme",
                    "property": "stability",
                    "pH": 7.0,
                    "temperature_c": 25.0,
                    "concentration_mg_ml": 10.0
                },
                "predict_parameters": ["ionic_strength_mM", "additive"],
                "top_k": 3
            }
        }


# Helper function: Get user ID from header
def get_user_id_from_header(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
) -> Optional[int]:
    """Get user ID from authorization header JWT token"""
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            return None
        
        token = authorization.replace("Bearer ", "").strip()
        
        # Verify and decode token
        from backend.app.core.security import verify_token
        
        payload = verify_token(token)
        sub = payload.get("sub")  # JWT subject contains user_id (as string)
        
        if not sub:
            return None
        
        # Token stores user_id as string, convert to int
        try:
            user_id = int(sub)
            print(f"DEBUG: Found user_id={user_id} from token")
            return user_id
        except (ValueError, TypeError):
            # Fallback: if sub is username instead of user_id, query database
            from backend.app.repos.user_repo import get_by_username
            user = get_by_username(db, sub)
            if user:
                print(f"DEBUG: Found user_id={user.id} for username={sub}")
                return user.id
            else:
                print(f"DEBUG: User not found for sub={sub}")
        
        return None
    except Exception as e:
        # If token is invalid or expired, return None (anonymous user)
        print(f"DEBUG: Failed to get user_id from header: {e}")
        import traceback
        traceback.print_exc()
        return None


@router.post("/predict-classification")
async def predict_classification(
    experiment: ExperimentInput,
    top_k: int = 3,
    db: Session = Depends(get_db),
    predictor = Depends(get_ml_predictor),
    user_id: Optional[int] = Depends(get_user_id_from_header)
):
    """
    Function 1: Determine if experimental conditions are reasonable (Good/Bad)
    
    User inputs biomolecule type, name, experiment type, and any combination of 8 optional parameters.
    System returns prediction result (Good/Bad) and related literature.
    """
    try:
        # Convert input format
        user_input = experiment.model_dump()

        if settings.parameter_validation_enabled:
            validator = get_parameter_validator()
            try:
                validation = validator.validate(
                    user_input,
                    context="predict-classification",
                )
                user_input = validation.normalized_payload
            except ParameterValidationError as exc:
                raise HTTPException(status_code=422, detail=_build_validation_error_detail(exc)) from exc

        # Create service instance
        service = ExperimentService(db, ml_predictor=predictor)

        # Execute prediction
        result = service.predict_classification(
            user_input=user_input,
            user_id=user_id,
            top_k=top_k
        )
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict-parameter")
async def predict_parameter(
    request: ParameterPredictionRequest,
    db: Session = Depends(get_db),
    predictor = Depends(get_ml_predictor),
    user_id: Optional[int] = Depends(get_user_id_from_header)
):
    """
    Function 2: Predict values for specified parameters
    
    After user inputs experimental conditions, select one or more parameters to predict.
    System returns predicted values, confidence, and related literature.
    """
    try:
        # Convert input format
        user_input = request.input.model_dump()

        validator = get_parameter_validator()
        valid_params = validator.optional_field_names()

        for param in request.predict_parameters:
            if param not in valid_params:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message": f"Invalid parameter: {param}",
                        "errors": [
                            {
                                "field": "predict_parameters",
                                "code": "invalid_choice",
                                "message": f"Parameter '{param}' is not supported",
                                "expected": {"allowed": valid_params},
                            }
                        ],
                    },
                )

        if settings.parameter_validation_enabled:
            try:
                validation = validator.validate(
                    user_input,
                    context="predict-parameter",
                )
                user_input = validation.normalized_payload
            except ParameterValidationError as exc:
                raise HTTPException(status_code=422, detail=_build_validation_error_detail(exc)) from exc

        # Create service instance
        service = ExperimentService(db, ml_predictor=predictor)

        # Execute prediction
        result = service.predict_parameter(
            user_input=user_input,
            request_params=request.predict_parameters,
            user_id=user_id,
            top_k=request.top_k
        )
        
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict-csv")
async def predict_from_csv(
    file: UploadFile = File(..., description="CSV file containing experiment definitions"),
    prediction_type: str = Form(
        "classification",
        description="Type of prediction to run: classification or parameter"
    ),
    top_k: int = Form(3, description="Number of literature records to return"),
    column_mapping: Optional[str] = Form(
        None,
        description="JSON mapping from experiment fields to CSV column names"
    ),
    predict_parameters: Optional[str] = Form(
        None,
        description="JSON list of parameters to predict when prediction_type=parameter"
    ),
    db: Session = Depends(get_db),
    predictor = Depends(get_ml_predictor),
    user_id: Optional[int] = Depends(get_user_id_from_header)
):
    """Run batch experiment predictions from an uploaded CSV file."""

    if prediction_type not in {"classification", "parameter"}:
        raise HTTPException(
            status_code=400,
            detail="prediction_type must be either 'classification' or 'parameter'"
        )

    try:
        mapping = DEFAULT_COLUMN_MAPPING.copy()
        if column_mapping:
            try:
                mapping.update(json.loads(column_mapping))
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid column_mapping JSON: {exc}"
                ) from exc

        parameter_list: Optional[List[str]] = None
        if predict_parameters:
            try:
                parsed_params = json.loads(predict_parameters)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid predict_parameters JSON: {exc}"
                ) from exc

            if not isinstance(parsed_params, list):
                raise HTTPException(
                    status_code=400,
                    detail="predict_parameters must be a JSON list"
                )
            parameter_list = parsed_params

        if prediction_type == "parameter" and not parameter_list:
            raise HTTPException(
                status_code=400,
                detail="predict_parameters is required when prediction_type is 'parameter'"
            )

        raw_content = await file.read()
        try:
            decoded_content = raw_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            decoded_content = raw_content.decode("utf-8")

        csv_reader = csv.DictReader(StringIO(decoded_content))
        if csv_reader.fieldnames is None:
            raise HTTPException(status_code=400, detail="CSV file must contain a header row")

        service = ExperimentService(db, ml_predictor=predictor)

        numeric_fields = {
            'pH', 'temperature_c', 'concentration_mg_ml',
            'ionic_strength_mM', 'time_min', 'shear_rate_s1', 'pressure_bar'
        }

        output_buffer = StringIO()
        output_fieldnames = list(csv_reader.fieldnames)
        for extra_field in ["Result Value", "Confidence Level", "Related Literature"]:
            if extra_field not in output_fieldnames:
                output_fieldnames.append(extra_field)
        csv_writer = csv.DictWriter(output_buffer, fieldnames=output_fieldnames)
        csv_writer.writeheader()

        validator = get_parameter_validator()

        for row in csv_reader:
            if not any(value.strip() for value in row.values() if isinstance(value, str)):
                # Skip completely empty rows
                continue

            user_input: Dict[str, Any] = {}
            for field, column_name in mapping.items():
                if column_name in row and row[column_name] not in (None, ""):
                    value = row[column_name]
                    if field in numeric_fields:
                        try:
                            user_input[field] = float(value)
                        except (TypeError, ValueError):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid numeric value '{value}' for column '{column_name}'"
                            )
                    else:
                        user_input[field] = value

            # Provide defaults for required fields if missing
            if 'biomolecule_type' not in user_input:
                raise HTTPException(
                    status_code=400,
                    detail="CSV data missing biomolecule_type information"
                )
            if 'biomolecule_name' not in user_input:
                raise HTTPException(
                    status_code=400,
                    detail="CSV data missing biomolecule_name information"
                )
            if 'property' not in user_input and 'experiment_type' in user_input:
                user_input['property'] = user_input['experiment_type']
            user_input.setdefault('property', 'stability')

            if settings.parameter_validation_enabled:
                try:
                    validation = validator.validate(
                        user_input,
                        context="predict-csv",
                    )
                    user_input = validation.normalized_payload
                except ParameterValidationError as exc:
                    raise HTTPException(status_code=422, detail=_build_validation_error_detail(exc)) from exc

            if prediction_type == "classification":
                prediction = service.predict_classification(
                    user_input=user_input,
                    user_id=user_id,
                    top_k=top_k
                )
                result_value = prediction.get('prediction')
                confidence_value = prediction.get('confidence')
                literature_value = json.dumps(prediction.get('similar_literature', []), ensure_ascii=False)
            else:
                prediction = service.predict_parameter(
                    user_input=user_input,
                    request_params=parameter_list or [],
                    user_id=user_id,
                    top_k=top_k
                )
                result_value = json.dumps(prediction.get('predicted_parameters', {}), ensure_ascii=False)
                confidence_value = prediction.get('confidence')
                literature_value = json.dumps(prediction.get('similar_literature', []), ensure_ascii=False)

            row_copy = dict(row)
            row_copy["Result Value"] = result_value
            row_copy["Confidence Level"] = confidence_value
            row_copy["Related Literature"] = literature_value
            csv_writer.writerow(row_copy)

        output_buffer.seek(0)
        filename = file.filename or "predictions.csv"
        return StreamingResponse(
            iter([output_buffer.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=predictions_{filename}"
            }
        )

    except HTTPException:
        raise
    except csv.Error as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CSV prediction failed: {exc}") from exc


@router.get("/history")
async def get_experiment_history(
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_user_id_from_header)
):
    """
    Get user's historical prediction records
    
    Returns user's previous prediction requests and usage history.
    """
    try:
        from backend.app.repos import user_experiment_repo
        
        records = user_experiment_repo.get_user_experiments(
            db, user_id=user_id, limit=limit
        )
        
        return {
            "status": "success",
            "count": len(records),
            "data": [record.to_dict() for record in records]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/{experiment_id}")
async def get_experiment_by_id(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get experiment record details by ID
    """
    try:
        from backend.app.repos import user_experiment_repo
        
        record = user_experiment_repo.get_experiment_by_id(db, experiment_id)
        
        if record is None:
            raise HTTPException(status_code=404, detail="Experiment record not found")
        
        return {
            "status": "success",
            "data": record.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

