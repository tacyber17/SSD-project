"""
Flask Application Factory
Creates and configures the Flask application instance.
"""
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from markupsafe import Markup
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name='development'):
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name: Configuration environment (development, production, testing)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    limiter.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register custom Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(value):
        """Convert newlines to HTML <br> tags."""
        if value is None:
            return ''
        return Markup(str(value).replace('\n', '<br>\n'))
    
    @app.template_filter('product_image')
    def product_image_filter(product):
        """Get product image URL or placeholder based on category."""
        from flask import url_for
        
        if product.image:
            return url_for('uploaded_file', filename='products/' + product.image)
        
        # Generate placeholder image using product ID for consistent images
        # Using Picsum Photos with product ID as seed for consistent random images
        width, height = 400, 400
        seed = product.id if hasattr(product, 'id') else hash(product.name) % 1000
        
        # Use Picsum Photos for beautiful random placeholder images
        # Seed ensures same product gets same image
        return f"https://picsum.photos/seed/{seed}/{width}/{height}"
    
    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.api import api_bp
    from app.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create upload directories (use absolute path)
    upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'products'), exist_ok=True)
    
    # Serve static files from uploads directory
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files."""
        from flask import send_from_directory
        return send_from_directory(upload_folder, filename)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file upload size limit errors."""
        from flask import render_template, flash, redirect, url_for
        flash('File is too large. Maximum size is 16MB.', 'error')
        return redirect(url_for('main.index'))
    
    # Session Security - Validate sessions before each request
    @app.before_request
    def validate_session_security():
        """Validate session security on each request."""
        from app.session_security import validate_session, clear_session_security
        from flask_login import logout_user
        from flask import flash, redirect, url_for, request
        
        # Skip validation for static files and auth routes
        if request.endpoint and (request.endpoint.startswith('static') or 
                                 request.endpoint.startswith('uploaded_file')):
            return
        
        if current_user.is_authenticated:
            if not validate_session():
                logout_user()
                clear_session_security()
                flash('Your session has expired or is invalid. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
    
    # Register Audit Listeners
    with app.app_context():
        from app.models import User, Order, Product
        from app.audit import register_audit_listeners
        register_audit_listeners([User, Order, Product])
    
    return app

