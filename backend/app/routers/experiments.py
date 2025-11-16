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
import jwt

# Add project root to path
# In Docker, use /workspace if it exists; otherwise calculate relative to __file__
if Path("/workspace").exists():
    project_root = Path("/workspace")
else:
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
        # Use absolute path for Docker environment
        models_base = project_root / "models"
        predictor = UnifiedPredictor(
            models_dir=str(models_base),
            iqr_file=str(models_base / "iqr_statistics.json")
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
    """Get user ID from authorization header JWT token
    
    Supports both real JWT tokens and mock tokens for development mode.
    Mock tokens start with 'dev-mock-token-' and will return user_id=1.
    """
    if not authorization:
        print("DEBUG: No authorization header provided")
        return None
    
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            print("DEBUG: Authorization header does not start with 'Bearer '")
            return None
        
        token = authorization.replace("Bearer ", "").strip()
        
        if not token:
            print("DEBUG: Token is empty after extraction")
            return None
        
        # Check for mock token (development mode)
        if token.startswith("dev-mock-token-"):
            print(f"DEBUG: Using mock token for development, returning user_id=1")
            return 1
        
        # Verify and decode real JWT token
        from backend.app.core.security import verify_token
        
        payload = verify_token(token)
        sub = payload.get("sub")  # JWT subject contains user_id (as string)
        
        if not sub:
            print("DEBUG: Token payload missing 'sub' field")
            return None
        
        # Token stores user_id as string, convert to int
        try:
            user_id = int(sub)
            print(f"DEBUG: Successfully extracted user_id={user_id} from token")
            return user_id
        except (ValueError, TypeError):
            # Fallback: if sub is username instead of user_id, query database
            print(f"DEBUG: 'sub' is not numeric, trying as username: {sub}")
            from backend.app.repos.user_repo import get_by_username
            user = get_by_username(db, sub)
            if user:
                print(f"DEBUG: Found user_id={user.id} for username={sub}")
                return user.id
            else:
                print(f"DEBUG: User not found for sub={sub}")
        
        return None
    except jwt.ExpiredSignatureError:
        print("DEBUG: Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"DEBUG: Invalid token: {e}")
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
        # Add result and confidence columns
        for extra_field in [
            "Result Value", 
            "Confidence Level"
        ]:
            if extra_field not in output_fieldnames:
                output_fieldnames.append(extra_field)
        
        # Add literature columns based on top_k (each literature has 2 columns: Info and DOI)
        for i in range(1, top_k + 1):
            lit_info_col = f"Literature {i} Info"
            lit_doi_col = f"Literature {i} DOI"
            if lit_info_col not in output_fieldnames:
                output_fieldnames.append(lit_info_col)
            if lit_doi_col not in output_fieldnames:
                output_fieldnames.append(lit_doi_col)
        
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
                similar_literature = prediction.get('similar_literature', [])
            else:
                # Filter out parameters that already exist in user_input
                # Only predict parameters that are missing or empty
                filtered_request_params = []
                skipped_params = []
                for param in parameter_list or []:
                    # Check if parameter exists in user_input and has a value
                    if param in user_input and user_input[param] not in (None, ""):
                        skipped_params.append(param)
                    else:
                        filtered_request_params.append(param)
                
                # If all requested parameters are already provided, skip prediction
                if not filtered_request_params:
                    # All requested parameters already have values, use existing values
                    predicted_parameters = {}
                    param_display_names = {
                        'pH': 'pH',
                        'temperature_c': 'Temperature',
                        'concentration_mg_ml': 'Concentration',
                        'ionic_strength_mM': 'Ionic Strength',
                        'additive': 'Additive',
                        'time_min': 'Time',
                        'shear_rate_s1': 'Shear Rate',
                        'pressure_bar': 'Pressure'
                    }
                    for param in parameter_list or []:
                        if param in user_input:
                            display_name = param_display_names.get(param, param)
                            predicted_parameters[param] = {
                                'status': 'already_provided',
                                'message': f'{display_name} already provided',
                                'provided_value': user_input[param],
                                'source': 'provided_in_csv'
                            }
                    prediction = {
                        'predicted_parameters': predicted_parameters,
                        'confidence': 1.0,  # High confidence since values are provided
                        'similar_literature': [],
                        'model_info': {
                            'note': f'All requested parameters ({", ".join(skipped_params)}) were already provided in CSV'
                        }
                    }
                else:
                    # Predict only missing parameters
                    prediction = service.predict_parameter(
                        user_input=user_input,
                        request_params=filtered_request_params,
                        user_id=user_id,
                        top_k=top_k
                    )
                    # Add skipped parameters with their provided values
                    if skipped_params:
                        predicted_params = prediction.get('predicted_parameters', {})
                        param_display_names = {
                            'pH': 'pH',
                            'temperature_c': 'Temperature',
                            'concentration_mg_ml': 'Concentration',
                            'ionic_strength_mM': 'Ionic Strength',
                            'additive': 'Additive',
                            'time_min': 'Time',
                            'shear_rate_s1': 'Shear Rate',
                            'pressure_bar': 'Pressure'
                        }
                        for param in skipped_params:
                            if param in user_input:
                                display_name = param_display_names.get(param, param)
                                predicted_params[param] = {
                                    'status': 'already_provided',
                                    'message': f'{display_name} already provided',
                                    'provided_value': user_input[param],
                                    'source': 'provided_in_csv'
                                }
                        prediction['predicted_parameters'] = predicted_params
                        if 'model_info' not in prediction:
                            prediction['model_info'] = {}
                        prediction['model_info']['skipped_params'] = skipped_params
                
                result_value = json.dumps(prediction.get('predicted_parameters', {}), ensure_ascii=False)
                confidence_value = prediction.get('confidence')
                similar_literature = prediction.get('similar_literature', [])

            # Extract literature metadata for CSV columns
            # Process top_k literature records in order of similarity
            row_copy = dict(row)
            row_copy["Result Value"] = result_value
            row_copy["Confidence Level"] = confidence_value
            
            # Process literature records in order (they are already sorted by similarity)
            for i in range(1, top_k + 1):
                lit_info_col = f"Literature {i} Info"
                lit_doi_col = f"Literature {i} DOI"
                
                if i <= len(similar_literature):
                    lit = similar_literature[i - 1]
                    # Extract title
                    title = (
                        lit.get('title') or 
                        (lit.get('literature', {}).get('title') if isinstance(lit.get('literature'), dict) else '') or 
                        ""
                    )
                    # Extract authors
                    authors = (
                        lit.get('authors') or 
                        (lit.get('literature', {}).get('authors') if isinstance(lit.get('literature'), dict) else '') or 
                        ""
                    )
                    # Extract year
                    pub_year = (
                        lit.get('pub_year') or 
                        (lit.get('literature', {}).get('pub_year') if isinstance(lit.get('literature'), dict) else None)
                    )
                    year = str(pub_year) if pub_year is not None else ""
                    # Extract DOI
                    doi = (
                        lit.get('doi') or 
                        (lit.get('literature', {}).get('doi') if isinstance(lit.get('literature'), dict) else '') or 
                        ""
                    )
                    
                    # Format: Title, Authors, Year in one cell
                    info_parts = []
                    if title:
                        info_parts.append(title)
                    if authors:
                        info_parts.append(authors)
                    if year:
                        info_parts.append(year)
                    lit_info = ", ".join(info_parts) if info_parts else ""
                    
                    row_copy[lit_info_col] = lit_info
                    row_copy[lit_doi_col] = doi
                else:
                    # No more literature records available
                    row_copy[lit_info_col] = ""
                    row_copy[lit_doi_col] = ""
            
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


@router.delete("/history")
async def delete_experiment_history(
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_user_id_from_header)
):
    """
    Delete all experiment records for the current user
    
    Requires login only - any logged-in user can delete their own experiment history.
    No additional permissions required.
    """
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        from backend.app.repos import user_experiment_repo
        
        deleted_count = user_experiment_repo.delete_user_experiments(db, user_id)
        
        return {
            "status": "success",
            "message": f"Successfully deleted {deleted_count} experiment record(s)",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


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

