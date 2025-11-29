"""
Session Security Utilities
Provides session timeout, IP validation, and session management features.
"""
from datetime import datetime, timedelta
from flask import session, request, current_app
from flask_login import logout_user, current_user
from functools import wraps


def init_session_security(user_id, ip_address):
    """
    Initialize session security data when user logs in.
    
    Args:
        user_id: User ID to store in session
        ip_address: User's IP address
    """
    session['user_id'] = user_id
    session['ip_address'] = ip_address
    session['login_time'] = datetime.utcnow().isoformat()
    session['last_activity'] = datetime.utcnow().isoformat()
    session.permanent = True


def validate_session():
    """
    Validate session security:
    - Check session timeout
    - Validate IP address
    - Update last activity time
    
    Returns:
        bool: True if session is valid, False otherwise
    """
    if not current_user.is_authenticated:
        return True
    
    # Check if session has required security data
    if 'ip_address' not in session or 'last_activity' not in session:
        return False
    
    # Validate IP address
    if not validate_ip_address():
        return False
    
    # Check session timeout
    if is_session_expired():
        return False
    
    # Update last activity time
    session['last_activity'] = datetime.utcnow().isoformat()
    session.modified = True
    
    return True


def validate_ip_address():
    """
    Validate that the current IP matches the session IP.
    
    Returns:
        bool: True if IP matches, False otherwise
    """
    session_ip = session.get('ip_address')
    current_ip = request.remote_addr
    
    if session_ip != current_ip:
        current_app.logger.warning(
            f"IP mismatch for user {current_user.id}: "
            f"session={session_ip}, current={current_ip}"
        )
        return False
    
    return True


def is_session_expired():
    """
    Check if session has expired based on inactivity or absolute timeout.
    
    Returns:
        bool: True if session is expired, False otherwise
    """
    last_activity_str = session.get('last_activity')
    login_time_str = session.get('login_time')
    
    if not last_activity_str or not login_time_str:
        return True
    
    try:
        last_activity = datetime.fromisoformat(last_activity_str)
        login_time = datetime.fromisoformat(login_time_str)
    except (ValueError, TypeError):
        return True
    
    now = datetime.utcnow()
    
    # Check inactivity timeout (30 minutes)
    inactivity_timeout = timedelta(minutes=30)
    if now - last_activity > inactivity_timeout:
        current_app.logger.info(
            f"Session expired due to inactivity for user {current_user.id}"
        )
        return True
    
    # Check absolute session timeout (24 hours)
    absolute_timeout = timedelta(hours=24)
    if now - login_time > absolute_timeout:
        current_app.logger.info(
            f"Session expired due to absolute timeout for user {current_user.id}"
        )
        return True
    
    return False


def clear_session_security():
    """Clear all session security data."""
    session.pop('user_id', None)
    session.pop('ip_address', None)
    session.pop('login_time', None)
    session.pop('last_activity', None)
    session.pop('mfa_user_id', None)
    session.pop('mfa_secret_setup', None)


def session_security_required(f):
    """
    Decorator to enforce session security on routes.
    Validates session and logs out user if session is invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            if not validate_session():
                logout_user()
                clear_session_security()
                from flask import flash, redirect, url_for
                flash('Your session has expired or is invalid. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
