"""
Database Models
Defines all database models for the e-commerce platform.
"""
from datetime import datetime
from app import db, bcrypt
from flask_login import UserMixin
from sqlalchemy.types import TypeDecorator, String
from app.encryption import AESCipher

cipher = AESCipher()

class EncryptedString(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return cipher.encrypt(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            decrypted = cipher.decrypt(value)
            # If decryption fails (returns None), return the original value
            # This handles legacy plain-text data
            return decrypted if decrypted is not None else value
        return value


class User(UserMixin, db.Model):
    """
    User model for authentication and user management.
    
    Attributes:
        id: Primary key
        email: Unique email address
        username: Unique username
        password_hash: Hashed password
        role: User role (admin, customer)
        is_active: Account activation status
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        orders: Relationship to orders
        cart_items: Relationship to cart items
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='customer', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    phone = db.Column(EncryptedString(255))
    address = db.Column(EncryptedString(1000))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # MFA Fields
    mfa_secret = db.Column(EncryptedString(255))
    mfa_enabled = db.Column(db.Boolean, default=False)
    
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set user password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches the hash."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    """
    Product category model.
    
    Attributes:
        id: Primary key
        name: Category name
        slug: URL-friendly category name
        description: Category description
        created_at: Creation timestamp
        products: Relationship to products
    """
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """
    Product model for e-commerce items.
    
    Attributes:
        id: Primary key
        name: Product name
        slug: URL-friendly product name
        description: Product description
        price: Product price
        stock: Available stock quantity
        image: Product image filename
        category_id: Foreign key to category
        is_active: Product availability status
        created_at: Creation timestamp
        updated_at: Last update timestamp
        order_items: Relationship to order items
        cart_items: Relationship to cart items
    """
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    image = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_in_stock(self):
        """Check if product is in stock."""
        return self.stock > 0 and self.is_active
    
    def __repr__(self):
        return f'<Product {self.name}>'


class CartItem(db.Model):
    """
    Shopping cart item model.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to user
        product_id: Foreign key to product
        quantity: Item quantity
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one cart item per user-product combination
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),)
    
    def get_total(self):
        """Calculate total price for this cart item."""
        return float(self.product.price * self.quantity)
    
    def __repr__(self):
        return f'<CartItem {self.user_id} - {self.product_id}>'


class Order(db.Model):
    """
    Order model for customer purchases.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to user
        order_number: Unique order number
        status: Order status (pending, processing, shipped, delivered, cancelled)
        total_amount: Total order amount
        shipping_address: Delivery address
        payment_method: Payment method used
        created_at: Order creation timestamp
        updated_at: Last update timestamp
        items: Relationship to order items
    """
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='pending', nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(EncryptedString(1000), nullable=False)
    payment_method = db.Column(db.String(50), default='cash_on_delivery')
    
    # Secure Payment Details (Encrypted)
    card_number = db.Column(EncryptedString(255))
    card_expiry = db.Column(EncryptedString(10))
    card_cvv = db.Column(EncryptedString(10))
    bank_account = db.Column(EncryptedString(255))
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    STATUS_CHOICES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    """
    Order item model for individual products in an order.
    
    Attributes:
        id: Primary key
        order_id: Foreign key to order
        product_id: Foreign key to product
        quantity: Item quantity
        price: Price at time of purchase
        created_at: Creation timestamp
    """
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Price at time of purchase
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def get_total(self):
        """Calculate total price for this order item."""
        return float(self.price * self.quantity)
    
    def __repr__(self):
        return f'<OrderItem {self.order_id} - {self.product_id}>'


class AuditLog(db.Model):
    """
    Immutable Audit Log model.
    Records all changes to critical resources.
    """
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable for system actions or unauthenticated
    action = db.Column(db.String(50), nullable=False) # INSERT, UPDATE, DELETE
    resource_type = db.Column(db.String(50), nullable=False) # User, Order, etc.
    resource_id = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text) # JSON string of changes
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.resource_type}:{self.resource_id}>'


