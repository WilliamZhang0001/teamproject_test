"""
Unit tests for user experiment repository
"""
import pytest
import json
from backend.app.repos import user_experiment_repo
from backend.app.models.user_experiment import UserExperimentRecord


class TestUserExperimentRepo:
    """Test user experiment repository functions"""
    
    def test_create_experiment_record(self, db_session, sample_user):
        """Test creating experiment record"""
        record_data = {
            'user_id': sample_user.id,
            'biomolecule_type': 'protein',
            'biomolecule_name': 'lysozyme',
            'experiment_type': 'stability',
            'input_pH': 7.0,
            'input_temperature_c': 25.0,
            'prediction_type': 'classification',
            'prediction_result': {'prediction': 'Good', 'confidence': 0.85},
            'confidence': 0.85
        }
        
        record = user_experiment_repo.create_experiment_record(
            db_session,
            record_data
        )
        
        assert record.id is not None
        assert record.user_id == sample_user.id
        assert record.biomolecule_name == 'lysozyme'
        assert record.prediction_type == 'classification'
        assert record.confidence == 0.85
        
        # Check JSON fields are stored correctly
        result_dict = json.loads(record.prediction_result)
        assert result_dict['prediction'] == 'Good'
    
    def test_get_user_experiments(self, db_session, sample_user, sample_experiment_record):
        """Test getting user's experiment records"""
        results = user_experiment_repo.get_user_experiments(
            db_session,
            user_id=sample_user.id,
            limit=10
        )
        
        assert len(results) > 0
        assert all(r.user_id == sample_user.id for r in results)
    
    def test_get_user_experiments_empty(self, db_session, sample_user):
        """Test getting experiments for user with no records"""
        results = user_experiment_repo.get_user_experiments(
            db_session,
            user_id=sample_user.id,
            limit=10
        )
        
        assert len(results) == 0
    
    def test_get_user_experiments_limit(self, db_session, sample_user):
        """Test that limit parameter works correctly"""
        # Create multiple records
        for i in range(5):
            record_data = {
                'user_id': sample_user.id,
                'biomolecule_type': 'protein',
                'biomolecule_name': f'protein_{i}',
                'experiment_type': 'stability',
                'prediction_type': 'classification',
                'confidence': 0.8
            }
            user_experiment_repo.create_experiment_record(db_session, record_data)
        
        results = user_experiment_repo.get_user_experiments(
            db_session,
            user_id=sample_user.id,
            limit=3
        )
        
        assert len(results) <= 3
    
    def test_get_experiment_by_id_found(self, db_session, sample_experiment_record):
        """Test getting experiment by ID when it exists"""
        result = user_experiment_repo.get_experiment_by_id(
            db_session,
            sample_experiment_record.id
        )
        
        assert result is not None
        assert result.id == sample_experiment_record.id
    
    def test_get_experiment_by_id_not_found(self, db_session):
        """Test getting experiment by ID when it doesn't exist"""
        result = user_experiment_repo.get_experiment_by_id(
            db_session,
            99999
        )
        
        assert result is None
    
    def test_delete_user_experiments(self, db_session, sample_user):
        """Test deleting all experiments for a user"""
        # Create some records
        for i in range(3):
            record_data = {
                'user_id': sample_user.id,
                'biomolecule_type': 'protein',
                'biomolecule_name': f'protein_{i}',
                'experiment_type': 'stability',
                'prediction_type': 'classification'
            }
            user_experiment_repo.create_experiment_record(db_session, record_data)
        
        # Delete all
        count = user_experiment_repo.delete_user_experiments(
            db_session,
            sample_user.id
        )
        
        assert count == 3
        
        # Verify deleted
        results = user_experiment_repo.get_user_experiments(
            db_session,
            user_id=sample_user.id
        )
        assert len(results) == 0

