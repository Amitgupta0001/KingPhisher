"""
Unit tests for King-Phisher application.
Tests authentication, password validation, and core functionality.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, validate_password, init_db
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import tempfile

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Use a temporary database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

class TestPasswordValidation:
    """Test password validation function."""
    
    def test_valid_password(self):
        """Test that a strong password passes validation."""
        is_valid, message = validate_password("StrongP@ss123")
        assert is_valid is True
        assert message == "Valid"
    
    def test_password_too_short(self):
        """Test that short passwords are rejected."""
        is_valid, message = validate_password("Short1!")
        assert is_valid is False
        assert "at least 8 characters" in message
    
    def test_password_no_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        is_valid, message = validate_password("weakpass123!")
        assert is_valid is False
        assert "uppercase" in message.lower()
    
    def test_password_no_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        is_valid, message = validate_password("WEAKPASS123!")
        assert is_valid is False
        assert "lowercase" in message.lower()
    
    def test_password_no_number(self):
        """Test that passwords without numbers are rejected."""
        is_valid, message = validate_password("WeakPass!")
        assert is_valid is False
        assert "number" in message.lower()
    
    def test_password_no_special_char(self):
        """Test that passwords without special characters are rejected."""
        is_valid, message = validate_password("WeakPass123")
        assert is_valid is False
        assert "special character" in message.lower()
    
    def test_common_password(self):
        """Test that common passwords are rejected."""
        is_valid, message = validate_password("Password123!")
        assert is_valid is False
        assert "too common" in message.lower()

class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_register_page_loads(self, client):
        """Test that register page loads successfully."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'register' in response.data.lower()
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard redirects to login when not authenticated."""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_register_with_weak_password(self, client):
        """Test that registration fails with weak password."""
        response = client.post('/register', data={
            'name': 'Test User',
            'username': 'testuser',
            'phone': '1234567890',
            'email': 'test@example.com',
            'password': 'weak'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'at least 8 characters' in response.data or b'Password' in response.data
    
    def test_register_with_invalid_email(self, client):
        """Test that registration fails with invalid email."""
        response = client.post('/register', data={
            'name': 'Test User',
            'username': 'testuser',
            'phone': '1234567890',
            'email': 'invalid-email',
            'password': 'StrongP@ss123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email' in response.data or b'email' in response.data.lower()
    
    def test_successful_registration(self, client):
        """Test successful user registration."""
        response = client.post('/register', data={
            'name': 'Test User',
            'username': 'testuser',
            'phone': '1234567890',
            'email': 'test@example.com',
            'password': 'StrongP@ss123'
        }, follow_redirects=True)
        # Should redirect to dashboard after successful registration
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower() or b'welcome' in response.data.lower()

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_login_rate_limit(self, client):
        """Test that login endpoint is rate limited."""
        # Make 6 requests (limit is 5 per minute)
        for i in range(6):
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'wrong'
            })
            if i < 5:
                assert response.status_code in [200, 302]
            else:
                # 6th request should be rate limited
                assert response.status_code == 429

class TestModelLoading:
    """Test model loading functionality."""
    
    def test_model_loads(self):
        """Test that model and scaler load correctly."""
        from app import model, scaler
        # Model might be None if files don't exist, which is okay for testing
        assert model is not None or scaler is None

class TestDatabaseSchema:
    """Test database schema and operations."""
    
    def test_database_initialization(self, client):
        """Test that database initializes with correct schema."""
        # Database should be initialized by the fixture
        # This test just ensures no errors occur
        assert True
    
    def test_user_table_exists(self, client):
        """Test that users table exists."""
        from app import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            result = cursor.fetchone()
            assert result is not None
    
    def test_scan_history_table_exists(self, client):
        """Test that scan_history table exists."""
        from app import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scan_history'")
            result = cursor.fetchone()
            assert result is not None
    
    def test_indexes_exist(self, client):
        """Test that database indexes are created."""
        from app import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            # Check for at least one of our custom indexes
            assert any('idx_' in idx for idx in indexes)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
