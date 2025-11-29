"""
Pytest configuration and fixtures.
"""
import pytest
import os
import tempfile
from app import create_app, db
from app.models import User, Product, Category


@pytest.fixture
def app():
    """Create application for testing."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role='customer'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Create a test admin user."""
    with app.app_context():
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        admin.set_password('adminpass123')
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def category(app):
    """Create a test category."""
    with app.app_context():
        category = Category(
            name='Test Category',
            slug='test-category',
            description='Test category description'
        )
        db.session.add(category)
        db.session.commit()
        return category


@pytest.fixture
def product(app, category):
    """Create a test product."""
    with app.app_context():
        product = Product(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            price=99.99,
            stock=10,
            category_id=category.id,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        return product


