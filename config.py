"""
Secure configuration classes for different environments.
All secrets must be defined in environment variables or an external vault.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    
    # --- SECURITY ---
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is missing! Set it in environment variables or your vault.")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- FILE UPLOAD SETTINGS ---
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # Default: 16MB
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # --- SESSION SECURITY ---
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 86400))  # 24 hours
    SESSION_REFRESH_EACH_REQUEST = True


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

    # Dev database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'sqlite:///ecommerce.db'   # Safe default for development only
    )


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI is missing for production!")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False

    # In-memory DB for tests — not sensitive
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Secure test key (not a real secret)
    SECRET_KEY = 'test-secret-key'
    

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
