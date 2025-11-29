"""
Tests for REST API endpoints.
"""
import pytest
import json
from flask import url_for


def test_get_products(client, product):
    """Test GET /api/products endpoint."""
    response = client.get(url_for('api.get_products'))
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data
    assert len(data['items']) > 0


def test_get_product(client, product):
    """Test GET /api/products/<id> endpoint."""
    response = client.get(url_for('api.get_product', product_id=product.id))
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['id'] == product.id
    assert data['name'] == product.name


def test_get_categories(client, category):
    """Test GET /api/categories endpoint."""
    response = client.get(url_for('api.get_categories'))
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'items' in data
    assert len(data['items']) > 0


def test_get_orders_requires_auth(client):
    """Test that orders endpoint requires authentication."""
    response = client.get(url_for('api.get_orders'))
    assert response.status_code == 401 or response.status_code == 302  # Redirect to login


def test_get_orders_authenticated(client, user):
    """Test GET /api/orders with authentication."""
    # Login
    client.post(url_for('auth.login'), data={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    response = client.get(url_for('api.get_orders'))
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'items' in data


