"""
Literature Service Layer - Integrates Literature Retrieval with ML Prediction Results
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.repos import literature_repo
from literature_mining.storage.structured_store import StructuredStore


class LiteratureService:
    """Literature Service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.jsonl_store = StructuredStore()
    
    def load_literature_to_db(self) -> int:
        """
        Load literature data from JSONL file to database
        
        Returns:
            Number of imported records
        """
        # Read all records
        all_records = self.jsonl_store.read_all()
        
        if not all_records:
            return 0
        
        imported_count = 0
        
        for record_data in all_records:
            try:
                # Process literature metadata
                doi = record_data.get('source_doi')
                literature_id = None
                
                if doi:
                    # Find or create literature record
                    literature = literature_repo.get_literature_by_doi(self.db, doi)
                    if not literature:
                        literature = literature_repo.create_literature(
                            self.db,
                            doi=doi,
                            title=None,  # May not exist in JSONL
                            authors=None,
                            pub_year=None,
                            source=None
                        )
                    literature_id = literature.id
                
                # Create extraction record
                literature_repo.create_extraction_record(self.db, record_data, literature_id)
                imported_count += 1
                
            except Exception as e:
                print(f"Error importing record: {e}")
                continue
        
        return imported_count
    
    def find_similar_literature(
        self,
        ml_result: Dict[str, Any],
        biomolecule_name: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find most similar literature based on ML prediction results
        
        Args:
            ml_result: ML prediction result (contains parameter recommendations)
            biomolecule_name: Biomolecule name
            top_k: Return Top K most similar literature
        
        Returns:
            List of similar literature, including similarity scores and literature information
        """
        # Extract parameters from ML result
        # Extract parameters based on different ML result formats
        target_params = self._extract_params_from_ml_result(ml_result, biomolecule_name)
        
        # Get property type
        property_type = ml_result.get('property_type', 'stability')
        if property_type is None:
            property_type = 'stability'
        
        # Use biomolecule_name parameter
        if not biomolecule_name:
            biomolecule_name = ml_result.get('biomolecule_name')
        
        # Search similar records
        similar_records = literature_repo.search_similar_records(
            self.db,
            target_params=target_params,
            biomolecule_name=biomolecule_name,
            property_type=property_type,
            limit=top_k
        )
        
        return similar_records
    
    def _extract_params_from_ml_result(
        self,
        ml_result: Dict[str, Any],
        biomolecule_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract parameters from ML result
        
        Supports multiple ML result formats:
        - UnifiedPredictor output
        - DualTrackRecommender output
        - Other formats
        """
        target_params = {}
        
        # Try to extract from recommended_ranges
        if 'recommended_ranges' in ml_result:
            ranges = ml_result['recommended_ranges']
            for param, param_info in ranges.items():
                if isinstance(param_info, dict) and 'median' in param_info:
                    target_params[param] = param_info['median']
        
        # Try to extract from consensus_recommendations
        if 'recommendations' in ml_result and 'consensus' in ml_result['recommendations']:
            consensus = ml_result['recommendations']['consensus']
            for param, param_info in consensus.items():
                if isinstance(param_info, dict) and 'median' in param_info:
                    target_params[param] = param_info['median']
        
        # Try to read parameters directly
        param_fields = ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
                       'additive', 'time_min', 'shear_rate_s1', 'pressure_bar']
        
        for param in param_fields:
            if param in ml_result and ml_result[param] is not None:
                target_params[param] = ml_result[param]
        
        return target_params
    
    def get_evidence_for_prediction(
        self,
        user_input: Dict[str, Any],
        ml_prediction: Dict[str, Any],
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Provide literature evidence for prediction results
        
        Args:
            user_input: User input experimental conditions
            ml_prediction: ML prediction result
            top_k: Return Top K literature records
        
        Returns:
            Complete result with literature evidence
        """
        # Merge user input and ML recommendations
        combined_params = {}
        
        # Prioritize user input
        param_fields = ['pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
                       'additive', 'time_min', 'shear_rate_s1', 'pressure_bar']
        
        for param in param_fields:
            if param in user_input and user_input[param] is not None:
                combined_params[param] = user_input[param]
            elif param in ml_prediction and ml_prediction[param] is not None:
                combined_params[param] = ml_prediction[param]
        
        # Get biomolecule name
        biomolecule_name = user_input.get('biomolecule_name') or ml_prediction.get('biomolecule_name')
        
        # Search similar literature
        similar_literature = self.find_similar_literature(
            ml_result=ml_prediction,
            biomolecule_name=biomolecule_name,
            top_k=top_k
        )
        
        # Build complete result
        enhanced_result = {
            'prediction': ml_prediction,
            'evidence': {
                'top_similar_literature': similar_literature,
                'count': len(similar_literature)
            },
            'input_parameters': combined_params
        }
        
        return enhanced_result


def enhance_ml_result_with_literature(
    db: Session,
    ml_result: Dict[str, Any],
    user_input: Dict[str, Any],
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Enhance ML result with literature evidence
    
    This is a convenience function for other modules to call
    """
    service = LiteratureService(db)
    return service.get_evidence_for_prediction(user_input, ml_result, top_k)

