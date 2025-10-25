"""
Authentication module for the Enhanced Library Management System
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models import User
from app import db
from flask import current_app

# Initialize login manager
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    try:
        user = User.query.get(int(user_id))
        if user:
            print(f"DEBUG: Loaded user {user.username} (ID: {user_id}, Role: {user.role})")
        else:
            print(f"DEBUG: No user found for ID: {user_id}")
        return user
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
        return None

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserCreateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create User')

    def validate_username(self, username):
        # Check if username exists in database
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Check if user is already authenticated and redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))

    # Check if admin exists for conditional template logic
    try:
        admin_exists = User.query.filter_by(role='admin').first() is not None
    except Exception as e:
        print(f"Error checking admin existence: {e}")
        admin_exists = False

    form = LoginForm()
    if form.validate_on_submit():
        try:
            print(f"DEBUG: Login attempt for user: {form.username.data}")
            user = User.query.filter_by(username=form.username.data, is_active=True).first()
            if user:
                print(f"DEBUG: User found: {user.username}, Active: {user.is_active}, Role: {user.role}")
                if user.check_password(form.password.data):
                    print(f"DEBUG: Password correct for user: {user.username}")
                    login_user(user)
                    next_page = request.args.get('next')
                    print(f"DEBUG: Next page: {next_page}")
                    flash(f'Welcome back, {user.username}!', 'success')

                    # Validate next_page to prevent redirect loops
                    if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                        print(f"DEBUG: Redirecting to next_page: {next_page}")
                        return redirect(next_page)
                    else:
                        print(f"DEBUG: Redirecting to dashboard")
                        return redirect(url_for('core.dashboard'))
                else:
                    print(f"DEBUG: Password incorrect for user: {user.username}")
                    flash('Invalid username or password.', 'error')
            else:
                print(f"DEBUG: No user found with username: {form.username.data}")
                flash('Invalid username or password.', 'error')
        except Exception as e:
            print(f"Error during login: {e}")
            flash('Login error occurred. Please try again.', 'error')

    return render_template('login.html', form=form, admin_exists=admin_exists)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/create_librarian', methods=['GET', 'POST'])
@login_required
def create_librarian():
    # Check if current user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

    form = UserCreateForm()
    if form.validate_on_submit():
        # Create librarian user using SQLAlchemy
        new_user = User(
            username=form.username.data,
            email=form.username.data + '@library.com',  # Default email
            password_hash='',
            role='librarian',  # Always create librarian
            is_active=True
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        flash('Librarian user created successfully!', 'success')
        return redirect(url_for('core.dashboard'))

    return render_template('create_librarian.html', form=form)

@auth_bp.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    # Check if any admin user exists
    admin_exists = User.query.filter_by(role='admin').first() is not None

    if admin_exists:
        flash('Admin user already exists.', 'warning')
        return redirect(url_for('auth.login'))

    form = UserCreateForm()
    if form.validate_on_submit():
        # Create admin user using SQLAlchemy
        new_user = User(
            username=form.username.data,
            email=form.username.data + '@library.com',  # Default email
            password_hash='',
            role='admin',  # Create admin user
            is_active=True
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        flash('Admin user created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('create_admin.html', form=form)

# Context processor to make current user available in all templates
@auth_bp.context_processor
def inject_user():
    return dict(current_user=current_user)

# Manual user creation for testing (add this if you want to create the Rasmi user)
def create_default_user():
    """Create default librarian user: Rasmi / Admin@159"""
    # Check if user already exists
    existing_user = User.query.filter_by(username='Rasmi').first()
    if not existing_user:
        new_user = User(
            username='Rasmi',
            email='rasmi@iitgn.ac.in',
            password_hash='',
            role='librarian',
            is_active=True
        )
        new_user.set_password('Admin@159')

        db.session.add(new_user)
        db.session.commit()
        print("✅ Default user 'Rasmi' created successfully!")
    else:
        print("ℹ️  User 'Rasmi' already exists")
