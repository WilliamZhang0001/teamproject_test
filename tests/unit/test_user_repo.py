"""
Unit tests for user repository
"""
import pytest
from backend.app.repos.user_repo import get_by_username
from backend.app.models.user import AppUser


class TestUserRepo:
    """Test user repository functions"""
    
    def test_get_by_username_found(self, db_session, sample_user):
        """Test getting user by username when user exists"""
        result = get_by_username(db_session, sample_user.username)
        
        assert result is not None
        assert result.id == sample_user.id
        assert result.username == sample_user.username
        assert result.email == sample_user.email
    
    def test_get_by_username_not_found(self, db_session):
        """Test getting user by username when user doesn't exist"""
        result = get_by_username(db_session, "nonexistent_user")
        
        assert result is None
    
    def test_get_by_username_case_sensitive(self, db_session, sample_user):
        """Test that username lookup is case-sensitive"""
        result = get_by_username(db_session, sample_user.username.upper())
        
        # Should not find user with different case
        assert result is None
    
    def test_get_by_username_empty_string(self, db_session):
        """Test getting user with empty username"""
        result = get_by_username(db_session, "")
        
        assert result is None

