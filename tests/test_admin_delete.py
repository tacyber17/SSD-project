import pytest
from app import create_app, db
from app.models import User, Order, Product, Category
from flask_login import login_user

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_user_id(app):
    with app.app_context():
        user = User(
            username="admin",
            email="admin@example.com",
            password_hash="hash",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        return user.id

@pytest.fixture
def regular_user_id(app):
    with app.app_context():
        user = User(
            username="user",
            email="user@example.com",
            password_hash="hash",
            first_name="Regular",
            last_name="User",
            role="customer"
        )
        db.session.add(user)
        db.session.commit()
        return user.id

def test_delete_user(client, admin_user_id, regular_user_id):
    # Login as admin
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user_id)
        sess['_fresh'] = True

    # Verify user exists
    with client.application.app_context():
        assert User.query.get(regular_user_id) is not None

    # Delete user
    response = client.post(f'/admin/users/{regular_user_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'User deleted successfully' in response.data

    # Verify user is gone
    with client.application.app_context():
        assert User.query.get(regular_user_id) is None

def test_delete_order(client, admin_user_id, regular_user_id):
    # Create an order
    with client.application.app_context():
        order = Order(
            user_id=regular_user_id,
            order_number="ORD-123",
            total_amount=100.00,
            shipping_address="123 Test St"
        )
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    # Login as admin
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user_id)
        sess['_fresh'] = True

    # Verify order exists
    with client.application.app_context():
        assert Order.query.get(order_id) is not None

    # Delete order
    response = client.post(f'/admin/orders/{order_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Order deleted successfully' in response.data

    # Verify order is gone
    with client.application.app_context():
        assert Order.query.get(order_id) is None
