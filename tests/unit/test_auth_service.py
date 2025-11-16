"""
Unit tests for authentication service
"""
import pytest
from unittest.mock import patch, MagicMock

from backend.app.services.auth_service import login
from backend.app.models.user import AppUser


class TestAuthService:
    """Test authentication service functions"""
    
    @patch('backend.app.services.auth_service.create_access_token')
    @patch('backend.app.services.auth_service.verify_password')
    @patch('backend.app.services.auth_service.add_login_audit')
    @patch('backend.app.services.auth_service.get_by_username')
    def test_login_success(
        self,
        mock_get_user,
        mock_add_audit,
        mock_verify_password,
        mock_create_token,
        db_session
    ):
        """Test successful login"""
        # Arrange
        mock_user = MagicMock(spec=AppUser)
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.password_hash = "hashed_password"
        
        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = True
        mock_create_token.return_value = "test_token_123"
        
        # Act
        result = login(
            db_session,
            username="testuser",
            password="testpassword123",
            ip="127.0.0.1"
        )
        
        # Assert
        assert result == "test_token_123"
        mock_get_user.assert_called_once_with(db_session, "testuser")
        mock_verify_password.assert_called_once_with("testpassword123", "hashed_password")
        mock_add_audit.assert_called_once()
        assert mock_user.last_login_at is not None
    
    @patch('backend.app.services.auth_service.create_access_token')
    @patch('backend.app.services.auth_service.verify_password')
    @patch('backend.app.services.auth_service.add_login_audit')
    @patch('backend.app.services.auth_service.get_by_username')
    def test_login_invalid_password(
        self,
        mock_get_user,
        mock_add_audit,
        mock_verify_password,
        mock_create_token,
        db_session
    ):
        """Test login with invalid password"""
        # Arrange
        mock_user = MagicMock(spec=AppUser)
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.password_hash = "hashed_password"
        
        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = False
        
        # Act
        result = login(
            db_session,
            username="testuser",
            password="wrongpassword",
            ip="127.0.0.1"
        )
        
        # Assert
        assert result is None
        mock_get_user.assert_called_once_with(db_session, "testuser")
        mock_verify_password.assert_called_once()
        mock_add_audit.assert_called_once()
        mock_create_token.assert_not_called()
    
    @patch('backend.app.services.auth_service.create_access_token')
    @patch('backend.app.services.auth_service.verify_password')
    @patch('backend.app.services.auth_service.add_login_audit')
    @patch('backend.app.services.auth_service.get_by_username')
    def test_login_user_not_found(
        self,
        mock_get_user,
        mock_add_audit,
        mock_verify_password,
        mock_create_token,
        db_session
    ):
        """Test login with non-existent user"""
        # Arrange
        mock_get_user.return_value = None
        
        # Act
        result = login(
            db_session,
            username="nonexistent",
            password="password123",
            ip="127.0.0.1"
        )
        
        # Assert
        assert result is None
        mock_get_user.assert_called_once_with(db_session, "nonexistent")
        mock_verify_password.assert_not_called()
        mock_add_audit.assert_called_once()
        mock_create_token.assert_not_called()
    
    @patch('backend.app.services.auth_service.create_access_token')
    @patch('backend.app.services.auth_service.verify_password')
    @patch('backend.app.services.auth_service.add_login_audit')
    @patch('backend.app.services.auth_service.get_by_username')
    def test_login_inactive_user(
        self,
        mock_get_user,
        mock_add_audit,
        mock_verify_password,
        mock_create_token,
        db_session
    ):
        """Test login with inactive user"""
        # Arrange
        mock_user = MagicMock(spec=AppUser)
        mock_user.id = 1
        mock_user.is_active = False
        mock_user.password_hash = "hashed_password"
        
        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = True
        
        # Act
        result = login(
            db_session,
            username="inactive_user",
            password="password123",
            ip="127.0.0.1"
        )
        
        # Assert
        assert result is None
        mock_get_user.assert_called_once_with(db_session, "inactive_user")
        mock_verify_password.assert_called_once()
        mock_add_audit.assert_called_once()
        mock_create_token.assert_not_called()
    
    @patch('backend.app.services.auth_service.create_access_token')
    @patch('backend.app.services.auth_service.verify_password')
    @patch('backend.app.services.auth_service.add_login_audit')
    @patch('backend.app.services.auth_service.get_by_username')
    def test_login_audit_logs_failure(
        self,
        mock_get_user,
        mock_add_audit,
        mock_verify_password,
        mock_create_token,
        db_session
    ):
        """Test that failed login attempts are logged"""
        # Arrange
        mock_get_user.return_value = None
        
        # Act
        login(
            db_session,
            username="nonexistent",
            password="password123",
            ip="127.0.0.1"
        )
        
        # Assert
        mock_add_audit.assert_called_once()
        call_args = mock_add_audit.call_args
        assert call_args[1]['username'] == "nonexistent"
        assert call_args[1]['ip'] == "127.0.0.1"
        assert call_args[1]['ok'] is False
        assert call_args[1]['user_id'] is None
    
    @patch('backend.app.services.auth_service.create_access_token')
    @patch('backend.app.services.auth_service.verify_password')
    @patch('backend.app.services.auth_service.add_login_audit')
    @patch('backend.app.services.auth_service.get_by_username')
    def test_login_audit_logs_success(
        self,
        mock_get_user,
        mock_add_audit,
        mock_verify_password,
        mock_create_token,
        db_session
    ):
        """Test that successful login attempts are logged"""
        # Arrange
        mock_user = MagicMock(spec=AppUser)
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.password_hash = "hashed_password"
        
        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = True
        mock_create_token.return_value = "token"
        
        # Act
        login(
            db_session,
            username="testuser",
            password="password123",
            ip="192.168.1.1"
        )
        
        # Assert
        mock_add_audit.assert_called_once()
        call_args = mock_add_audit.call_args
        assert call_args[1]['user_id'] == 1
        assert call_args[1]['username'] == "testuser"
        assert call_args[1]['ip'] == "192.168.1.1"
        assert call_args[1]['ok'] is True

