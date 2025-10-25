"""
Transaction routes for the Library Management System
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
from sqlalchemy import text
from app.models import User, Patron, Book, Category, Transaction, LibrarySettings
from app import db

transactions_bp = Blueprint('transactions', __name__)

# Safe conversion functions
def safe_int(value):
    if value is None or value == '' or str(value).strip() == '' or str(value).strip().lower() == 'none':
        return 0
    try:
        if isinstance(value, str):
            cleaned_value = str(value).strip()
            if cleaned_value == '' or cleaned_value.lower() == 'none':
                return 0
            return int(float(cleaned_value)) if '.' in cleaned_value else int(cleaned_value)
        else:
            return int(float(value)) if value != 0 else 0
    except (ValueError, TypeError, AttributeError):
        return 0

def safe_float(value):
    if value is None or value == '' or str(value).strip() == '' or str(value).strip().lower() == 'none':
        return 0.0
    try:
        if isinstance(value, str):
            cleaned_value = str(value).strip()
            if cleaned_value == '' or cleaned_value.lower() == 'none':
                return 0.0
            return float(cleaned_value)
        else:
            return float(value) if value != 0 else 0.0
    except (ValueError, TypeError, AttributeError):
        return 0.0

# Form classes
class IssueBookForm(FlaskForm):
    patron_roll_no = SelectField('Patron Roll Number', coerce=str, validators=[DataRequired()])
    accession_number = SelectField('Book Accession Number', coerce=str, validators=[DataRequired()])
    submit = SubmitField('Issue Book')

class ReturnBookForm(FlaskForm):
    transaction_id = SelectField('Transaction', coerce=str, validators=[DataRequired()])
    submit = SubmitField('Return Book')

@transactions_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue_book():
    """Issue book to patron"""
    form = IssueBookForm()

    # Populate form choices
    try:
        with db.engine.connect() as conn:
            # Get active patrons for dropdown
            patrons = conn.execute(text('SELECT roll_no, name FROM patrons WHERE status = :status ORDER BY name'), {'status': 'active'}).fetchall()
            form.patron_roll_no.choices = [('', 'Select a patron...')] + [
                (str(p[0]) if p[0] is not None else '', f"{str(p[0]) if p[0] is not None else 'Unknown'} - {str(p[1]) if p[1] is not None else 'Unknown'}")
                for p in patrons if p[0] is not None and p[1] is not None
            ]

            # Get available books for dropdown
            books = conn.execute(text('SELECT accession_number, title FROM books WHERE status = :status ORDER BY title'), {'status': 'available'}).fetchall()
            form.accession_number.choices = [('', 'Select a book...')] + [
                (str(b[0]) if b[0] is not None else '', f"{str(b[0]) if b[0] is not None else 'Unknown'} - {str(b[1]) if b[1] is not None else 'Unknown'}")
                for b in books if b[0] is not None and b[1] is not None
            ]
    except Exception as e:
        flash(f'Error loading form data: {str(e)}', 'error')
        form.patron_roll_no.choices = [('', 'Error loading patrons')]
        form.accession_number.choices = [('', 'Error loading books')]

    if form.validate_on_submit():
        try:
            with db.engine.connect() as conn:
                # Get patron and book details
                patron = conn.execute(text('SELECT * FROM patrons WHERE roll_no = :roll_no AND status = :status'),
                                    {'roll_no': form.patron_roll_no.data, 'status': 'active'}).fetchone()
                book = conn.execute(text('SELECT * FROM books WHERE accession_number = :accession_number AND status = :status'),
                                  {'accession_number': form.accession_number.data, 'status': 'available'}).fetchone()

                if not patron:
                    flash('Patron not found or inactive', 'error')
                elif not book:
                    flash('Book not found or not available', 'error')
                else:
                    # Check if patron can issue more books
                    current_issued = conn.execute(text('''
                        SELECT COUNT(*) FROM transactions
                        WHERE patron_id = :patron_id AND status = 'issued'
                    '''), {'patron_id': patron[0]}).fetchone()[0]

                    # Get patron's max books from settings based on patron type
                    patron_type = patron[5]  # patron_type is at index 5
                    max_books_key = f'{patron_type}_max_books'
                    max_books = LibrarySettings.get_setting(max_books_key, 3)  # Default to 3

                    if current_issued >= max_books:
                        flash(f'Patron has reached maximum limit of {max_books} books', 'error')
                    else:
                        # Get due date based on patron type from settings
                        due_days_key = f'{patron_type}_due_days'
                        due_days = LibrarySettings.get_setting(due_days_key, 14)  # Default to 14

                        due_date = (date.today() + timedelta(days=due_days)).strftime('%Y-%m-%d')

                        # Execute transaction
                        try:
                            # Create transaction
                            conn.execute(text('''
                                INSERT INTO transactions (patron_id, book_id, issue_date, due_date, status, issued_by)
                                VALUES (:patron_id, :book_id, :issue_date, :due_date, :status, :issued_by)
                            '''), {
                                'patron_id': patron[0],
                                'book_id': book[0],
                                'issue_date': date.today().strftime('%Y-%m-%d'),
                                'due_date': due_date,
                                'status': 'issued',
                                'issued_by': current_user.id
                            })

                            # Update book status
                            conn.execute(text('UPDATE books SET status = :status WHERE id = :book_id'), {'status': 'issued', 'book_id': book[0]})

                            # Commit changes
                            conn.commit()

                            flash(f'Book issued successfully! Due date: {due_date}', 'success')
                            return redirect(url_for('transactions.issue_book'))
                        except Exception as e:
                            raise e

        except Exception as e:
            flash(f'Error issuing book: {str(e)}', 'error')

    # Get recent issues for display at bottom of page
    recent_issues = []
    try:
        with db.engine.connect() as conn:
            recent_issues = conn.execute(text('''
                SELECT t.id, p.name as patron_name, p.roll_no, b.title as book_title,
                       b.accession_number, t.issue_date, t.due_date
                FROM transactions t
                JOIN patrons p ON t.patron_id = p.id
                JOIN books b ON t.book_id = b.id
                WHERE t.status = :status
                ORDER BY t.created_at DESC
                LIMIT 10
            '''), {'status': 'issued'}).fetchall()
    except Exception as e:
        # If database error, just pass empty list
        recent_issues = []

    return render_template('issue_book.html', form=form, recent_issues=recent_issues)

@transactions_bp.route('/return', methods=['GET', 'POST'])
@login_required
def return_book():
    """Return book from patron"""
    form = ReturnBookForm()

    # Populate form with active transactions
    try:
        with db.engine.connect() as conn:
            transactions = conn.execute(text('''
                SELECT t.id, p.name, b.title, t.due_date
                FROM transactions t
                JOIN patrons p ON t.patron_id = p.id
                JOIN books b ON t.book_id = b.id
                WHERE t.status = :status
            '''), {'status': 'issued'}).fetchall()

            form.transaction_id.choices = [('', 'Select a transaction...')] + [
                (str(t[0]) if t[0] is not None else '', f"{str(t[1]) if t[1] is not None else 'Unknown'} - {str(t[2]) if t[2] is not None else 'Unknown'} (Due: {str(t[3]) if t[3] is not None else 'Unknown'})")
                for t in transactions if t[0] is not None and t[1] is not None and t[2] is not None and t[3] is not None
            ]
    except Exception as e:
        flash(f'Error loading form data: {str(e)}', 'error')
        form.transaction_id.choices = [('', 'Error loading transactions')]

    if form.validate_on_submit():
        # Check if a valid transaction is selected
        if not form.transaction_id.data or form.transaction_id.data == '':
            flash('Please select a transaction to return.', 'error')
        else:
            try:
                transaction_id = int(form.transaction_id.data)
                with db.engine.connect() as conn:
                    # Get transaction details
                    transaction = conn.execute(text('SELECT * FROM transactions WHERE id = :transaction_id'), {'transaction_id': transaction_id}).fetchone()

                    if transaction:
                        # Calculate fine if overdue using configurable rate
                        today = date.today()
                        try:
                            if isinstance(transaction[4], str):
                                due_date = date.fromisoformat(transaction[4])
                            else:
                                due_date = transaction[4]
                            fine_amount = 0.0

                            if today > due_date:
                                overdue_days = (today - due_date).days
                                # Get fine rate from settings
                                fine_rate = LibrarySettings.get_setting('fine_per_day', 1.0)
                                fine_amount = overdue_days * fine_rate
                        except (ValueError, TypeError, AttributeError):
                            fine_amount = 0.0

                        # Execute transaction
                        try:
                            # Update transaction
                            conn.execute(text('''
                                UPDATE transactions
                                SET return_date = :return_date, status = :status, fine_amount = :fine_amount
                                WHERE id = :transaction_id
                            '''), {
                                'return_date': today.strftime('%Y-%m-%d'),
                                'status': 'returned',
                                'fine_amount': fine_amount,
                                'transaction_id': transaction_id
                            })

                            # Update book status back to available
                            conn.execute(text('UPDATE books SET status = :status WHERE id = :book_id'), {'status': 'available', 'book_id': transaction[2]})

                            # Commit changes
                            conn.commit()

                            flash(f'Book returned successfully! Fine: ₹{fine_amount:.2f}', 'success')
                            return redirect(url_for('transactions.return_book'))
                        except Exception as e:
                            raise e

            except Exception as e:
                flash(f'Error returning book: {str(e)}', 'error')

    return render_template('return_book.html', form=form)

@transactions_bp.route('/collect_fine/<int:transaction_id>', methods=['POST'])
@login_required
def collect_fine(transaction_id):
    """Mark a fine as paid"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        return jsonify({'success': False, 'error': 'Access denied. Admin or librarian privileges required.'})

    try:
        with db.engine.connect() as conn:
            # Get transaction details
            transaction = conn.execute(text('SELECT * FROM transactions WHERE id = :transaction_id'), {'transaction_id': transaction_id}).fetchone()
            if not transaction:
                return jsonify({'success': False, 'error': 'Transaction not found'})

            if transaction[7] == 0:  # fine_amount is at index 7
                return jsonify({'success': False, 'error': 'No fine to collect'})

            if transaction[8]:  # fine_paid is at index 8
                return jsonify({'success': False, 'error': 'Fine already paid'})

            # Mark fine as paid
            conn.execute(text('UPDATE transactions SET fine_paid = 1 WHERE id = :transaction_id'), {'transaction_id': transaction_id})
            conn.commit()

            return jsonify({
                'success': True,
                'message': f'Fine of ₹{transaction[7]:.2f} marked as paid'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@transactions_bp.route('/fines', methods=['GET'])
@login_required
def fines():
    """View all outstanding fines"""
    print(f"DEBUG: Fines route accessed by user: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")
    print(f"DEBUG: Current user role: {current_user.role}")
    print(f"DEBUG: Current user is_admin: {current_user.is_admin()}")

    # More detailed role checking
    user_role = getattr(current_user, 'role', None)
    is_admin_check = getattr(current_user, 'is_admin', lambda: False)()

    print(f"DEBUG: Current user role attribute: {user_role}")
    print(f"DEBUG: Current user is_admin() result: {is_admin_check}")
    print(f"DEBUG: Role check 'admin' in [user_role]: {user_role in ['admin', 'librarian']}")

    # Strict role checking - only admin and librarian can access fines
    auth_check = current_user.is_authenticated
    role_check = user_role == 'admin' or user_role == 'librarian'

    print(f"DEBUG: Auth check: {auth_check}")
    print(f"DEBUG: Role check (strict): {role_check}")
    print(f"DEBUG: User role: '{user_role}'")

    if not auth_check or not role_check:
        print(f"DEBUG: Access denied - Auth: {auth_check}, Role: '{user_role}', Role_Valid: {role_check}")
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

    print("DEBUG: Access granted to admin/librarian user, proceeding to load fines page")

    try:
        with db.engine.connect() as conn:
            # Get ALL outstanding fines (no pagination to avoid errors)
            print("DEBUG: Executing fines query...")
            outstanding_fines = conn.execute(text('''
                SELECT t.*, p.name as patron_name, p.roll_no, b.title as book_title, b.accession_number
                FROM transactions t
                JOIN patrons p ON t.patron_id = p.id
                JOIN books b ON t.book_id = b.id
                WHERE CAST(t.fine_amount AS REAL) > 0 AND t.fine_paid = 0 AND t.status = 'returned'
                ORDER BY CAST(t.fine_amount AS REAL) DESC
            ''')).fetchall()

            print(f"DEBUG: Found {len(outstanding_fines)} outstanding fines")

            # Get summary statistics
            print("DEBUG: Executing statistics query...")
            try:
                stats_result = conn.execute(text('''
                SELECT
                    COUNT(*) as total_outstanding,
                    COALESCE(SUM(CASE WHEN fine_amount IS NULL OR fine_amount = '' THEN 0.0 ELSE CAST(fine_amount AS REAL) END), 0) as total_amount,
                    COALESCE(AVG(CASE WHEN fine_amount IS NULL OR fine_amount = '' THEN 0.0 ELSE CAST(fine_amount AS REAL) END), 0) as avg_fine
                FROM transactions
                WHERE CAST(COALESCE(fine_amount, '0') AS REAL) > 0 AND fine_paid = 0 AND status = 'returned'
            ''')).fetchone()

                print(f"DEBUG: Stats query result: {stats_result}")

                # Handle potential None or empty string values in stats
                if stats_result:
                    total_outstanding = safe_int(stats_result[0])
                    total_amount = safe_float(stats_result[1])
                    avg_fine = safe_float(stats_result[2])

                    # Additional safety check for fine_amount in query results
                    if outstanding_fines:
                        for fine in outstanding_fines:
                            if fine[7] is not None and fine[7] != '':
                                try:
                                    fine[7] = float(fine[7])
                                except (ValueError, TypeError):
                                    fine[7] = 0.0

                    # Ensure we have valid numeric values for template rendering
                    total_outstanding = max(0, total_outstanding)
                    total_amount = max(0.0, total_amount)
                    avg_fine = max(0.0, avg_fine)

                    stats = (total_outstanding, total_amount, avg_fine)
                    print(f"DEBUG: Processed stats: {stats}")
                else:
                    stats = (0, 0.0, 0.0)
                    print("DEBUG: No stats found, using defaults")
            except Exception as e:
                print(f"DEBUG: Error in stats query: {e}")
                stats = (0, 0.0, 0.0)
                print("DEBUG: Using default stats due to query error")

            # Simple template variables (no pagination needed)
            return render_template('fines.html',
                                 outstanding_fines=outstanding_fines,
                                 stats=stats)

    except Exception as e:
        flash(f'Error loading fines: {str(e)}', 'error')
        return redirect(url_for('core.dashboard'))

@transactions_bp.route('/mark_fine_paid/<int:transaction_id>', methods=['POST'])
@login_required
def mark_fine_paid(transaction_id):
    """Mark a specific fine as paid"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('transactions.fines'))

    try:
        with db.engine.connect() as conn:
            # Get transaction details
            transaction = conn.execute(text('SELECT * FROM transactions WHERE id = :transaction_id'), {'transaction_id': transaction_id}).fetchone()
            if not transaction:
                flash('Transaction not found', 'error')
                return redirect(url_for('transactions.fines'))

            if transaction[7] == 0:  # fine_amount is at index 7
                flash('No fine to collect', 'error')
                return redirect(url_for('transactions.fines'))

            if transaction[8]:  # fine_paid is at index 8
                flash('Fine already paid', 'error')
                return redirect(url_for('transactions.fines'))

            # Mark fine as paid
            conn.execute(text('UPDATE transactions SET fine_paid = 1 WHERE id = :transaction_id'), {'transaction_id': transaction_id})
            conn.commit()

            flash(f'Fine of ₹{transaction[7]:.2f} marked as paid successfully!', 'success')

    except Exception as e:
        flash(f'Error marking fine as paid: {str(e)}', 'error')

    return redirect(url_for('transactions.fines'))

@transactions_bp.route('/transaction_logs', methods=['GET'])
@login_required
def transaction_logs():
    """View transaction logs with date range filtering"""
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    transaction_type = request.args.get('type', 'all')  # all, issued, returned
    try:
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    per_page = 25

    # Set default date range if not provided (last 30 days)
    if not start_date:
        from datetime import datetime, timedelta
        end_date_default = datetime.now().date()
        start_date_default = end_date_default - timedelta(days=30)
        start_date = start_date_default.strftime('%Y-%m-%d')
        end_date = end_date_default.strftime('%Y-%m-%d')

    offset = (page - 1) * per_page

    try:
        with db.engine.connect() as conn:
            # Build query based on filters
            query = text('''
                SELECT t.*, p.name as patron_name, p.roll_no, b.title as book_title, b.accession_number
                FROM transactions t
                JOIN patrons p ON t.patron_id = p.id
                JOIN books b ON t.book_id = b.id
                WHERE strftime('%Y-%m-%d', t.created_at) BETWEEN :start_date AND :end_date
            ''')
            params = {'start_date': start_date, 'end_date': end_date}

            if transaction_type == 'issued':
                query = text(str(query) + ' AND t.status = :status')
                params['status'] = 'issued'
            elif transaction_type == 'returned':
                query = text(str(query) + ' AND t.status = :status')
                params['status'] = 'returned'

            query = text(str(query) + ' ORDER BY t.created_at DESC LIMIT :per_page OFFSET :offset')
            params['per_page'] = per_page
            params['offset'] = offset

            # Get filtered transactions
            transactions = conn.execute(query, params).fetchall()

            # Get total count for pagination
            count_query = text('''
                SELECT COUNT(*)
                FROM transactions t
                WHERE strftime('%Y-%m-%d', t.created_at) BETWEEN :start_date AND :end_date
            ''')
            count_params = {'start_date': start_date, 'end_date': end_date}

            if transaction_type == 'issued':
                count_query = text(str(count_query) + ' AND t.status = :status')
                count_params['status'] = 'issued'
            elif transaction_type == 'returned':
                count_query = text(str(count_query) + ' AND t.status = :status')
                count_params['status'] = 'returned'

            count_result = conn.execute(count_query, count_params).fetchone()
            total_transactions = count_result[0] if count_result else 0

            # Calculate pagination info
            total_pages = (total_transactions + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1

            # Get summary statistics for the filtered period
            stats = {
                'total_issues': 0,
                'total_returns': 0,
                'total_fines': 0.0,
                'overdue_returns': 0
            }

            if transaction_type == 'all' or transaction_type == 'issued':
                issues_result = conn.execute(text('''
                    SELECT COUNT(*) FROM transactions
                    WHERE strftime('%Y-%m-%d', created_at) BETWEEN :start_date AND :end_date AND status = 'issued'
                '''), {'start_date': start_date, 'end_date': end_date}).fetchone()
                stats['total_issues'] = issues_result[0] if issues_result else 0

            if transaction_type == 'all' or transaction_type == 'returned':
                returns_result = conn.execute(text('''
                    SELECT COUNT(*) FROM transactions
                    WHERE strftime('%Y-%m-%d', created_at) BETWEEN :start_date AND :end_date AND status = 'returned'
                '''), {'start_date': start_date, 'end_date': end_date}).fetchone()
                stats['total_returns'] = returns_result[0] if returns_result else 0

                # Get fine statistics for returned books
                fine_stats = conn.execute(text('''
                    SELECT SUM(fine_amount), COUNT(*) FROM transactions
                    WHERE strftime('%Y-%m-%d', created_at) BETWEEN :start_date AND :end_date AND status = 'returned' AND fine_amount > 0
                '''), {'start_date': start_date, 'end_date': end_date}).fetchone()
                stats['total_fines'] = safe_float(fine_stats[0])
                stats['overdue_returns'] = safe_int(fine_stats[1])

            return render_template('transaction_logs.html',
                                 transactions=transactions,
                                 start_date=start_date,
                                 end_date=end_date,
                                 transaction_type=transaction_type,
                                 page=page,
                                 total_pages=total_pages,
                                 has_next=has_next,
                                 has_prev=has_prev,
                                 per_page=per_page,
                                 stats=stats)

    except Exception as e:
        # Check if it's a database-related error (likely no tables or no data)
        error_msg = str(e).lower()
        if 'no such table' in error_msg or 'no column named' in error_msg or 'no filter named' in error_msg:
            # Database not initialized or tables don't exist
            return render_template('transaction_logs.html',
                                 transactions=[],
                                 start_date=start_date,
                                 end_date=end_date,
                                 transaction_type=transaction_type,
                                 page=1,
                                 total_pages=0,
                                 has_next=False,
                                 has_prev=False,
                                 per_page=25,
                                 stats={'total_issues': 0, 'total_returns': 0, 'total_fines': 0.0, 'overdue_returns': 0},
                                 setup_mode=True)
        else:
            # Other database errors
            flash(f'Error loading transaction logs: {str(e)}', 'error')
            return redirect(url_for('core.dashboard'))

@transactions_bp.route('/export_transaction_logs')
@login_required
def export_transaction_logs():
    """Export transaction logs for a specific date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    transaction_type = request.args.get('type', 'all')

    # Set default date range if not provided (last 30 days)
    if not start_date:
        from datetime import datetime, timedelta
        end_date_default = datetime.now().date()
        start_date_default = end_date_default - timedelta(days=30)
        start_date = start_date_default.strftime('%Y-%m-%d')
        end_date = end_date_default.strftime('%Y-%m-%d')

    try:
        with db.engine.connect() as conn:
            # Build query for export
            query = text('''
                SELECT
                    t.id,
                    p.roll_no,
                    p.name as patron_name,
                    b.accession_number,
                    b.title as book_title,
                    t.issue_date,
                    t.due_date,
                    t.return_date,
                    t.status,
                    t.fine_amount,
                    t.created_at
                FROM transactions t
                JOIN patrons p ON t.patron_id = p.id
                JOIN books b ON t.book_id = b.id
                WHERE strftime('%Y-%m-%d', t.created_at) BETWEEN :start_date AND :end_date
            ''')
            params = {'start_date': start_date, 'end_date': end_date}

            if transaction_type == 'issued':
                query = text(str(query) + ' AND t.status = :status')
                params['status'] = 'issued'
            elif transaction_type == 'returned':
                query = text(str(query) + ' AND t.status = :status')
                params['status'] = 'returned'

            query = text(str(query) + ' ORDER BY t.created_at DESC')

            transactions = conn.execute(query, params).fetchall()

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            writer.writerow(['Transaction ID', 'Patron Roll No', 'Patron Name', 'Book Accession No',
                           'Book Title', 'Issue Date', 'Due Date', 'Return Date', 'Status',
                           'Fine Amount', 'Transaction Date'])

            # Write data
            for transaction in transactions:
                writer.writerow([
                    transaction[0],  # id
                    transaction[1],  # roll_no
                    transaction[2],  # patron_name
                    transaction[3],  # accession_number
                    transaction[4],  # book_title
                    transaction[5] or '',  # issue_date
                    transaction[6] or '',  # due_date
                    transaction[7] or '',  # return_date
                    transaction[8],  # status
                    f'{transaction[9]:.2f}' if transaction[9] else '0.00',  # fine_amount
                    transaction[10]  # created_at
                ])

            # Create response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filter_text = f'_{transaction_type}' if transaction_type != 'all' else ''
            filename = f'transaction_logs_{start_date}_to_{end_date}{filter_text}_{timestamp}.csv'

            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-disposition': f'attachment; filename={filename}'}
            )
            return response

    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('transactions.transaction_logs', start_date=start_date, end_date=end_date, type=transaction_type))
