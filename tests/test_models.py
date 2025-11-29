"""
Tests for database models.
"""
import pytest
from app.models import User, Product, Category, Order, OrderItem, CartItem


def test_user_password_hashing(app, user):
    """Test password hashing."""
    assert user.check_password('testpass123')
    assert not user.check_password('wrongpassword')


def test_user_is_admin(app, admin_user):
    """Test admin check."""
    assert admin_user.is_admin()
    assert admin_user.role == 'admin'


def test_product_is_in_stock(app, product):
    """Test product stock check."""
    assert product.is_in_stock()
    
    product.stock = 0
    assert not product.is_in_stock()
    
    product.stock = 5
    product.is_active = False
    assert not product.is_in_stock()


def test_cart_item_total(app, user, product):
    """Test cart item total calculation."""
    from app import db
    cart_item = CartItem(
        user_id=user.id,
        product_id=product.id,
        quantity=2
    )
    db.session.add(cart_item)
    db.session.commit()
    expected_total = float(product.price * 2)
    assert cart_item.get_total() == expected_total


def test_order_item_total(app, product, user):
    """Test order item total calculation."""
    from app import db
    order = Order(
        user_id=user.id,
        order_number='ORD-123',
        total_amount=99.99,
        shipping_address='123 Main St'
    )
    db.session.add(order)
    db.session.flush()
    
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=3,
        price=product.price
    )
    expected_total = float(product.price * 3)
    assert order_item.get_total() == expected_total

