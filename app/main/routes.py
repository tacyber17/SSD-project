"""
Main application routes for products, cart, and orders.
"""
from flask import render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.main import main_bp
from app.models import Product, Category, CartItem, Order, OrderItem
from app.forms import CheckoutForm
from app.utils import generate_order_number, slugify


@main_bp.route('/')
@main_bp.route('/index')
def index():
    """Home page with featured products."""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    products = Product.query.filter_by(is_active=True)\
        .order_by(Product.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    categories = Category.query.all()
    
    return render_template('main/index.html', 
                         title='Home',
                         products=products,
                         categories=categories)


@main_bp.route('/products')
def products():
    """Products listing page with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '', type=str)
    
    query = Product.query.filter_by(is_active=True)
    
    # Filter by category
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Search functionality
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%')
            )
        )
    
    products = query.order_by(Product.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    categories = Category.query.all()
    
    return render_template('main/products.html',
                         title='Products',
                         products=products,
                         categories=categories,
                         current_category=category_id,
                         search=search)


@main_bp.route('/product/<slug>')
def product_detail(slug):
    """Product detail page."""
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Get related products from same category
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return render_template('main/product_detail.html',
                         title=product.name,
                         product=product,
                         related_products=related_products)


@main_bp.route('/cart')
@login_required
def cart():
    """Shopping cart page."""
    cart_items = CartItem.query.filter_by(user_id=current_user.id)\
        .join(Product)\
        .filter(Product.is_active == True)\
        .all()
    
    total = sum(item.get_total() for item in cart_items)
    
    return render_template('main/cart.html',
                         title='Shopping Cart',
                         cart_items=cart_items,
                         total=total)


@main_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart."""
    product = Product.query.get_or_404(product_id)
    
    if not product.is_in_stock():
        flash('Product is out of stock.', 'error')
        return redirect(url_for('main.product_detail', slug=product.slug))
    
    quantity = request.form.get('quantity', 1, type=int)
    
    if quantity < 1:
        quantity = 1
    if quantity > product.stock:
        flash(f'Only {product.stock} items available in stock.', 'error')
        return redirect(url_for('main.product_detail', slug=product.slug))
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if cart_item:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            flash(f'Cannot add more. Only {product.stock} items available.', 'error')
            return redirect(url_for('main.cart'))
        cart_item.quantity = new_quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'{product.name} added to cart.', 'success')
    
    return redirect(url_for('main.cart'))


@main_bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update cart item quantity."""
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != current_user.id:
        abort(403)
    
    quantity = request.form.get('quantity', 1, type=int)
    
    if quantity < 1:
        db.session.delete(cart_item)
        flash('Item removed from cart.', 'info')
    else:
        if quantity > cart_item.product.stock:
            flash(f'Only {cart_item.product.stock} items available.', 'error')
            return redirect(url_for('main.cart'))
        cart_item.quantity = quantity
    
    db.session.commit()
    return redirect(url_for('main.cart'))


@main_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove item from cart."""
    cart_item = CartItem.query.get_or_404(item_id)
    
    if cart_item.user_id != current_user.id:
        abort(403)
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    
    return redirect(url_for('main.cart'))


@main_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout page."""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('main.cart'))
    
    # Check stock availability
    for item in cart_items:
        if not item.product.is_in_stock() or item.quantity > item.product.stock:
            flash(f'{item.product.name} is out of stock or quantity exceeds available stock.', 'error')
            return redirect(url_for('main.cart'))
    
    form = CheckoutForm()
    
    if form.validate_on_submit():
        payment_method = form.payment_method.data
        
        # --- Payment Simulation Logic ---
        if payment_method in ['credit_card', 'debit_card']:
            card_num = form.card_number.data.replace(' ', '') if form.card_number.data else ''
            if not card_num or not form.card_expiry.data or not form.card_cvv.data:
                flash('Please provide all card details.', 'error')
                return render_template('main/checkout.html', title='Checkout', form=form, cart_items=cart_items, total=sum(item.get_total() for item in cart_items))
            
            # Magic Number Check
            if card_num == '0000000000000000':
                flash('Payment Declined: Insufficient Funds (Simulation)', 'error')
                return render_template('main/checkout.html', title='Checkout', form=form, cart_items=cart_items, total=sum(item.get_total() for item in cart_items))
            
        elif payment_method == 'bank_transfer':
            if not form.bank_account.data:
                flash('Please provide your bank account number.', 'error')
                return render_template('main/checkout.html', title='Checkout', form=form, cart_items=cart_items, total=sum(item.get_total() for item in cart_items))
        # -------------------------------

        # Create order
        order = Order(
            user_id=current_user.id,
            order_number=generate_order_number(),
            status='pending',
            total_amount=sum(item.get_total() for item in cart_items),
            shipping_address=form.shipping_address.data,
            payment_method=form.payment_method.data,
            
            # Store encrypted payment details
            card_number=form.card_number.data if payment_method in ['credit_card', 'debit_card'] else None,
            card_expiry=form.card_expiry.data if payment_method in ['credit_card', 'debit_card'] else None,
            card_cvv=form.card_cvv.data if payment_method in ['credit_card', 'debit_card'] else None,
            bank_account=form.bank_account.data if payment_method == 'bank_transfer' else None,
            
            notes=form.notes.data
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items and update stock
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
            
            # Update product stock
            cart_item.product.stock -= cart_item.quantity
        
        # Clear cart
        CartItem.query.filter_by(user_id=current_user.id).delete()
        
        db.session.commit()
        
        flash(f'Order placed successfully! Order number: {order.order_number}', 'success')
        return redirect(url_for('main.order_detail', order_id=order.id))
    
    # Pre-fill shipping address if user has one
    if current_user.address:
        form.shipping_address.data = current_user.address
    
    total = sum(item.get_total() for item in cart_items)
    
    return render_template('main/checkout.html',
                         title='Checkout',
                         form=form,
                         cart_items=cart_items,
                         total=total)


@main_bp.route('/orders')
@login_required
def orders():
    """User orders listing page."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    orders = Order.query.filter_by(user_id=current_user.id)\
        .order_by(Order.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('main/orders.html',
                         title='My Orders',
                         orders=orders)


@main_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail page."""
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    
    return render_template('main/order_detail.html',
                         title=f'Order {order.order_number}',
                         order=order)


