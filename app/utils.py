"""
Utility functions for the application.
"""
import os
import secrets
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_product_image(file, product_id=None):
    """
    Save uploaded product image with secure filename.
    
    Args:
        file: Uploaded file object
        product_id: Optional product ID for filename
    
    Returns:
        Filename of saved image or None if error
    """
    if file and allowed_file(file.filename):
        # Generate secure filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        random_hex = secrets.token_hex(8)
        
        if product_id:
            filename = f"product_{product_id}_{random_hex}.{file_ext}"
        else:
            filename = f"product_{random_hex}.{file_ext}"
        
        filename = secure_filename(filename)
        # Get absolute path for uploads
        upload_dir = os.path.join(
            current_app.root_path,
            current_app.config['UPLOAD_FOLDER'],
            'products'
        )
        os.makedirs(upload_dir, exist_ok=True)
        
        upload_path = os.path.join(upload_dir, filename)
        
        # Resize and save image
        try:
            img = Image.open(file)
            # Resize if image is too large (max 800x800)
            max_size = (800, 800)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(upload_path)
            return filename
        except Exception as e:
            current_app.logger.error(f"Error saving image: {str(e)}")
            return None
    
    return None


def delete_product_image(filename):
    """Delete product image file."""
    if filename:
        file_path = os.path.join(
            current_app.root_path,
            current_app.config['UPLOAD_FOLDER'],
            'products',
            filename
        )
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                current_app.logger.error(f"Error deleting image: {str(e)}")
                return False
    return False


def generate_order_number():
    """Generate unique order number."""
    import random
    import string
    from datetime import datetime
    timestamp = str(int(datetime.utcnow().timestamp()))
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD-{timestamp}-{random_str}"


def slugify(text):
    """Convert text to URL-friendly slug."""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')



