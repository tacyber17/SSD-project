"""
Admin panel routes for managing products, orders, and users.
"""
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.admin import admin_bp
from app.models import Product, Category, Order, User, OrderItem
from app.forms import ProductForm, CategoryForm, OrderStatusForm
from app.utils import save_product_image, delete_product_image, slugify
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


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard."""
    stats = {
        'total_products': Product.query.count(),
        'active_products': Product.query.filter_by(is_active=True).count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'total_users': User.query.count(),
        'total_categories': Category.query.count()
    }
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         title='Admin Dashboard',
                         stats=stats,
                         recent_orders=recent_orders)


@admin_bp.route('/products')
@admin_required
def products():
    """Admin products listing."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '', type=str)
    
    query = Product.query
    
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%')
            )
        )
    
    products = query.order_by(Product.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/products.html',
                         title='Manage Products',
                         products=products,
                         search=search)


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def new_product():
    """Create new product."""
    form = ProductForm()
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            slug=slugify(form.name.data),
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            category_id=form.category_id.data,
            is_active=form.is_active.data
        )
        
        db.session.add(product)
        db.session.flush()  # Get product ID
        
        # Save image if uploaded
        if form.image.data:
            filename = save_product_image(form.image.data, product.id)
            if filename:
                product.image = filename
        
        db.session.commit()
        flash('Product created successfully.', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html',
                         title='New Product',
                         form=form)


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit existing product."""
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.slug = slugify(form.name.data)
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.category_id = form.category_id.data
        product.is_active = form.is_active.data
        
        # Handle image upload
        if form.image.data:
            # Delete old image
            if product.image:
                delete_product_image(product.image)
            
            # Save new image
            filename = save_product_image(form.image.data, product.id)
            if filename:
                product.image = filename
        
        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html',
                         title='Edit Product',
                         form=form,
                         product=product)


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Delete product."""
    product = Product.query.get_or_404(product_id)
    
    # Delete associated image
    if product.image:
        delete_product_image(product.image)
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/categories')
@admin_required
def categories():
    """Admin categories listing."""
    categories = Category.query.all()
    return render_template('admin/categories.html',
                         title='Manage Categories',
                         categories=categories)


@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@admin_required
def new_category():
    """Create new category."""
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            slug=slugify(form.name.data),
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully.', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html',
                         title='New Category',
                         form=form)


@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """Edit existing category."""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = slugify(form.name.data)
        category.description = form.description.data
        db.session.commit()
        flash('Category updated successfully.', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html',
                         title='Edit Category',
                         form=form,
                         category=category)


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    """Delete category."""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has products
    if category.products.count() > 0:
        flash('Cannot delete category with existing products.', 'error')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/orders')
@admin_required
def orders():
    """Admin orders listing."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', '', type=str)
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/orders.html',
                         title='Manage Orders',
                         orders=orders,
                         status=status)


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    """Admin order detail view."""
    order = Order.query.get_or_404(order_id)
    form = OrderStatusForm(obj=order)
    
    if form.validate_on_submit():
        order.status = form.status.data
        db.session.commit()
        flash('Order status updated.', 'success')
        return redirect(url_for('admin.order_detail', order_id=order.id))
    
    return render_template('admin/order_detail.html',
                         title=f'Order {order.order_number}',
                         order=order,
                         form=form)


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order status."""
    order = Order.query.get_or_404(order_id)
    form = OrderStatusForm()
    
    if form.validate_on_submit():
        order.status = form.status.data
        db.session.commit()
        flash('Order status updated successfully.', 'success')
    
    return redirect(url_for('admin.order_detail', order_id=order.id))


@admin_bp.route('/users')
@admin_required
def users():
    """Admin users listing."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '', type=str)
    
    query = User.query
    
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    users = query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html',
                         title='Manage Users',
                         users=users,
                         search=search)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user."""
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/orders/<int:order_id>/delete', methods=['POST'])
@admin_required
def delete_order(order_id):
    """Delete order."""
    order = Order.query.get_or_404(order_id)
    
    db.session.delete(order)
    db.session.commit()
    
    flash('Order deleted successfully.', 'success')
    return redirect(url_for('admin.orders'))


