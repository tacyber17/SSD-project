"""
WTForms for form validation and rendering.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, DecimalField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError, Optional, Regexp
from app.models import User, Product, Category


class RegistrationForm(FlaskForm):
    """User registration form."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=80, message='Username must be between 4 and 80 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=1, max=100)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(min=1, max=100)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Check if username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email is already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please use a different email or log in.')


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class ProductForm(FlaskForm):
    """Product creation/editing form."""
    name = StringField('Product Name', validators=[
        DataRequired(),
        Length(min=1, max=200)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, message='Description must be at least 10 characters.')
    ])
    price = DecimalField('Price', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Price must be greater than 0.')
    ], places=2)
    stock = IntegerField('Stock Quantity', validators=[
        DataRequired(),
        NumberRange(min=0, message='Stock cannot be negative.')
    ])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = FileField('Product Image', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Only image files are allowed.')
    ])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Product')
    
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]


class CategoryForm(FlaskForm):
    """Category creation/editing form."""
    name = StringField('Category Name', validators=[
        DataRequired(),
        Length(min=1, max=100)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')
    
    def validate_name(self, name):
        """Check if category name is already taken."""
        category = Category.query.filter_by(name=name.data).first()
        if category and (not hasattr(self, 'category_id') or category.id != self.category_id):
            raise ValidationError('Category name already exists.')


class CheckoutForm(FlaskForm):
    """Order checkout form."""
    shipping_address = TextAreaField('Shipping Address', validators=[
        DataRequired(),
        Length(min=10, message='Please provide a complete shipping address.')
    ])
    payment_method = SelectField('Payment Method', choices=[
        ('cash_on_delivery', 'Cash on Delivery'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer')
    ], validators=[DataRequired()])
    
    # Payment Details (Optional - validation handled in route)
    card_number = StringField('Card Number', validators=[
        Optional(),
        Length(min=16, max=20),
        Regexp(r'^[0-9\s]*$', message='Card number must contain only digits and spaces.')
    ])
    card_expiry = StringField('Expiry Date (MM/YY)', validators=[
        Optional(),
        Length(min=5, max=5),
        Regexp(r'^(0[1-9]|1[0-2])\/\d{2}$', message='Invalid format. Use MM/YY.')
    ])
    card_cvv = StringField('CVV', validators=[
        Optional(),
        Length(min=3, max=4),
        Regexp(r'^\d{3,4}$', message='CVV must be 3 or 4 digits.')
    ])
    bank_account = StringField('Bank Account Number', validators=[
        Optional(),
        Length(min=10, max=30),
        Regexp(r'^[0-9a-zA-Z]+$', message='Account number must contain only letters and numbers.')
    ])
    notes = TextAreaField('Order Notes (Optional)', validators=[Optional()])
    submit = SubmitField('Place Order')


class UpdateProfileForm(FlaskForm):
    """User profile update form."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=1, max=100)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(min=1, max=100)
    ])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Update Profile')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        """Check if username is already taken by another user."""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is already taken.')
    
    def validate_email(self, email):
        """Check if email is already registered by another user."""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email is already registered.')


class ChangePasswordForm(FlaskForm):
    """Password change form."""
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')


class OrderStatusForm(FlaskForm):
    """Order status update form (admin only)."""
    status = SelectField('Order Status', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Status')


class EnableMFAForm(FlaskForm):
    """Form to verify MFA setup with a code."""
    code = StringField('Verification Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Code must be 6 digits.')
    ])
    submit = SubmitField('Verify & Enable')


class VerifyMFAForm(FlaskForm):
    """Form to verify MFA during login."""
    code = StringField('Authentication Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Code must be 6 digits.')
    ])
    submit = SubmitField('Verify')



