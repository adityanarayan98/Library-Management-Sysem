"""
Patron routes for the Library Management System
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, IntegerField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import csv
import io
import os
import json
from app.models import User, Patron, Book, Category, Transaction, LibrarySettings
from app import db
from sqlalchemy import text

patrons_bp = Blueprint('patrons', __name__)

# Form classes
class PatronForm(FlaskForm):
    roll_no = StringField('Roll Number', validators=[DataRequired(), Length(min=2, max=50)])
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[Optional(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    patron_type = SelectField('Patron Type',
                             choices=[('student', 'Student'), ('faculty', 'Faculty'), ('staff', 'Staff')],
                             validators=[DataRequired()])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    max_books = IntegerField('Max Books Allowed', validators=[DataRequired(), NumberRange(min=1, max=10)])
    submit = SubmitField('Add Patron')

@patrons_bp.route('/patrons/<int:patron_id>')
@login_required
def patron_details(patron_id):
    """Show detailed information about a specific patron and their transaction history"""
    # Get patron details using SQLAlchemy
    patron = Patron.query.get(patron_id)

    if not patron:
        flash('Patron not found', 'error')
        return redirect(url_for('patrons.patrons'))

    # Get transaction history for this patron
    transactions = Transaction.query.join(Book).filter(
        Transaction.patron_id == patron_id
    ).order_by(Transaction.created_at.desc()).all()

    # Get current active transactions (issued books)
    current_transactions = Transaction.query.join(Book).filter(
        Transaction.patron_id == patron_id,
        Transaction.status == 'issued'
    ).order_by(Transaction.due_date.asc()).all()

    # Calculate patron statistics
    print(f"DEBUG: Patron {patron.name} has {len(current_transactions)} current transactions")
    overdue_books = 0
    for t in current_transactions:
        print(f"DEBUG: Transaction {t.id}, book: {t.book.title}, due_date: {t.due_date}, type: {type(t.due_date)}, is_overdue: {t.is_overdue()}")
        if t.is_overdue():
            overdue_books += 1
    # Calculate total fines
    total_fines = 0.0
    for t in transactions:
        fine = float(t.fine_amount or 0)
        total_fines += fine
        print(f"DEBUG: Transaction {t.id} fine: {fine}")
    print(f"DEBUG: Total fines: {total_fines}")

    stats = {
        'total_transactions': len(transactions),
        'current_books': len(current_transactions),
        'total_fines': total_fines,
        'overdue_books': overdue_books,
        'completed_returns': sum(1 for t in transactions if t.status == 'returned')
    }

    return render_template('patron_details.html',
                         patron=patron,
                         transactions=transactions,
                         current_transactions=current_transactions,
                         stats=stats)

@patrons_bp.route('/patrons')
@login_required
def patrons():
    """List all patrons with pagination"""
    # Pagination parameters
    try:
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    per_page = 25
    offset = (page - 1) * per_page

    # Get total count for pagination using SQLAlchemy
    total_patrons = Patron.query.count()

    # Get paginated patrons data with issued books count using SQLAlchemy
    patrons_query = Patron.query.outerjoin(
        Transaction, (Patron.id == Transaction.patron_id) & (Transaction.status == 'issued')
    ).group_by(Patron.id).order_by(Patron.name)

    # Apply pagination
    patrons_page = patrons_query.paginate(page=page, per_page=per_page, error_out=False)

    # Create patron objects with issued books count
    patrons = []
    for patron in patrons_page.items:
        # Get issued books count for this patron
        issued_count = Transaction.query.filter_by(
            patron_id=patron.id, status='issued'
        ).count()
        patron.issued_books_count = issued_count
        patrons.append(patron)

    # Calculate pagination info
    total_pages = patrons_page.pages
    has_next = patrons_page.has_next
    has_prev = patrons_page.has_prev

    return render_template('patrons.html',
                         patrons=patrons,
                         page=page,
                         total_pages=total_pages,
                         has_next=has_next,
                         has_prev=has_prev,
                         per_page=per_page)

@patrons_bp.route('/patrons/add', methods=['GET', 'POST'])
@login_required
def add_patron():
    """Add or edit patron"""
    form = PatronForm()

    # Check if this is an edit request from URL parameters
    edit_id = request.args.get('edit')
    is_edit = edit_id is not None

    # Pre-populate form with URL parameters if provided
    if request.args.get('roll_no'):
        form.roll_no.data = request.args.get('roll_no')
    if request.args.get('name'):
        form.name.data = request.args.get('name')
    if request.args.get('type'):
        form.patron_type.data = request.args.get('type')
    if request.args.get('department'):
        form.department.data = request.args.get('department')
    if request.args.get('status'):
        status = request.args.get('status')
    else:
        status = 'active'

    # Handle max_books with proper type conversion
    if request.args.get('max_books'):
        try:
            max_books_str = request.args.get('max_books', '').strip()
            if max_books_str:
                form.max_books.data = int(max_books_str)
            else:
                form.max_books.data = 3  # Default value
        except (ValueError, TypeError):
            form.max_books.data = 3  # Default value
    else:
        form.max_books.data = 3  # Default value

    # Check if roll number already exists
    roll_no_exists = False
    existing_patron_id = None

    with db.engine.connect() as conn:
        if form.roll_no.data:
            existing_patron = conn.execute(text('SELECT id FROM patrons WHERE roll_no = :roll_no'), {'roll_no': form.roll_no.data}).fetchone()
            if existing_patron:
                roll_no_exists = True
                existing_patron_id = existing_patron[0]

    if form.validate_on_submit():
        try:
            # Get status from form submission
            status = request.form.get('status', 'pending')

            # Use default password for all patrons
            default_password = '12345'

            with db.engine.connect() as conn:
                if roll_no_exists and existing_patron_id:
                    # Update existing patron (roll number exists)
                    # Update password to default password
                    conn.execute(text('''
                        UPDATE patrons
                        SET name = :name, patron_type = :patron_type, department = :department, division = :division, status = :status, max_books = :max_books, password_hash = :password_hash, first_login = :first_login, updated_at = CURRENT_TIMESTAMP
                        WHERE roll_no = :roll_no
                    '''), {
                        'name': form.name.data,
                        'patron_type': form.patron_type.data,
                        'department': form.department.data or None,
                        'division': request.form.get('division') or None,
                        'status': status,
                        'max_books': int(form.max_books.data),
                        'password_hash': generate_password_hash(default_password),
                        'first_login': True,
                        'roll_no': form.roll_no.data
                    })
                    flash(f'Patron "{form.roll_no.data}" updated successfully!', 'success')
                else:
                    # Insert new patron (roll number doesn't exist)
                    conn.execute(text('''
                        INSERT INTO patrons (roll_no, name, patron_type, department, division, status, max_books, password_hash, first_login)
                        VALUES (:roll_no, :name, :patron_type, :department, :division, :status, :max_books, :password_hash, :first_login)
                    '''), {
                        'roll_no': form.roll_no.data,
                        'name': form.name.data,
                        'patron_type': form.patron_type.data,
                        'department': form.department.data or None,
                        'division': request.form.get('division') or None,
                        'status': status,
                        'max_books': int(form.max_books.data),
                        'password_hash': generate_password_hash(default_password),
                        'first_login': True
                    })
                    flash(f'Patron "{form.roll_no.data}" created successfully!', 'success')

                conn.commit()
                return redirect(url_for('patrons.patrons'))

        except Exception as e:
            flash(f'Error saving patron: {str(e)}', 'error')

    return render_template('add_patron.html', form=form, is_edit=is_edit)

@patrons_bp.route('/delete_patron/<int:patron_id>', methods=['POST'])
@login_required
def delete_patron(patron_id):
    """Delete a patron and all their transactions"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        return jsonify({'success': False, 'error': 'Access denied. Admin or librarian privileges required.'})

    try:
        with db.engine.connect() as conn:
            # Check if patron exists
            patron = conn.execute(text('SELECT * FROM patrons WHERE id = :patron_id'), {'patron_id': patron_id}).fetchone()
            if not patron:
                return jsonify({'success': False, 'error': 'Patron not found'})

            # Check if patron has active transactions
            active_transactions = conn.execute(text('''
                SELECT COUNT(*) FROM transactions
                WHERE patron_id = :patron_id AND status = 'issued'
            '''), {'patron_id': patron_id}).fetchone()[0]

            if active_transactions > 0:
                return jsonify({
                    'success': False,
                    'error': f'Cannot delete patron with {active_transactions} active transactions. Please return all books first.'
                })

            # Delete all transactions for this patron
            conn.execute(text('DELETE FROM transactions WHERE patron_id = :patron_id'), {'patron_id': patron_id})

            # Delete the patron
            conn.execute(text('DELETE FROM patrons WHERE id = :patron_id'), {'patron_id': patron_id})

            conn.commit()

            return jsonify({
                'success': True,
                'message': f'Patron "{patron[2]}" deleted successfully'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@patrons_bp.route('/bulk_upload_patrons', methods=['GET', 'POST'])
@login_required
def bulk_upload_patrons():
    """Bulk upload patrons from CSV file"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('patrons.patrons'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV file
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.reader(stream)

                # Get headers
                headers = next(csv_input)
                headers = [h.lower().strip() for h in headers]

                # Validate headers
                required_fields = ['roll_no', 'name']
                missing_fields = [field for field in required_fields if field not in headers]
                if missing_fields:
                    flash(f'Missing required fields: {", ".join(missing_fields)}', 'error')
                    return redirect(request.url)

                success_count = 0
                error_count = 0
                errors = []

                for row_num, row in enumerate(csv_input, start=2):  # Start at 2 for header row
                    try:
                        if len(row) < 2:
                            continue

                        # Map CSV columns to database fields
                        roll_no = row[headers.index('roll_no')].strip()
                        name = row[headers.index('name')].strip()

                        if not roll_no or not name:
                            continue

                        # Get optional fields
                        email = None
                        phone = None
                        patron_type = 'student'
                        department = None
                        division = None
                        status = 'active'
                        max_books = 3

                        if 'email' in headers and headers.index('email') < len(row):
                            email = row[headers.index('email')].strip() or None
                        if 'phone' in headers and headers.index('phone') < len(row):
                            phone = row[headers.index('phone')].strip() or None
                        if 'patron_type' in headers and headers.index('patron_type') < len(row):
                            patron_type = row[headers.index('patron_type')].strip() or 'student'
                        if 'department' in headers and headers.index('department') < len(row):
                            department = row[headers.index('department')].strip() or None
                        if 'division' in headers and headers.index('division') < len(row):
                            division = row[headers.index('division')].strip() or None
                        if 'status' in headers and headers.index('status') < len(row):
                            status = row[headers.index('status')].strip() or 'active'
                        if 'max_books' in headers and headers.index('max_books') < len(row):
                            try:
                                max_books = int(row[headers.index('max_books')].strip() or 3)
                            except:
                                max_books = 3

                        # Check if patron already exists
                        existing = Patron.query.filter_by(roll_no=roll_no).first()

                        if existing:
                            # Update existing patron
                            existing.name = name
                            existing.email = email
                            existing.phone = phone
                            existing.patron_type = patron_type
                            existing.department = department
                            existing.division = division
                            existing.status = status
                            existing.max_books = max_books
                            # Set default password for existing patrons too
                            existing.password_hash = generate_password_hash('12345')
                            existing.first_login = True
                            existing.updated_at = datetime.utcnow()
                        else:
                            # Create new patron
                            new_patron = Patron(
                                roll_no=roll_no,
                                name=name,
                                email=email,
                                phone=phone,
                                patron_type=patron_type,
                                department=department,
                                division=division,
                                status=status,
                                max_books=max_books,
                                password_hash=generate_password_hash('12345'),
                                first_login=True
                            )
                            db.session.add(new_patron)

                        success_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f'Row {row_num}: {str(e)}')

                db.session.commit()

                flash(f'Bulk upload completed! {success_count} patrons processed successfully, {error_count} errors occurred.', 'success')
                if errors:
                    flash(f'Errors: {"; ".join(errors[:5])}', 'warning')  # Show first 5 errors

            except Exception as e:
                flash(f'Bulk upload failed: {str(e)}', 'error')

    return render_template('bulk_upload_patrons.html')

@patrons_bp.route('/reset_patron_password/<int:patron_id>', methods=['POST'])
@login_required
def reset_patron_password(patron_id):
    """Reset a patron's password to default"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        return jsonify({'success': False, 'error': 'Access denied. Admin or librarian privileges required.'})

    try:
        patron = Patron.query.get(patron_id)
        if not patron:
            return jsonify({'success': False, 'error': 'Patron not found'})

        # Reset to default password
        patron.reset_to_default_password(current_user.id)
        db.session.commit()

        flash(f'Password for {patron.name} ({patron.roll_no}) has been reset to default.', 'success')
        return jsonify({
            'success': True,
            'message': f'Password reset to default for {patron.name}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@patrons_bp.route('/export_patron_history/<int:patron_id>')
@login_required
def export_patron_history(patron_id):
    """Export transaction history for a specific patron"""
    try:
        with db.engine.connect() as conn:
            # Get patron details for filename
            patron = conn.execute(text('SELECT roll_no, name FROM patrons WHERE id = :patron_id'), {'patron_id': patron_id}).fetchone()
            if not patron:
                flash('Patron not found', 'error')
                return redirect(url_for('patrons.patrons'))

            # Get patron's transaction history
            transactions = conn.execute(text('''
                SELECT
                    t.id,
                    b.accession_number,
                    b.title as book_title,
                    t.issue_date,
                    t.due_date,
                    t.return_date,
                    t.status,
                    t.fine_amount,
                    t.created_at
                FROM transactions t
                JOIN books b ON t.book_id = b.id
                WHERE t.patron_id = :patron_id
                ORDER BY t.created_at DESC
            '''), {'patron_id': patron_id}).fetchall()

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            writer.writerow(['Transaction ID', 'Book Accession No', 'Book Title', 'Issue Date',
                           'Due Date', 'Return Date', 'Status', 'Fine Amount', 'Transaction Date'])

            # Write data
            for transaction in transactions:
                writer.writerow([
                    transaction[0],  # id
                    transaction[1],  # accession_number
                    transaction[2],  # book_title
                    transaction[3] or '',  # issue_date
                    transaction[4] or '',  # due_date
                    transaction[5] or '',  # return_date
                    transaction[6],  # status
                    f'{transaction[7]:.2f}' if transaction[7] else '0.00',  # fine_amount
                    transaction[8]  # created_at
                ])

            # Create response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'patron_{patron[0]}_{patron[1].replace(" ", "_")}_history_{timestamp}.csv'

            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-disposition': f'attachment; filename={filename}'}
            )
            return response

    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('patrons.patron_details', patron_id=patron_id))
