"""
Integration tests for literature API endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
class TestLiteratureRouter:
    """Test literature API endpoints"""
    
    def test_search_similar_literature_success(self, client, sample_extraction_record):
        """Test searching similar literature"""
        response = client.get(
            "/literature/search",
            params={
                "biomolecule_name": "lysozyme",
                "property_type": "stability",
                "pH": 7.0,
                "temperature_c": 25.0,
                "limit": 3
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "similarity_score" in data[0]
            assert "protein_name" in data[0] or "biomolecule_type" in data[0]
    
    def test_search_similar_literature_no_params(self, client):
        """Test searching literature with no parameters"""
        response = client.get(
            "/literature/search",
            params={
                "biomolecule_name": "lysozyme",
                "property_type": "stability"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_similar_literature_not_found(self, client):
        """Test searching literature with no matches"""
        response = client.get(
            "/literature/search",
            params={
                "biomolecule_name": "nonexistent_protein",
                "property_type": "stability",
                "limit": 3
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # May be empty or have low similarity results
    
    def test_get_top_confidence_records(self, client, sample_extraction_record):
        """Test getting top confidence records"""
        response = client.get(
            "/literature/top-confidence",
            params={
                "biomolecule_name": "lysozyme",
                "property_type": "stability",
                "limit": 3
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 1:
            # Should be sorted by confidence
            assert data[0]["confidence"] >= data[1]["confidence"]

