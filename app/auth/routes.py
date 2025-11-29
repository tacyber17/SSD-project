"""
Authentication routes for user registration, login, and logout.
"""
import io
import base64
import pyotp
import qrcode
from flask import render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.auth import auth_bp
from app.models import User
from app.forms import RegistrationForm, LoginForm, ChangePasswordForm, UpdateProfileForm, EnableMFAForm, VerifyMFAForm
from app.session_security import init_session_security, clear_session_security
from urllib.parse import urlparse, urljoin
from flask import request

def is_safe_url(target):
    """
    Validates that the redirect URL is safe (same server or explicitly trusted).
    Prevents open redirect vulnerabilities.
    """
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))

    return (
        redirect_url.scheme in ('http', 'https') and
        host_url.netloc == redirect_url.netloc
    )


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return redirect(url_for('auth.login'))
            
            # Check for MFA
            if user.mfa_enabled:
                session['mfa_user_id'] = user.id
                return redirect(url_for('auth.verify_2fa_login'))
            
            # Login user and initialize session security
            login_user(user, remember=form.remember_me.data)
            init_session_security(user.id, request.remote_addr)
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', title='Log In', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route."""
    logout_user()
    clear_session_security()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile view and update route."""
    form = UpdateProfileForm(
        original_username=current_user.username,
        original_email=current_user.email,
        obj=current_user
    )
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', title='Profile', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Password change route."""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been changed.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', title='Change Password', form=form)


@auth_bp.route('/enable-2fa', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    """Enable 2FA setup route."""
    if current_user.mfa_enabled:
        flash('2FA is already enabled.', 'info')
        return redirect(url_for('auth.profile'))
    
    form = EnableMFAForm()
    
    if request.method == 'GET':
        # Generate a new secret
        secret = pyotp.random_base32()
        session['mfa_secret_setup'] = secret
    else:
        secret = session.get('mfa_secret_setup')
    
    if not secret:
        flash('Session expired. Please try again.', 'error')
        return redirect(url_for('auth.enable_2fa'))
    
    # Generate QR Code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.email, issuer_name='EcommerceApp')
    
    qr = qrcode.make(provisioning_uri)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    if form.validate_on_submit():
        if totp.verify(form.code.data):
            current_user.mfa_secret = secret
            current_user.mfa_enabled = True
            db.session.commit()
            session.pop('mfa_secret_setup', None)
            flash('Two-Factor Authentication enabled successfully!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Invalid verification code. Please try again.', 'error')
            
    return render_template('auth/enable_2fa.html', title='Enable 2FA', form=form, qr_code=qr_code, secret=secret)


@auth_bp.route('/verify-2fa-login', methods=['GET', 'POST'])
def verify_2fa_login():
    """Verify 2FA during login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    user_id = session.get('mfa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
        
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))
        
    form = VerifyMFAForm()
    
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(form.code.data):
            # Login user and initialize session security
            login_user(user)
            init_session_security(user.id, request.remote_addr)
            session.pop('mfa_user_id', None)
            
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid authentication code.', 'error')
            
    return render_template('auth/verify_2fa.html', title='Verify 2FA', form=form)


@auth_bp.route('/disable-2fa')
@login_required
def disable_2fa():
    """Disable 2FA."""
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.session.commit()
    flash('Two-Factor Authentication has been disabled.', 'info')
    return redirect(url_for('auth.profile'))






