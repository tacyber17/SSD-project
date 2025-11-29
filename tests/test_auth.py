"""
Tests for authentication routes.
"""
import pytest
from flask import url_for
from app.models import User


def test_register(client):
    """Test user registration."""
    response = client.post(url_for('auth.register'), data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'first_name': 'New',
        'last_name': 'User',
        'password': 'password123',
        'password2': 'password123',
        'phone': '1234567890'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Registration successful' in response.data
    
    # Check user was created
    user = User.query.filter_by(email='newuser@example.com').first()
    assert user is not None
    assert user.username == 'newuser'


def test_login(client, user):
    """Test user login."""
    response = client.post(url_for('auth.login'), data={
        'email': 'test@example.com',
        'password': 'testpass123',
        'remember_me': False
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(url_for('auth.login'), data={
        'email': 'wrong@example.com',
        'password': 'wrongpass',
        'remember_me': False
    })
    
    assert b'Invalid email or password' in response.data


def test_logout(client, user):
    """Test user logout."""
    # Login first
    client.post(url_for('auth.login'), data={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Logout
    response = client.get(url_for('auth.logout'), follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out' in response.data.lower()


def test_profile_requires_login(client):
    """Test that profile page requires login."""
    response = client.get(url_for('auth.profile'), follow_redirects=True)
    assert b'log in' in response.data.lower()


