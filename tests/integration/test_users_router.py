"""
Integration tests for user management API endpoints
"""
import pytest
from fastapi import status


@pytest.mark.integration
class TestUsersRouter:
    """Test user management API endpoints"""
    
    def test_create_user_success(self, client):
        """Test successful user creation"""
        response = client.post(
            "/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data  # Password should not be in response
        assert "password_hash" not in data
    
    def test_create_user_duplicate_username(self, client, sample_user_data):
        """Test creating user with duplicate username"""
        # Create first user
        client.post(
            "/users",
            json={
                "username": sample_user_data["username"],
                "email": "first@example.com",
                "password": "password123"
            }
        )
        
        # Try to create second user with same username
        response = client.post(
            "/users",
            json={
                "username": sample_user_data["username"],
                "email": "second@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()
    
    def test_create_user_missing_fields(self, client):
        """Test creating user with missing required fields"""
        # Missing email
        response = client.post(
            "/users",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_current_user_success(self, authenticated_client, sample_user):
        """Test getting current user information"""
        response = authenticated_client.get("/users/me")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == sample_user.username
        assert data["email"] == sample_user.email
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        client.headers.update({"Authorization": "Bearer invalid_token"})
        response = client.get("/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_by_id_success(self, client, sample_user):
        """Test getting user by ID"""
        response = client.get(f"/users/{sample_user.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["username"] == sample_user.username
    
    def test_get_user_by_id_not_found(self, client):
        """Test getting non-existent user"""
        response = client.get("/users/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_user_success(self, client, sample_user):
        """Test updating user information"""
        response = client.put(
            f"/users/{sample_user.id}",
            json={
                "email": "updated@example.com"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "updated@example.com"
        assert data["username"] == sample_user.username  # Unchanged
    
    def test_update_user_not_found(self, client):
        """Test updating non-existent user"""
        response = client.put(
            "/users/99999",
            json={
                "email": "updated@example.com"
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_user_duplicate_username(self, client, sample_user, sample_user_data):
        """Test updating user with duplicate username"""
        # Create another user
        response = client.post(
            "/users",
            json={
                "username": "otheruser",
                "email": "other@example.com",
                "password": "password123"
            }
        )
        other_user_id = response.json()["id"]
        
        # Try to update other user with sample_user's username
        response = client.put(
            f"/users/{other_user_id}",
            json={
                "username": sample_user_data["username"]
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_delete_user_success(self, client, sample_user):
        """Test deleting user"""
        response = client.delete(f"/users/{sample_user.id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify user is deleted
        get_response = client.get(f"/users/{sample_user.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_user_not_found(self, client):
        """Test deleting non-existent user"""
        response = client.delete("/users/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

