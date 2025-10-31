"""
Experiment Prediction API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.dependencies import get_db
from app.services.experiment_service import ExperimentService
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


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
    experiment_type: str = Field(default="stability", description="Experiment type: stability, solubility, aggregation")
    
    # Optional 8 parameters
    pH: Optional[float] = Field(None, ge=0, le=14, description="pH value (0-14)")
    temperature_c: Optional[float] = Field(None, ge=-50, le=200, description="Temperature (°C)")
    concentration_mg_ml: Optional[float] = Field(None, gt=0, description="Concentration (mg/mL)")
    ionic_strength_mM: Optional[float] = Field(None, ge=0, description="Ionic strength (mM)")
    additive: Optional[str] = Field(None, description="Additive")
    time_min: Optional[float] = Field(None, ge=0, description="Time (minutes)")
    shear_rate_s1: Optional[float] = Field(None, ge=0, description="Shear rate (s⁻¹)")
    pressure_bar: Optional[float] = Field(None, ge=0, description="Pressure (bar)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "biomolecule_type": "protein",
                "biomolecule_name": "lysozyme",
                "experiment_type": "stability",
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
        min_items=1
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Number of most similar literature records to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input": {
                    "biomolecule_type": "protein",
                    "biomolecule_name": "lysozyme",
                    "experiment_type": "stability",
                    "pH": 7.0,
                    "temperature_c": 25.0,
                    "concentration_mg_ml": 10.0
                },
                "predict_parameters": ["ionic_strength_mM", "additive"],
                "top_k": 3
            }
        }


# Helper function: Get user ID from header (simplified implementation)
def get_user_id_from_header(authorization: Optional[str] = Header(None)) -> Optional[int]:
    """Get user ID from authorization header"""
    # TODO: Implement real JWT parsing logic
    # Currently returns None for anonymous users
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
        # Validate prediction parameters
        valid_params = [
            'pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
            'additive', 'time_min', 'shear_rate_s1', 'pressure_bar'
        ]
        
        for param in request.predict_parameters:
            if param not in valid_params:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid parameter: {param}. Valid values: {valid_params}"
                )
        
        # Convert input format
        user_input = request.input.model_dump()
        
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
        from app.repos import user_experiment_repo
        
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
        from app.repos import user_experiment_repo
        
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

