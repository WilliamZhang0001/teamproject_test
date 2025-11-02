"""
Literature API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.core.dependencies import get_db
from backend.app.services.literature_service import LiteratureService
from backend.app.repos import literature_repo

router = APIRouter(prefix="/literature", tags=["literature"])


@router.post("/load")
async def load_literature_to_db(db: Session = Depends(get_db)):
    """
    Load literature data from JSONL file to database
    
    This is a one-time operation for database initialization
    """
    try:
        service = LiteratureService(db)
        count = service.load_literature_to_db()
        return {
            "status": "success",
            "message": f"Successfully imported {count} literature records",
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/search")
async def search_similar_literature(
    biomolecule_name: str = None,
    property_type: str = "stability",
    pH: float = None,
    temperature_c: float = None,
    concentration_mg_ml: float = None,
    ionic_strength_mM: float = None,
    additive: str = None,
    time_min: float = None,
    shear_rate_s1: float = None,
    pressure_bar: float = None,
    limit: int = 3,
    db: Session = Depends(get_db)
):
    """
    Search similar literature
    
    Args:
        biomolecule_name: Biomolecule name
        property_type: Property type (stability/solubility/etc.)
        pH: pH value
        temperature_c: Temperature
        concentration_mg_ml: Concentration
        ionic_strength_mM: Ionic strength
        additive: Additive name
        time_min: Time in minutes
        shear_rate_s1: Shear rate
        pressure_bar: Pressure in bar
        limit: Number of results to return
    """
    target_params = {}
    
    if pH is not None:
        target_params['pH'] = pH
    if temperature_c is not None:
        target_params['temperature_c'] = temperature_c
    if concentration_mg_ml is not None:
        target_params['concentration_mg_ml'] = concentration_mg_ml
    if ionic_strength_mM is not None:
        target_params['ionic_strength_mM'] = ionic_strength_mM
    if additive is not None and additive != '':
        target_params['additive'] = additive
    if time_min is not None:
        target_params['time_min'] = time_min
    if shear_rate_s1 is not None:
        target_params['shear_rate_s1'] = shear_rate_s1
    if pressure_bar is not None:
        target_params['pressure_bar'] = pressure_bar
    
    try:
        similar_records = literature_repo.search_similar_records(
            db,
            target_params=target_params,
            biomolecule_name=biomolecule_name,
            property_type=property_type,
            limit=limit
        )
        
        return {
            "status": "success",
            "count": len(similar_records),
            "results": similar_records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/enhance-prediction")
async def enhance_ml_prediction(
    ml_result: Dict[str, Any],
    user_input: Dict[str, Any] = None,
    top_k: int = 3,
    db: Session = Depends(get_db)
):
    """
    Enhance ML prediction results with literature evidence
    
    Args:
        ml_result: ML prediction result
        user_input: User input experimental conditions
        top_k: Return Top K literature records
    """
    try:
        if user_input is None:
            user_input = {}
        
        service = LiteratureService(db)
        enhanced_result = service.get_evidence_for_prediction(
            user_input=user_input,
            ml_prediction=ml_result,
            top_k=top_k
        )
        
        return enhanced_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/top-confidence")
async def get_top_confidence_records(
    biomolecule_name: str = None,
    property_type: str = "stability",
    limit: int = 3,
    db: Session = Depends(get_db)
):
    """
    Get high-confidence literature records
    
    Args:
        biomolecule_name: Biomolecule name
        property_type: Property type
        limit: Number of results to return
    """
    try:
        records = literature_repo.get_top_records_by_confidence(
            db,
            biomolecule_name=biomolecule_name,
            property_type=property_type,
            limit=limit
        )
        
        return {
            "status": "success",
            "count": len(records),
            "results": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

