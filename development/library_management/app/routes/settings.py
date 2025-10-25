"""
Settings and Reports routes for the Library Management System
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, IntegerField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from datetime import datetime, date, timedelta
import csv
import io
import os
import json
from app.models import User, Patron, Book, Category, Transaction, LibrarySettings
from app import db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Library settings management"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

    if request.method == 'POST':
        try:
            # Get form data
            fine_per_day = float(request.form.get('fine_per_day', 1.0))
            student_due_days = int(request.form.get('student_due_days', 14))
            faculty_due_days = int(request.form.get('faculty_due_days', 30))
            staff_due_days = int(request.form.get('staff_due_days', 21))
            student_max_books = int(request.form.get('student_max_books', 3))
            faculty_max_books = int(request.form.get('faculty_max_books', 5))
            staff_max_books = int(request.form.get('staff_max_books', 4))
            library_name = request.form.get('library_name', 'Library').strip()
            librarian_email = request.form.get('librarian_email', 'library@example.com').strip()

            # Update settings
            LibrarySettings.set_setting('fine_per_day', fine_per_day, 'Fine amount per day for overdue books')
            LibrarySettings.set_setting('student_due_days', student_due_days, 'Maximum days students can keep books')
            LibrarySettings.set_setting('faculty_due_days', faculty_due_days, 'Maximum days faculty can keep books')
            LibrarySettings.set_setting('staff_due_days', staff_due_days, 'Maximum days staff can keep books')
            LibrarySettings.set_setting('student_max_books', student_max_books, 'Maximum books students can borrow')
            LibrarySettings.set_setting('faculty_max_books', faculty_max_books, 'Maximum books faculty can borrow')
            LibrarySettings.set_setting('staff_max_books', staff_max_books, 'Maximum books staff can borrow')
            LibrarySettings.set_setting('library_name', library_name, 'Name of the library')
            LibrarySettings.set_setting('librarian_email', librarian_email, 'Contact email for library administration')

            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings.settings'))

        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'error')

    # GET request - display current settings
    current_settings = {}
    setting_keys = [
        'fine_per_day', 'student_due_days', 'faculty_due_days', 'staff_due_days',
        'student_max_books', 'faculty_max_books', 'staff_max_books',
        'library_name', 'librarian_email'
    ]

    for key in setting_keys:
        current_settings[key] = LibrarySettings.get_setting(key)

    return render_template('settings.html', current_settings=current_settings)

@settings_bp.route('/reports')
@login_required
def reports():
    """Library reports and statistics"""
    # Get statistics using SQLAlchemy
    total_books = Book.query.count()
    available_books = Book.query.filter_by(status='available').count()
    issued_books = Book.query.filter_by(status='issued').count()
    total_patrons = Patron.query.count()
    active_patrons = Patron.query.filter_by(status='active').count()
    overdue_count = Transaction.query.filter(
        Transaction.status == 'issued',
        Transaction.due_date < date.today()
    ).count()

    return render_template('reports.html',
                         total_books=total_books,
                         available_books=available_books,
                         issued_books=issued_books,
                         total_patrons=total_patrons,
                         active_patrons=active_patrons,
                         overdue_count=overdue_count)
