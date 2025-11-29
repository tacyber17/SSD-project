import pytest
from app import create_app, db
from app.models import User
from app.encryption import AESCipher
import base64

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_encryption_utility():
    """Test the raw encryption utility."""
    cipher = AESCipher()
    original_text = "Secret Data 123"
    
    # Test Encrypt
    encrypted = cipher.encrypt(original_text)
    assert encrypted != original_text
    assert isinstance(encrypted, str)
    
    # Test Decrypt
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == original_text

def test_model_encryption(app):
    """Test that model fields are encrypted in DB but decrypted on access."""
    with app.app_context():
        # Create user with sensitive data
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            first_name="Test",
            last_name="User",
            phone="123-456-7890",
            address="123 Secret St",
            mfa_secret="MYSECRETKEY"
        )
        db.session.add(user)
        db.session.commit()
        
        # 1. Verify transparent access (Decryption)
        loaded_user = User.query.filter_by(username="testuser").first()
        assert loaded_user.phone == "123-456-7890"
        assert loaded_user.address == "123 Secret St"
        assert loaded_user.mfa_secret == "MYSECRETKEY"
        
        # 2. Verify storage (Encryption)
        # We inspect the raw DB value. 
        # In SQLAlchemy, we can execute raw SQL to see what's actually stored.
        from sqlalchemy import text
        result = db.session.execute(text("SELECT phone, address, mfa_secret FROM users WHERE username='testuser'")).fetchone()
        
        raw_phone = result[0]
        raw_address = result[1]
        raw_mfa = result[2]
        
        # Ensure they are NOT the plain text
        assert raw_phone != "123-456-7890"
        assert raw_address != "123 Secret St"
        assert raw_mfa != "MYSECRETKEY"
        
        # Ensure they look like base64 (just a basic check)
        # They should be decryptable by our cipher
        cipher = AESCipher()
        assert cipher.decrypt(raw_phone) == "123-456-7890"
        assert cipher.decrypt(raw_address) == "123 Secret St"
        assert cipher.decrypt(raw_mfa) == "MYSECRETKEY"

def test_legacy_data_handling(app):
    """Test that accessing legacy plain-text data works (regression test)."""
    import pyotp
    with app.app_context():
        # 1. Insert a user using raw SQL to simulate legacy plain-text data
        from sqlalchemy import text
        db.session.execute(text(
            "INSERT INTO users (username, email, password_hash, first_name, last_name, mfa_secret, mfa_enabled, created_at, updated_at, role, is_active) "
            "VALUES ('legacy', 'legacy@example.com', 'hash', 'Legacy', 'User', 'JBSWY3DPEHPK3PXP', 1, '2023-01-01', '2023-01-01', 'customer', 1)"
        ))
        db.session.commit()
        
        # 2. Load the user via the model
        user = User.query.filter_by(username='legacy').first()
        
        # 3. Check mfa_secret - it should be the original plain text
        assert user.mfa_secret == 'JBSWY3DPEHPK3PXP'
        
        # 4. Verify pyotp works
        totp = pyotp.TOTP(user.mfa_secret)
        assert totp.now()
