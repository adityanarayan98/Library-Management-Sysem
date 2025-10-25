"""
Core routes for the Library Management System
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import User, Patron, Book, Category, Transaction, LibrarySettings
from app import db
from datetime import datetime, date

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
def index():
    """Main entry point - redirect to dashboard if authenticated, otherwise to login"""
    try:
        print(f"DEBUG: Index route accessed. Current user authenticated: {current_user.is_authenticated}")
        if current_user.is_authenticated:
            print(f"DEBUG: User {current_user.username} is authenticated, redirecting to dashboard")
            return redirect(url_for('core.dashboard'))
        else:
            print(f"DEBUG: User not authenticated, redirecting to login")
            return redirect(url_for('auth.login'))
    except Exception as e:
        print(f"Error in index route: {e}")
        # If there's any error with authentication check, redirect to login
        return redirect(url_for('auth.login'))

@core_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard view with library statistics"""
    from datetime import datetime as dt

    print(f"DEBUG: Dashboard accessed by user: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")

    try:
        # Get statistics using SQLAlchemy
        total_patrons = Patron.query.filter_by(status='active').count()
        total_books = Book.query.count()
        available_books = Book.query.filter_by(status='available').count()
        issued_books = Book.query.filter_by(status='issued').count()
        overdue_transactions = Transaction.query.filter(
            Transaction.status == 'issued',
            Transaction.due_date < date.today()
        ).count()

        print(f"DEBUG: Dashboard stats - Patrons: {total_patrons}, Books: {total_books}")

        return render_template('dashboard.html',
                             total_patrons=total_patrons,
                             total_books=total_books,
                             available_books=available_books,
                             issued_books=issued_books,
                             overdue_transactions=overdue_transactions,
                             now=dt.now())
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        # Return a simple dashboard if database queries fail
        return render_template('dashboard.html',
                             total_patrons=0,
                             total_books=0,
                             available_books=0,
                             issued_books=0,
                             overdue_transactions=0,
                             now=dt.now())

@core_bp.route('/terms')
def terms_conditions():
    """Terms and conditions page"""
    return render_template('terms_conditions.html')
