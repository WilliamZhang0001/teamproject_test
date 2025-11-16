"""
Unit tests for experiment service
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.experiment_service import ExperimentService


class TestExperimentService:
    """Test experiment service functions"""
    
    @patch('backend.app.services.experiment_service.literature_repo')
    def test_predict_classification_success(
        self,
        mock_literature_repo,
        db_session
    ):
        """Test successful classification prediction"""
        # Mock ML predictor
        mock_predictor = MagicMock()
        mock_predictor.predict.return_value = {
            'prediction': 'Good',
            'confidence': 0.85
        }
        
        # Mock literature search
        mock_literature_repo.search_similar_records.return_value = [
            {'similarity_score': 0.8, 'title': 'Test Paper'}
        ]
        
        service = ExperimentService(db_session, mock_predictor)
        
        user_input = {
            'biomolecule_type': 'protein',
            'biomolecule_name': 'lysozyme',
            'experiment_type': 'stability',
            'pH': 7.0,
            'temperature_c': 25.0
        }
        
        result = service.predict_classification(user_input, user_id=1, top_k=3)
        
        assert result['prediction'] in ['Good', 'Bad']
        assert 'confidence' in result
        assert 'similar_literature' in result
        assert len(result['similar_literature']) > 0
    
    @patch('backend.app.services.experiment_service.user_experiment_repo')
    @patch('backend.app.services.experiment_service.literature_repo')
    def test_predict_classification_saves_record(
        self,
        mock_literature_repo,
        mock_experiment_repo,
        db_session
    ):
        """Test that classification prediction saves record"""
        mock_predictor = MagicMock()
        mock_predictor.predict.return_value = {
            'prediction': 'Good',
            'confidence': 0.85
        }
        mock_literature_repo.search_similar_records.return_value = []
        
        mock_record = MagicMock()
        mock_record.id = 1
        mock_experiment_repo.create_experiment_record.return_value = mock_record
        
        service = ExperimentService(db_session, mock_predictor)
        
        user_input = {
            'biomolecule_type': 'protein',
            'biomolecule_name': 'lysozyme',
            'experiment_type': 'stability',
            'pH': 7.0
        }
        
        result = service.predict_classification(user_input, user_id=1)
        
        # Verify record was saved
        mock_experiment_repo.create_experiment_record.assert_called_once()
    
    @patch('backend.app.services.experiment_service.literature_repo')
    def test_predict_parameter_success(
        self,
        mock_literature_repo,
        db_session
    ):
        """Test successful parameter prediction"""
        mock_predictor = MagicMock()
        mock_predictor.get_parameter_recommendations.return_value = {
            'recommended_ranges': {
                'pH': {'median': 7.0, 'min': 6.5, 'max': 7.5}
            },
            'confidence': 0.8
        }
        
        mock_literature_repo.search_similar_records.return_value = []
        mock_literature_repo.get_most_common_additives.return_value = None
        
        service = ExperimentService(db_session, mock_predictor)
        
        user_input = {
            'biomolecule_type': 'protein',
            'biomolecule_name': 'lysozyme',
            'experiment_type': 'stability',
            'temperature_c': 25.0
        }
        
        result = service.predict_parameter(
            user_input,
            request_params=['pH'],
            user_id=1
        )
        
        assert 'predicted_parameters' in result
        assert 'confidence' in result
    
    @patch('backend.app.services.experiment_service.literature_repo')
    def test_predict_parameter_with_provided_params(
        self,
        mock_literature_repo,
        db_session
    ):
        """Test parameter prediction when some params are already provided"""
        mock_predictor = MagicMock()
        mock_predictor.get_parameter_recommendations.return_value = {
            'recommended_ranges': {
                'pH': {'median': 7.0}
            },
            'confidence': 0.8
        }
        
        mock_literature_repo.search_similar_records.return_value = []
        
        service = ExperimentService(db_session, mock_predictor)
        
        user_input = {
            'biomolecule_type': 'protein',
            'biomolecule_name': 'lysozyme',
            'experiment_type': 'stability',
            'temperature_c': 25.0  # Already provided
        }
        
        result = service.predict_parameter(
            user_input,
            request_params=['pH', 'temperature_c'],  # Request both
            user_id=1
        )
        
        assert 'predicted_parameters' in result
        # Should have _provided_params entry
        assert '_provided_params' in result['predicted_parameters'] or 'pH' in result['predicted_parameters']
    
    def test_predict_classification_no_predictor(self, db_session):
        """Test classification prediction without ML predictor"""
        service = ExperimentService(db_session, None)
        
        user_input = {
            'biomolecule_type': 'protein',
            'biomolecule_name': 'lysozyme',
            'experiment_type': 'stability'
        }
        
        result = service.predict_classification(user_input)
        
        # Should return default result
        assert 'prediction' in result
        assert 'confidence' in result

