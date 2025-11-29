"""
REST API routes for JSON endpoints.
"""
from flask import jsonify, request, abort
from flask_login import login_required, current_user
from app import db
from app.api import api_bp
from app.models import Product, Category, Order, User
from functools import wraps


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/products', methods=['GET'])
def get_products():
    """Get list of products with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '', type=str)
    
    query = Product.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(Product.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    products = [{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'description': p.description,
        'price': float(p.price),
        'stock': p.stock,
        'image': p.image,
        'category': p.category.name if p.category else None,
        'created_at': p.created_at.isoformat()
    } for p in pagination.items]
    
    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'items': products
    })


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product details."""
    product = Product.query.get_or_404(product_id)
    
    if not product.is_active:
        abort(404)
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'price': float(product.price),
        'stock': product.stock,
        'image': product.image,
        'category': {
            'id': product.category.id,
            'name': product.category.name
        } if product.category else None,
        'created_at': product.created_at.isoformat()
    })


@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get list of categories."""
    categories = Category.query.all()
    
    return jsonify({
        'items': [{
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'description': c.description
        } for c in categories]
    })


@api_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Get user's orders (requires authentication)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Order.query.filter_by(user_id=current_user.id)
    
    pagination = query.order_by(Order.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    orders = [{
        'id': o.id,
        'order_number': o.order_number,
        'status': o.status,
        'total_amount': float(o.total_amount),
        'created_at': o.created_at.isoformat()
    } for o in pagination.items]
    
    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'items': orders
    })


@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Get order details (requires authentication)."""
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    
    return jsonify({
        'id': order.id,
        'order_number': order.order_number,
        'status': order.status,
        'total_amount': float(order.total_amount),
        'shipping_address': order.shipping_address,
        'payment_method': order.payment_method,
        'created_at': order.created_at.isoformat(),
        'items': [{
            'product_id': item.product_id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.price),
            'total': float(item.get_total())
        } for item in order.items]
    })


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors in API."""
    return jsonify({'error': 'Resource not found'}), 404


@api_bp.errorhandler(403)
def forbidden(error):
    """Handle 403 errors in API."""
    return jsonify({'error': 'Forbidden'}), 403


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors in API."""
    return jsonify({'error': 'Internal server error'}), 500


