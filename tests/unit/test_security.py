"""
Unit tests for security functions (password hashing, JWT tokens)
"""
import pytest
from datetime import datetime, timedelta, timezone
import jwt
from unittest.mock import patch, MagicMock

from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)
from backend.app.core.config import settings


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string"""
        result = hash_password("testpassword123")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_hash_password_different_for_same_input(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Hashes should be different due to random salt
        assert hash1 != hash2
    
    def test_verify_password_correct_password(self):
        """Test that verify_password returns True for correct password"""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect_password(self):
        """Test that verify_password returns False for incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty_string(self):
        """Test password verification with empty string"""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False
    
    def test_hash_password_special_characters(self):
        """Test password hashing with special characters"""
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("different", hashed) is False
    
    def test_hash_password_unicode(self):
        """Test password hashing with unicode characters"""
        password = "密码123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestJWTToken:
    """Test JWT token creation and verification"""
    
    @patch('backend.app.core.security.settings')
    def test_create_access_token_returns_string(self, mock_settings):
        """Test that create_access_token returns a string"""
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_expire_minutes = None
        
        token = create_access_token("user123")
        assert isinstance(token, str)
        assert len(token) > 0
    
    @patch('backend.app.core.security.settings')
    def test_create_access_token_with_expiration(self, mock_settings):
        """Test token creation with expiration"""
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_expire_minutes = 30
        
        token = create_access_token("user123")
        
        # Decode and verify
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])
        assert payload["sub"] == "user123"
        assert "exp" in payload
    
    @patch('backend.app.core.security.settings')
    def test_create_access_token_without_expiration(self, mock_settings):
        """Test token creation without expiration (permanent token)"""
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_expire_minutes = None
        
        token = create_access_token("user123")
        
        # Decode and verify
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"], options={"verify_exp": False})
        assert payload["sub"] == "user123"
        # exp should not be present
        assert "exp" not in payload
    
    @patch('backend.app.core.security.settings')
    def test_verify_token_valid_token(self, mock_settings):
        """Test verification of valid token"""
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_expire_minutes = None
        
        token = create_access_token("user123")
        payload = verify_token(token)
        
        assert payload["sub"] == "user123"
    
    @patch('backend.app.core.security.settings')
    def test_verify_token_invalid_secret(self, mock_settings):
        """Test verification fails with wrong secret"""
        mock_settings.jwt_secret = "test_secret"
        mock_settings.jwt_expire_minutes = None
        
        token = create_access_token("user123")
        
        # Change secret
        mock_settings.jwt_secret = "wrong_secret"
        
        with pytest.raises(Exception) as exc_info:
            verify_token(token)
        assert "Invalid token" in str(exc_info.value)
    
    @patch('backend.app.core.security.settings')
    def test_verify_token_expired_token(self, mock_settings):
        """Test verification fails with expired token"""
        mock_settings.jwt_secret = "test_secret"
        
        # Create expired token manually
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {"sub": "user123", "exp": expire}
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        
        mock_settings.jwt_secret = "test_secret"
        
        with pytest.raises(Exception) as exc_info:
            verify_token(token)
        assert "expired" in str(exc_info.value).lower()
    
    @patch('backend.app.core.security.settings')
    def test_verify_token_malformed_token(self, mock_settings):
        """Test verification fails with malformed token"""
        mock_settings.jwt_secret = "test_secret"
        
        with pytest.raises(Exception) as exc_info:
            verify_token("not.a.valid.token")
        assert "Invalid token" in str(exc_info.value)
    
    @patch('backend.app.core.security.settings')
    def test_verify_token_empty_string(self, mock_settings):
        """Test verification fails with empty string"""
        mock_settings.jwt_secret = "test_secret"
        
        with pytest.raises(Exception):
            verify_token("")

