"""
Unit tests for literature repository
"""
import pytest
from backend.app.repos import literature_repo
from backend.app.models.literature import Literature, ExtractionRecord


class TestLiteratureRepo:
    """Test literature repository functions"""
    
    def test_create_literature(self, db_session):
        """Test creating literature record"""
        literature = literature_repo.create_literature(
            db_session,
            doi="10.1000/test",
            title="Test Title",
            authors="Author 1",
            pub_year=2023,
            source="test"
        )
        
        assert literature.id is not None
        assert literature.doi == "10.1000/test"
        assert literature.title == "Test Title"
        assert literature.authors == "Author 1"
        assert literature.pub_year == 2023
    
    def test_get_literature_by_doi_found(self, db_session, sample_literature):
        """Test getting literature by DOI when it exists"""
        result = literature_repo.get_literature_by_doi(
            db_session,
            sample_literature.doi
        )
        
        assert result is not None
        assert result.id == sample_literature.id
        assert result.doi == sample_literature.doi
    
    def test_get_literature_by_doi_not_found(self, db_session):
        """Test getting literature by DOI when it doesn't exist"""
        result = literature_repo.get_literature_by_doi(
            db_session,
            "10.1000/nonexistent"
        )
        
        assert result is None
    
    def test_create_extraction_record(self, db_session, sample_literature):
        """Test creating extraction record"""
        record_data = {
            'biomolecule_type': 'protein',
            'protein_name': 'lysozyme',
            'property': 'stability',
            'parameters': {
                'pH': 7.0,
                'temperature_c': 25.0,
                'concentration_mg_ml': 10.0
            },
            'outcome_score': 0.85,
            'confidence': 0.9
        }
        
        record = literature_repo.create_extraction_record(
            db_session,
            record_data,
            sample_literature.id
        )
        
        assert record.id is not None
        assert record.literature_id == sample_literature.id
        assert record.protein_name == 'lysozyme'
        assert record.pH == 7.0
        assert record.temperature_c == 25.0
        assert record.confidence == 0.9
    
    def test_search_similar_records_no_params(self, db_session, sample_extraction_record):
        """Test similarity search with no parameters"""
        target_params = {}
        
        results = literature_repo.search_similar_records(
            db_session,
            target_params=target_params,
            biomolecule_name="lysozyme",
            property_type="stability",
            limit=3
        )
        
        # Should return records but with low similarity
        assert isinstance(results, list)
    
    def test_search_similar_records_exact_match(self, db_session, sample_extraction_record):
        """Test similarity search with exact parameter match"""
        target_params = {
            'pH': 7.0,
            'temperature_c': 25.0,
            'concentration_mg_ml': 10.0
        }
        
        results = literature_repo.search_similar_records(
            db_session,
            target_params=target_params,
            biomolecule_name="lysozyme",
            property_type="stability",
            limit=3
        )
        
        assert len(results) > 0
        assert results[0]['similarity_score'] > 0.5
    
    def test_search_similar_records_partial_match(self, db_session, sample_extraction_record):
        """Test similarity search with partial parameter match"""
        target_params = {
            'pH': 7.0,
            'temperature_c': 25.0
            # Missing concentration_mg_ml
        }
        
        results = literature_repo.search_similar_records(
            db_session,
            target_params=target_params,
            biomolecule_name="lysozyme",
            property_type="stability",
            limit=3
        )
        
        assert len(results) > 0
        # Should have similarity but lower than exact match
        assert results[0]['similarity_score'] > 0
    
    def test_calculate_similarity_exact_match(self, db_session, sample_extraction_record):
        """Test similarity calculation with exact match"""
        target_params = {
            'pH': 7.0,
            'temperature_c': 25.0,
            'concentration_mg_ml': 10.0
        }
        
        similarity = literature_repo.calculate_similarity(
            target_params,
            sample_extraction_record
        )
        
        assert similarity > 0.7  # High similarity for exact match
    
    def test_calculate_similarity_no_match(self, db_session, sample_extraction_record):
        """Test similarity calculation with completely different parameters"""
        target_params = {
            'pH': 2.0,  # Very different
            'temperature_c': 100.0,  # Very different
            'concentration_mg_ml': 1000.0  # Very different
        }
        
        similarity = literature_repo.calculate_similarity(
            target_params,
            sample_extraction_record
        )
        
        assert similarity < 0.5  # Low similarity
    
    def test_calculate_similarity_missing_params(self, db_session, sample_extraction_record):
        """Test similarity calculation when record has missing parameters"""
        target_params = {
            'pH': 7.0,
            'temperature_c': 25.0,
            'concentration_mg_ml': 10.0,
            'ionic_strength_mM': 200.0  # Not in record
        }
        
        similarity = literature_repo.calculate_similarity(
            target_params,
            sample_extraction_record
        )
        
        # Should still calculate similarity but with penalty
        assert similarity >= 0
    
    def test_get_most_common_additives(self, db_session, sample_extraction_record):
        """Test getting most common additives"""
        result = literature_repo.get_most_common_additives(
            db_session,
            biomolecule_name="lysozyme",
            property_type="stability",
            limit=5
        )
        
        if result:
            assert 'recommended_value' in result
            assert 'common_values' in result
            assert 'count' in result
    
    def test_get_top_records_by_confidence(self, db_session, sample_extraction_record):
        """Test getting top records by confidence"""
        results = literature_repo.get_top_records_by_confidence(
            db_session,
            biomolecule_name="lysozyme",
            property_type="stability",
            limit=3
        )
        
        assert isinstance(results, list)
        if len(results) > 1:
            # Should be sorted by confidence (descending)
            assert results[0]['confidence'] >= results[1]['confidence']

