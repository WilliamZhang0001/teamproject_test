"""
Experiment Prediction Service - Integrates ML Prediction and Literature Retrieval
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.repos import literature_repo, user_experiment_repo


class ExperimentService:
    """Experiment Prediction Service"""
    
    def __init__(self, db: Session, ml_predictor=None):
        """
        Initialize service
        
        Args:
            db: Database session
            ml_predictor: ML predictor instance (optional)
        """
        self.db = db
        self.ml_predictor = ml_predictor
    
    def predict_classification(
        self,
        user_input: Dict[str, Any],
        user_id: Optional[int] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Function 1: Determine if experimental conditions are reasonable (Good/Bad)
        
        Args:
            user_input: User input
                {
                    'biomolecule_type': 'protein',
                    'biomolecule_name': 'lysozyme',
                    'experiment_type': 'stability',
                    'pH': 7.0,
                    'temperature_c': 25.0,
                    'concentration_mg_ml': 10.0,
                    'ionic_strength_mM': 150.0,
                    'additive': None,
                    'time_min': None,
                    'shear_rate_s1': None,
                    'pressure_bar': None
                }
            user_id: User ID (optional)
            top_k: Return top K most similar literature
        
        Returns:
            Prediction result
        """
        # 1. Call ML model for prediction
        ml_result = self._call_ml_model(user_input)
        
        # 2. Search similar literature
        similar_literature = self._search_similar_literature(user_input, top_k)
        
        # 3. Build complete result
        result = {
            'biomolecule_type': user_input.get('biomolecule_type'),
            'biomolecule_name': user_input.get('biomolecule_name'),
            'experiment_type': user_input.get('experiment_type', 'stability'),
            'prediction': 'Good' if ml_result.get('is_stable') else 'Bad',
            'confidence': ml_result.get('confidence', 0.0),
            'input_parameters': self._extract_input_params(user_input),
            'similar_literature': similar_literature,
            'model_info': ml_result.get('model_info', {})
        }
        
        # 4. Save to database (if user_id is provided)
        if user_id is not None:
            self._save_experiment_record(user_id, user_input, result, 'classification')
        
        return result
    
    def predict_parameter(
        self,
        user_input: Dict[str, Any],
        request_params: List[str],
        user_id: Optional[int] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Function 2: Predict values for specified parameters
        
        Args:
            user_input: User input (contains known parameters)
            request_params: List of parameters to predict, e.g. ['pH', 'temperature_c']
            user_id: User ID (optional)
            top_k: Return top K most similar literature
        
        Returns:
            Prediction result
        """
        # 1. Call ML model for parameter recommendations
        ml_result = self._call_ml_model_for_recommendation(user_input, request_params)
        
        # 2. Search similar literature
        similar_literature = self._search_similar_literature(user_input, top_k)
        
        # 3. Build complete result
        result = {
            'biomolecule_type': user_input.get('biomolecule_type'),
            'biomolecule_name': user_input.get('biomolecule_name'),
            'experiment_type': user_input.get('experiment_type', 'stability'),
            'input_parameters': self._extract_input_params(user_input),
            'predicted_parameters': ml_result.get('predicted_parameters', {}),
            'confidence': ml_result.get('confidence', 0.0),
            'similar_literature': similar_literature,
            'model_info': ml_result.get('model_info', {})
        }
        
        # 4. Save to database (if user_id is provided)
        if user_id is not None:
            self._save_experiment_record(user_id, user_input, result, 'parameter_prediction')
        
        return result
    
    def _call_ml_model(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call ML model for classification prediction"""
        if self.ml_predictor is None:
            # If no predictor is provided, return default result
            return {
                'is_stable': True,
                'confidence': 0.5,
                'model_info': {'model': 'default'}
            }
        
        try:
            # Call ML predictor
            ml_result = self.ml_predictor.predict(user_input)
            
            # Extract prediction results
            is_good = ml_result.get('prediction') == 'Good'
            confidence = ml_result.get('confidence', 0.0)
            
            return {
                'is_stable': is_good,
                'confidence': confidence,
                'model_info': ml_result.get('details', {})
            }
        except Exception as e:
            print(f"Warning: ML prediction failed: {e}")
            return {
                'is_stable': True,
                'confidence': 0.5,
                'model_info': {'error': str(e)}
            }
    
    def _call_ml_model_for_recommendation(
        self,
        user_input: Dict[str, Any],
        request_params: List[str]
    ) -> Dict[str, Any]:
        """Call ML model for parameter recommendation"""
        if self.ml_predictor is None:
            # If no predictor is provided, return default ranges
            return {
                'predicted_parameters': {},
                'confidence': 0.5,
                'model_info': {'model': 'default'}
            }
        
        try:
            # Call ML predictor
            ml_result = self.ml_predictor.get_parameter_recommendations(
                user_input, request_params
            )
            
            # Extract recommended parameter ranges
            recommended_ranges = ml_result.get('recommended_ranges', {})
            predicted_parameters = {}
            
            # Extract median as recommended value from ranges
            for param, param_info in recommended_ranges.items():
                if isinstance(param_info, dict):
                    # UnifiedPredictor return format
                    if 'median' in param_info:
                        predicted_parameters[param] = {
                            'recommended_value': param_info.get('median'),
                            'min': param_info.get('min'),
                            'max': param_info.get('max'),
                            'unit': param_info.get('unit', ''),
                            'confidence': param_info.get('count', 0)
                        }
                    # Other possible formats
                    elif 'recommended_value' in param_info:
                        predicted_parameters[param] = param_info
                    else:
                        # Use all available information
                        predicted_parameters[param] = {
                            'recommended_value': param_info.get('q1', 0),
                            'min': param_info.get('q1'),
                            'max': param_info.get('q3'),
                            'confidence': param_info.get('count', 0)
                        }
            
            # Calculate average confidence
            confidence = ml_result.get('confidence', 0.0)
            if isinstance(confidence, str):
                confidence_map = {'high': 0.8, 'medium': 0.6, 'low': 0.4}
                confidence = confidence_map.get(confidence, 0.5)
            
            return {
                'predicted_parameters': predicted_parameters,
                'confidence': float(confidence) if confidence else 0.5,
                'model_info': {
                    'scenario': ml_result.get('scenario', 'parameter_recommendation'),
                    'note': ml_result.get('note', '')
                }
            }
        except Exception as e:
            print(f"Warning: ML recommendation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'predicted_parameters': {},
                'confidence': 0.5,
                'model_info': {'error': str(e)}
            }
    
    def _search_similar_literature(
        self,
        user_input: Dict[str, Any],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search similar literature"""
        try:
            # Extract parameters
            target_params = {}
            param_map = {
                'pH': 'pH',
                'temperature_c': 'temperature_c',
                'concentration_mg_ml': 'concentration_mg_ml',
                'ionic_strength_mM': 'ionic_strength_mM',
                'additive': 'additive',
                'time_min': 'time_min',
                'shear_rate_s1': 'shear_rate_s1',
                'pressure_bar': 'pressure_bar'
            }
            
            for input_key, db_key in param_map.items():
                if input_key in user_input and user_input[input_key] is not None:
                    target_params[db_key] = user_input[input_key]
            
            # Search similar records
            biomolecule_name = user_input.get('biomolecule_name')
            experiment_type = user_input.get('experiment_type', 'stability')
            
            similar_records = literature_repo.search_similar_records(
                self.db,
                target_params=target_params,
                biomolecule_name=biomolecule_name,
                property_type=experiment_type,
                limit=top_k
            )
            
            return similar_records
        except Exception as e:
            print(f"Warning: Literature search failed: {e}")
            return []
    
    def _extract_input_params(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user input parameters"""
        param_fields = [
            'pH', 'temperature_c', 'concentration_mg_ml', 'ionic_strength_mM',
            'additive', 'time_min', 'shear_rate_s1', 'pressure_bar'
        ]
        
        params = {}
        for field in param_fields:
            if field in user_input:
                params[field] = user_input[field]
        
        return params
    
    def _save_experiment_record(
        self,
        user_id: int,
        user_input: Dict[str, Any],
        result: Dict[str, Any],
        prediction_type: str
    ):
        """Save experiment record to database"""
        try:
            record_data = {
                'user_id': user_id,
                'biomolecule_type': user_input.get('biomolecule_type'),
                'biomolecule_name': user_input.get('biomolecule_name'),
                'experiment_type': user_input.get('experiment_type', 'stability'),
                'input_pH': user_input.get('pH'),
                'input_temperature_c': user_input.get('temperature_c'),
                'input_concentration_mg_ml': user_input.get('concentration_mg_ml'),
                'input_ionic_strength_mM': user_input.get('ionic_strength_mM'),
                'input_additive': user_input.get('additive'),
                'input_time_min': user_input.get('time_min'),
                'input_shear_rate_s1': user_input.get('shear_rate_s1'),
                'input_pressure_bar': user_input.get('pressure_bar'),
                'prediction_type': prediction_type,
                'prediction_result': result,
                'confidence': result.get('confidence'),
                'recommended_literature': result.get('similar_literature', [])
            }
            
            user_experiment_repo.create_experiment_record(self.db, record_data)
        except Exception as e:
            print(f"Warning: Failed to save experiment record: {e}")

