import json
from datetime import datetime
from flask import has_request_context, request
from flask_login import current_user
from sqlalchemy import event, inspect
from app import db
from app.models import AuditLog

def get_current_user_id():
    """Helper to safely get current user ID."""
    if has_request_context() and current_user.is_authenticated:
        return current_user.id
    return None

def get_ip_address():
    """Helper to safely get IP address."""
    if has_request_context():
        return request.remote_addr
    return 'system'

def create_audit_log(action, target, details=None, connection=None):
    """Create and save an audit log entry."""
    try:
        # Avoid infinite recursion
        if isinstance(target, AuditLog):
            return

        # Prepare data
        log_data = {
            'user_id': get_current_user_id(),
            'action': action,
            'resource_type': target.__class__.__name__,
            'resource_id': str(target.id),
            'details': json.dumps(details, default=str) if details else None,
            'ip_address': get_ip_address(),
            'timestamp': datetime.utcnow()
        }
        
        # Use the existing connection to insert directly
        # This avoids session flushing issues within event listeners
        if connection:
            connection.execute(
                AuditLog.__table__.insert().values(**log_data)
            )
        else:
            # Fallback if no connection provided (shouldn't happen in listeners)
            # But if called manually, we might need a session.
            # For now, we rely on the listener's connection.
            pass
            
    except Exception as e:
        print(f"Failed to create audit log: {e}")

def after_insert_listener(mapper, connection, target):
    """Listener for INSERT events."""
    details = {attr.key: getattr(target, attr.key) for attr in mapper.column_attrs}
    create_audit_log('INSERT', target, details, connection)

def after_update_listener(mapper, connection, target):
    """Listener for UPDATE events."""
    state = inspect(target)
    changes = {}
    
    for attr in mapper.column_attrs:
        hist = getattr(state.attrs, attr.key).history
        if hist.has_changes():
            changes[attr.key] = {
                'old': hist.deleted[0] if hist.deleted else None,
                'new': hist.added[0] if hist.added else None
            }
            
    if changes:
        create_audit_log('UPDATE', target, changes, connection)

def after_delete_listener(mapper, connection, target):
    """Listener for DELETE events."""
    details = {attr.key: getattr(target, attr.key) for attr in mapper.column_attrs}
    create_audit_log('DELETE', target, details, connection)

def register_audit_listeners(models):
    """Register audit listeners for the given models."""
    for model in models:
        event.listen(model, 'after_insert', after_insert_listener)
        event.listen(model, 'after_update', after_update_listener)
        event.listen(model, 'after_delete', after_delete_listener)
