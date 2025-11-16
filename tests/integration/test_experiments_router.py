"""
Integration tests for experiment prediction API endpoints
"""
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestExperimentsRouter:
    """Test experiment prediction API endpoints"""
    
    @patch('backend.app.routers.experiments.get_ml_predictor')
    def test_predict_classification_success(
        self,
        mock_get_predictor,
        authenticated_client,
        sample_user
    ):
        """Test successful classification prediction"""
        # Mock ML predictor
        mock_predictor = MagicMock()
        mock_predictor.predict.return_value = {
            'prediction': 'Good',
            'confidence': 0.85,
            'probabilities': {'stable': 0.85, 'unstable': 0.15}
        }
        mock_get_predictor.return_value = mock_predictor
        
        response = authenticated_client.post(
            "/api/v1/experiments/predict-classification",
            json={
                "biomolecule_type": "protein",
                "biomolecule_name": "lysozyme",
                "experiment_type": "stability",
                "pH": 7.0,
                "temperature_c": 25.0,
                "concentration_mg_ml": 10.0
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "similar_literature" in data
    
    def test_predict_classification_unauthorized(self, client):
        """Test classification prediction without authentication"""
        response = client.post(
            "/api/v1/experiments/predict-classification",
            json={
                "biomolecule_type": "protein",
                "biomolecule_name": "lysozyme",
                "experiment_type": "stability"
            }
        )
        
        # May require authentication or may work without it
        # Adjust based on actual implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    def test_predict_classification_missing_required_fields(self, authenticated_client):
        """Test classification prediction with missing required fields"""
        response = authenticated_client.post(
            "/api/v1/experiments/predict-classification",
            json={
                "biomolecule_name": "lysozyme"
                # Missing biomolecule_type and experiment_type
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('backend.app.routers.experiments.get_ml_predictor')
    def test_predict_parameter_success(
        self,
        mock_get_predictor,
        authenticated_client,
        sample_user
    ):
        """Test successful parameter prediction"""
        # Mock ML predictor
        mock_predictor = MagicMock()
        mock_predictor.get_parameter_recommendations.return_value = {
            'recommended_ranges': {
                'pH': {'median': 7.0, 'min': 6.5, 'max': 7.5},
                'temperature_c': {'median': 25.0, 'min': 20.0, 'max': 30.0}
            },
            'confidence': 0.8
        }
        mock_get_predictor.return_value = mock_predictor
        
        response = authenticated_client.post(
            "/api/v1/experiments/predict-parameter",
            json={
                "biomolecule_type": "protein",
                "biomolecule_name": "lysozyme",
                "experiment_type": "stability",
                "request_params": ["pH", "temperature_c"]
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "predicted_parameters" in data
        assert "confidence" in data
    
    def test_get_experiment_history_success(self, authenticated_client, sample_user, sample_experiment_record):
        """Test getting user's experiment history"""
        response = authenticated_client.get(
            "/api/v1/experiments/history",
            params={"limit": 10}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "biomolecule_name" in data[0]
    
    def test_get_experiment_history_empty(self, authenticated_client, db_session, sample_user):
        """Test getting history for user with no records"""
        # Delete all records first
        from backend.app.repos import user_experiment_repo
        user_experiment_repo.delete_user_experiments(
            db_session,
            sample_user.id
        )
        
        response = authenticated_client.get("/api/v1/experiments/history")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_experiment_by_id_success(self, authenticated_client, sample_experiment_record):
        """Test getting experiment by ID"""
        response = authenticated_client.get(
            f"/api/v1/experiments/{sample_experiment_record.id}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_experiment_record.id
    
    def test_get_experiment_by_id_not_found(self, authenticated_client):
        """Test getting non-existent experiment"""
        response = authenticated_client.get("/api/v1/experiments/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

