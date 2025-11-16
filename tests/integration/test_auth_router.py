"""
Integration tests for authentication API endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
class TestAuthRouter:
    """Test authentication API endpoints"""
    
    def test_login_success(self, client, sample_user_data, sample_user):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            json={
                "username": sample_user_data["username"],
                "password": sample_user_data["password"]
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == sample_user_data["username"]
    
    def test_login_invalid_password(self, client, sample_user_data, sample_user):
        """Test login with invalid password"""
        response = client.post(
            "/auth/login",
            json={
                "username": sample_user_data["username"],
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_user_not_found(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self, client, inactive_user, sample_user_data):
        """Test login with inactive user"""
        response = client.post(
            "/auth/login",
            json={
                "username": inactive_user.username,
                "password": sample_user_data["password"]
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_missing_fields(self, client):
        """Test login with missing required fields"""
        # Missing password
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_empty_username(self, client):
        """Test login with empty username"""
        response = client.post(
            "/auth/login",
            json={
                "username": "",
                "password": "password123"
            }
        )
        
        # Should fail validation or return 401
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_login_empty_password(self, client, sample_user_data):
        """Test login with empty password"""
        response = client.post(
            "/auth/login",
            json={
                "username": sample_user_data["username"],
                "password": ""
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

