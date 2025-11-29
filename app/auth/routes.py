"""
Authentication routes for user registration, login, logout, MFA, and profile management.
Fully secured version with safe redirects and hardened logic.
"""

import io
import base64
import pyotp
import qrcode

from flask import (
    render_template, redirect, url_for, flash,
    request, session
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)

from urllib.parse import urlparse, urljoin

from app import db, limiter
from app.auth import auth_bp
from app.models import User
from app.forms import (
    RegistrationForm, LoginForm, ChangePasswordForm,
    UpdateProfileForm, EnableMFAForm, VerifyMFAForm
)
from app.session_security import init_session_security, clear_session_security


# ==================================================================
# SAFE REDIRECT VALIDATION
# ==================================================================
def is_safe_url(target: str) -> bool:
    """
    Ensures the redirect target is safe:
    - Must be same host (defense against open redirects)
    - Must use HTTP/HTTPS
    """
    if not target:
        return False

    host_url = request.host_url
    test_url = urljoin(host_url, target)

    parsed_host = urlparse(host_url)
    parsed_test = urlparse(test_url)

    return (
        parsed_test.scheme in ("http", "https")
        and parsed_host.netloc == parsed_test.netloc
    )


def redirect_back(default='main.index'):
    """
    Safe helper for all redirects that depend on ?next=.
    """
    next_url = request.args.get('next')
    if next_url and is_safe_url(next_url):
        return redirect(next_url)
    return redirect(url_for(default))


# ==================================================================
# REGISTRATION
# ==================================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
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


# ==================================================================
# LOGIN
# ==================================================================
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
                flash('Your account has been deactivated. Contact support.', 'error')
                return redirect(url_for('auth.login'))

            # MFA Flow
            if user.mfa_enabled:
                session['mfa_user_id'] = user.id
                return redirect(url_for('auth.verify_2fa_login'))

            # Normal login
            login_user(user, remember=form.remember_me.data)
            init_session_security(user.id, request.remote_addr)

            return redirect_back()

        flash('Invalid email or password.', 'error')

    return render_template('auth/login.html', title='Log In', form=form)


# ==================================================================
# LOGOUT
# ==================================================================
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    clear_session_security()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# ==================================================================
# PROFILE
# ==================================================================
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
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


# ==================================================================
# CHANGE PASSWORD
# ==================================================================
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
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


# ==================================================================
# ENABLE 2FA
# ==================================================================
@auth_bp.route('/enable-2fa', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    if current_user.mfa_enabled:
        flash('2FA is already enabled.', 'info')
        return redirect(url_for('auth.profile'))

    form = EnableMFAForm()

    # Generate a new secret for QR Code (on GET)
    if request.method == 'GET':
        secret = pyotp.random_base32()
        session['mfa_secret_setup'] = secret
    else:
        secret = session.get('mfa_secret_setup')

    if not secret:
        flash('Session expired. Try again.', 'error')
        return redirect(url_for('auth.enable_2fa'))

    # Generate QR Code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.email, issuer_name='EcommerceApp')

    qr = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode('utf-8')

    if form.validate_on_submit():
        if totp.verify(form.code.data):
            current_user.mfa_secret = secret
            current_user.mfa_enabled = True
            db.session.commit()

            session.pop('mfa_secret_setup', None)

            flash('Two-Factor Authentication enabled!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Invalid verification code.', 'error')

    return render_template(
        'auth/enable_2fa.html',
        title='Enable 2FA',
        form=form,
        qr_code=qr_code,
        secret=secret
    )


# ==================================================================
# VERIFY 2FA LOGIN
# ==================================================================
@auth_bp.route('/verify-2fa-login', methods=['GET', 'POST'])
def verify_2fa_login():
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
            login_user(user)
            init_session_security(user.id, request.remote_addr)

            session.pop('mfa_user_id', None)

            return redirect_back()

        flash('Invalid authentication code.', 'error')

    return render_template('auth/verify_2fa.html', title='Verify 2FA', form=form)


# ==================================================================
# DISABLE 2FA
# ==================================================================
@auth_bp.route('/disable-2fa')
@login_required
def disable_2fa():
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.session.commit()

    flash('Two-Factor Authentication has been disabled.', 'info')
    return redirect(url_for('auth.profile'))
