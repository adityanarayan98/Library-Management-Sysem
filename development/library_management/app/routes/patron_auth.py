"""
Patron authentication routes for the Library Management System
Separate from librarian authentication - handles patron login/logout
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from werkzeug.security import check_password_hash
from app.models import Patron, Book, Transaction, LibrarySettings
from app import db
from datetime import datetime, timedelta

# Patron login manager (separate from librarian login)
patron_login_manager = LoginManager()

class PatronUserMixin:
    """Mixin for patron user functionality"""
    def get_id(self):
        return str(self.patron_id)

    @property
    def is_active(self):
        return self.patron.status == 'active'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

class PatronSession:
    """Patron session management"""
    def __init__(self, patron):
        self.patron = patron
        self.patron_id = patron.id

    def get_id(self):
        return str(self.patron_id)

    @property
    def is_active(self):
        return self.patron.status == 'active'

patron_auth_bp = Blueprint('patron_auth', __name__)

class PatronLoginForm(FlaskForm):
    roll_no = StringField('Roll Number', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PatronChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')

@patron_auth_bp.route('/patron/login', methods=['GET', 'POST'])
def patron_login():
    """Patron login page"""
    if 'patron_id' in session:
        return redirect(url_for('patron_auth.patron_dashboard'))

    form = PatronLoginForm()
    if form.validate_on_submit():
        patron = Patron.query.filter_by(roll_no=form.roll_no.data, status='active').first()

        # Debug logging
        print(f"DEBUG: Login attempt for roll_no: {form.roll_no.data}")
        print(f"DEBUG: Patron found: {patron.name if patron else 'None'}")
        if patron:
            print(f"DEBUG: Patron status: {patron.status}")
            print(f"DEBUG: Password check: {patron.check_password(form.password.data)}")

        if patron and patron.check_password(form.password.data):
            # Check if first login - require password change
            if patron.first_login:
                session['patron_id'] = patron.id
                session['require_password_change'] = True
                flash('Please change your password to continue.', 'warning')
                return redirect(url_for('patron_auth.change_password'))

            # Regular login
            session['patron_id'] = patron.id
            session['patron_roll_no'] = patron.roll_no
            flash(f'Welcome back, {patron.name}!', 'success')
            return redirect(url_for('patron_auth.patron_dashboard'))
        else:
            flash('Invalid roll number or password.', 'error')

    return render_template('opac/patron_login.html', form=form)

@patron_auth_bp.route('/patron/logout')
def patron_logout():
    """Patron logout"""
    session.pop('patron_id', None)
    session.pop('patron_roll_no', None)
    session.pop('require_password_change', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('opac.search'))

@patron_auth_bp.route('/patron/dashboard')
def patron_dashboard():
    """Patron dashboard - requires login"""
    if 'patron_id' not in session:
        flash('Please login to access your dashboard.', 'warning')
        return redirect(url_for('patron_auth.patron_login'))

    patron = Patron.query.get(session['patron_id'])
    if not patron or patron.status != 'active':
        session.pop('patron_id', None)
        flash('Access denied. Please contact librarian.', 'error')
        return redirect(url_for('opac.search'))

    # Get patron's current transactions (issued books)
    current_books = Transaction.query.filter_by(
        patron_id=patron.id,
        status='issued'
    ).order_by(Transaction.due_date.asc()).all()

    # Calculate statistics
    current_loans = len(current_books)
    print(f"DEBUG: Patron {patron.name} has {current_loans} current books")
    overdue_books = 0
    for t in current_books:
        print(f"DEBUG: Book {t.book.title}, due_date: {t.due_date}, type: {type(t.due_date)}, is_overdue: {t.is_overdue()}")
        if t.is_overdue():
            overdue_books += 1
    total_borrowed = len(current_books) + len([t for t in Transaction.query.filter_by(patron_id=patron.id, status='returned').all()])

    # Calculate total outstanding fines
    total_fines = 0.0
    for t in current_books:
        if not t.fine_paid and (t.fine_amount or 0) > 0:
            fine = float(t.fine_amount or 0)
            total_fines += fine
            print(f"DEBUG: Transaction {t.id} fine: {fine}")
    print(f"DEBUG: Total fines: {total_fines}")

    # Get librarian email from settings
    librarian_email = LibrarySettings.get_setting('librarian_email', 'library@example.com')

    return render_template('opac/patron_dashboard.html',
                         patron=patron,
                         current_loans=current_loans,
                         overdue_books=overdue_books,
                         total_borrowed=total_borrowed,
                         total_fines=total_fines,
                         current_loans_list=current_books,
                         datetime=datetime,
                         librarian_email=librarian_email)

@patron_auth_bp.route('/patron/change_password', methods=['GET', 'POST'])
def change_password():
    """Change patron password"""
    if 'patron_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('patron_auth.patron_login'))

    patron = Patron.query.get(session['patron_id'])
    if not patron:
        session.pop('patron_id', None)
        flash('Patron not found.', 'error')
        return redirect(url_for('opac.search'))

    form = PatronChangePasswordForm()

    if form.validate_on_submit():
        # Validate current password
        if not patron.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return redirect(request.url)

        # Validate new password
        if form.new_password.data != form.confirm_password.data:
            flash('New password and confirmation do not match.', 'error')
            return redirect(request.url)

        # Update password
        patron.set_password(form.new_password.data)

        # Update optional contact information if provided
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        division = request.form.get('division', '').strip()

        # Only update fields if they have values
        if email:
            patron.email = email
        if phone:
            patron.phone = phone
        if department:
            patron.department = department
        if division:
            patron.division = division

        # Update timestamp
        patron.updated_at = datetime.utcnow()

        db.session.commit()

        # Clear first login flag if this was first login
        if session.get('require_password_change'):
            session.pop('require_password_change', None)
            if email or phone or department or division:
                flash('Password changed successfully! Thank you for providing your contact information.', 'success')
            else:
                flash('Password changed successfully! Welcome to the library system.', 'success')
            return redirect(url_for('patron_auth.patron_dashboard'))
        else:
            flash('Password changed successfully!', 'success')
            return redirect(url_for('patron_auth.patron_dashboard'))

    return render_template('opac/patron_change_password.html', patron=patron, form=form)







# Decorator to require patron login
def patron_login_required(f):
    """Decorator to require patron login"""
    def decorated_function(*args, **kwargs):
        if 'patron_id' not in session:
            flash('Please login to access this feature.', 'warning')
            return redirect(url_for('patron_auth.patron_login', next=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function
