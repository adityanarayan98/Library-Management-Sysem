"""
Backup and Import routes for the Library Management System
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

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/backup', methods=['GET', 'POST'])
@login_required
def backup_data():
    """Create system backups"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

    # Get backup files information
    backup_files = []
    total_size = 0
    csv_count = 0

    # Use single backup location
    backup_dirs = ['backups']

    for backup_dir in backup_dirs:
        if os.path.exists(backup_dir):
            try:
                for filename in os.listdir(backup_dir):
                    if filename.endswith('.csv') or filename.endswith('.json'):
                        file_path = os.path.join(backup_dir, filename)
                        try:
                            file_stat = os.stat(file_path)
                            is_csv = filename.endswith('.csv')
                            if is_csv:
                                csv_count += 1

                            backup_files.append({
                                'name': filename,
                                'path': file_path,
                                'size': file_stat.st_size,
                                'modified': file_stat.st_mtime,
                                'modified_formatted': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                                'modified_date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d'),
                                'type': filename.split('_')[0] if '_' in filename else 'unknown'
                            })
                            total_size += file_stat.st_size
                        except OSError as e:
                            print(f"Error accessing file {file_path}: {e}")
                            continue
            except OSError as e:
                print(f"Error accessing backup directory {backup_dir}: {e}")
                continue

    if request.method == 'POST':
        backup_type = request.form.get('backup_type', 'csv')

        try:
            with db.engine.connect() as conn:
                # Create backup directory
                backup_dir = 'backups'
                os.makedirs(backup_dir, exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                if backup_type == 'csv':
                    # Create COMPLETE SYSTEM BACKUP with coordinated 4-file set

                    # 1. Export categories FIRST (needed for books)
                    categories = conn.execute(text('SELECT * FROM category')).fetchall()
                    if categories:
                        with open(f'{backup_dir}/system_backup_categories_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['id', 'name', 'description', 'is_active', 'created_at'])
                            writer.writerows(categories)

                    # 2. Export patrons SECOND (needed for transactions)
                    patrons = conn.execute(text('SELECT * FROM patrons')).fetchall()
                    if patrons:
                        with open(f'{backup_dir}/system_backup_patrons_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['id', 'roll_no', 'name', 'email', 'phone', 'patron_type', 'department', 'division', 'status', 'max_books', 'created_at', 'updated_at'])
                            writer.writerows(patrons)

                    # 3. Export books THIRD (depends on categories)
                    books = conn.execute(text('SELECT * FROM books')).fetchall()
                    if books:
                        with open(f'{backup_dir}/system_backup_books_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['id', 'title', 'author', 'isbn', 'publisher', 'publication_year', 'accession_number', 'category_id', 'status', 'created_at', 'updated_at'])
                            writer.writerows(books)

                    # 4. Export transactions LAST (depends on patrons and books)
                    transactions = conn.execute(text('SELECT * FROM transactions')).fetchall()
                    if transactions:
                        with open(f'{backup_dir}/system_backup_transactions_{timestamp}.csv', 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['id', 'patron_id', 'book_id', 'issue_date', 'due_date', 'return_date', 'status', 'fine_amount', 'fine_paid', 'issued_by', 'created_at', 'updated_at'])
                            writer.writerows(transactions)

                    # 5. Create backup manifest file (metadata and instructions)
                    manifest_data = {
                        'backup_type': 'complete_system_backup',
                        'timestamp': timestamp,
                        'version': '1.0',
                        'total_files': 4,
                        'files': [
                            {
                                'filename': f'system_backup_categories_{timestamp}.csv',
                                'type': 'categories',
                                'description': 'Book categories - import FIRST',
                                'record_count': len(categories) if categories else 0,
                                'import_order': 1,
                                'dependencies': []
                            },
                            {
                                'filename': f'system_backup_patrons_{timestamp}.csv',
                                'type': 'patrons',
                                'description': 'Library patrons - import SECOND',
                                'record_count': len(patrons) if patrons else 0,
                                'import_order': 2,
                                'dependencies': ['categories']
                            },
                            {
                                'filename': f'system_backup_books_{timestamp}.csv',
                                'type': 'books',
                                'description': 'Book collection - import THIRD',
                                'record_count': len(books) if books else 0,
                                'import_order': 3,
                                'dependencies': ['categories']
                            },
                            {
                                'filename': f'system_backup_transactions_{timestamp}.csv',
                                'type': 'transactions',
                                'description': 'Transaction history - import FOURTH',
                                'record_count': len(transactions) if transactions else 0,
                                'import_order': 4,
                                'dependencies': ['patrons', 'books']
                            }
                        ],
                        'restore_instructions': [
                            '1. Import categories first (creates foundation)',
                            '2. Import patrons second (needs categories for reference)',
                            '3. Import books third (needs categories for reference)',
                            '4. Import transactions last (needs patrons and books)',
                            '5. System will be fully restored and ready for use'
                        ],
                        'backup_summary': {
                            'total_categories': len(categories) if categories else 0,
                            'total_patrons': len(patrons) if patrons else 0,
                            'total_books': len(books) if books else 0,
                            'total_transactions': len(transactions) if transactions else 0
                        }
                    }

                    with open(f'{backup_dir}/system_backup_manifest_{timestamp}.json', 'w', encoding='utf-8') as f:
                        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

                    flash(f'COMPLETE SYSTEM BACKUP created successfully! 4 coordinated files + manifest saved in {backup_dir}/', 'success')
                    flash(f'📋 Import Order: 1) Categories → 2) Patrons → 3) Books → 4) Transactions', 'info')

                elif backup_type == 'json':
                    # Create JSON backup using proper SQLAlchemy approach

                    # Get table data and convert to dictionaries with safe type conversion
                    patrons_result = conn.execute(text('SELECT * FROM patrons'))
                    patrons_columns = list(patrons_result.keys())
                    patrons_data = [dict(zip(patrons_columns, [str(val) if val is not None else None for val in row])) for row in patrons_result.fetchall()]

                    books_result = conn.execute(text('SELECT * FROM books'))
                    books_columns = list(books_result.keys())
                    books_data = [dict(zip(books_columns, [str(val) if val is not None else None for val in row])) for row in books_result.fetchall()]

                    transactions_result = conn.execute(text('SELECT * FROM transactions'))
                    transactions_columns = list(transactions_result.keys())
                    transactions_data = [dict(zip(transactions_columns, [str(val) if val is not None else None for val in row])) for row in transactions_result.fetchall()]

                    categories_result = conn.execute(text('SELECT * FROM category'))
                    categories_columns = list(categories_result.keys())
                    categories_data = [dict(zip(categories_columns, [str(val) if val is not None else None for val in row])) for row in categories_result.fetchall()]

                    data = {
                        'patrons': patrons_data,
                        'books': books_data,
                        'transactions': transactions_data,
                        'categories': categories_data,
                        'backup_date': datetime.now().isoformat()
                    }

                    with open(f'{backup_dir}/library_backup_{timestamp}.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    flash(f'JSON backup completed successfully! File saved in {backup_dir}/', 'success')

        except Exception as e:
            flash(f'Backup failed: {str(e)}', 'error')

    return render_template('backup.html', backup_files=backup_files, total_size=total_size, csv_count=csv_count)

@backup_bp.route('/export/reports')
@login_required
def export_reports():
    """Export comprehensive library reports"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('settings.reports'))

    try:
        with db.engine.connect() as conn:
            # Get all report statistics
            total_books = conn.execute(text('SELECT COUNT(*) FROM books')).fetchone()[0]
            available_books = conn.execute(text('SELECT COUNT(*) FROM books WHERE status = ?'), ('available',)).fetchone()[0]
            issued_books = conn.execute(text('SELECT COUNT(*) FROM books WHERE status = ?'), ('issued',)).fetchone()[0]
            total_patrons = conn.execute(text('SELECT COUNT(*) FROM patrons')).fetchone()[0]
            active_patrons = conn.execute(text('SELECT COUNT(*) FROM patrons WHERE status = ?'), ('active',)).fetchone()[0]
            overdue_count = conn.execute(text('''
                SELECT COUNT(*) FROM transactions
                WHERE status = ? AND due_date < ?
            '''), ('issued', date.today().strftime('%Y-%m-%d'))).fetchone()[0]

            # Get library settings
            library_name = LibrarySettings.get_setting('library_name', 'Library')
            librarian_email = LibrarySettings.get_setting('librarian_email', 'library@example.com')

            # Create comprehensive report data
            report_data = [
                ['Library Reports Summary'],
                ['Generated On', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Library Name', library_name],
                ['Contact Email', librarian_email],
                [''],
                ['BOOK STATISTICS'],
                ['Total Books', total_books],
                ['Available Books', available_books],
                ['Issued Books', issued_books],
                ['Overdue Books', overdue_count],
                [''],
                ['PATRON STATISTICS'],
                ['Total Patrons', total_patrons],
                ['Active Patrons', active_patrons],
                [''],
                ['CATEGORY BREAKDOWN']
            ]

            # Add category breakdown
            categories = conn.execute(text('''
                SELECT c.name, COUNT(b.id) as book_count
                FROM category c
                LEFT JOIN books b ON c.id = b.category_id
                WHERE c.is_active = 1
                GROUP BY c.id, c.name
                ORDER BY book_count DESC
            ''')).fetchall()

            for category in categories:
                report_data.append([category[0], category[1]])

            # Add recent transactions summary
            report_data.extend([
                [''],
                ['RECENT ACTIVITY'],
                ['Recent Issues (Last 7 days)', ''],
                ['Recent Returns (Last 7 days)', '']
            ])

            # Get recent activity
            seven_days_ago = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
            recent_issues = conn.execute(text('''
                SELECT COUNT(*) FROM transactions
                WHERE issue_date >= ? AND status = 'issued'
            '''), (seven_days_ago,)).fetchone()[0]

            recent_returns = conn.execute(text('''
                SELECT COUNT(*) FROM transactions
                WHERE return_date >= ? AND status = 'returned'
            '''), (seven_days_ago,)).fetchone()[0]

            report_data[-2].append(recent_issues)  # Add to recent issues row
            report_data[-1].append(recent_returns)  # Add to recent returns row

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)

            # Write report data
            for row in report_data:
                writer.writerow(row)

            # Create response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'library_reports_{timestamp}.csv'

            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-disposition': f'attachment; filename={filename}'}
            )
            return response

    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('settings.reports'))

@backup_bp.route('/export/<table_name>')
@login_required
def export_table(table_name):
    """Export specific table data"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

    try:
        with db.engine.connect() as conn:
            # Validate table name
            valid_tables = ['patrons', 'books', 'transactions', 'categories']
            if table_name not in valid_tables:
                flash('Invalid table name', 'error')
                return redirect(url_for('core.dashboard'))

            # Get table data using text() for proper SQLAlchemy handling
            query = text(f'SELECT * FROM {table_name}')
            result = conn.execute(query)
            rows = result.fetchall()

            # Get column names using the proper method for SQLAlchemy result
            columns = list(result.keys())

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)

            # Create response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{table_name}_export_{timestamp}.csv'

            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-disposition': f'attachment; filename={filename}'}
            )
            return response

    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('core.dashboard'))

@backup_bp.route('/restore/<table_name>', methods=['GET', 'POST'])
@login_required
def restore_table(table_name):
    """Restore specific table from backup file"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

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

                success_count = 0
                error_count = 0

                if table_name == 'patrons':
                    for row in csv_input:
                        try:
                            if len(row) < 10:
                                continue

                            # Check if patron already exists
                            existing = Patron.query.filter_by(id=row[0]).first() if row[0] else None

                            if existing:
                                # Update existing patron
                                existing.roll_no = row[1]
                                existing.name = row[2]
                                existing.email = row[3] if len(row) > 3 else None
                                existing.phone = row[4] if len(row) > 4 else None
                                existing.patron_type = row[5] if len(row) > 5 else 'student'
                                existing.department = row[6] if len(row) > 6 else None
                                existing.division = row[7] if len(row) > 7 else None
                                existing.status = row[8] if len(row) > 8 else 'active'
                                existing.max_books = int(row[9]) if len(row) > 9 and row[9] else 3
                                existing.updated_at = datetime.utcnow()
                            else:
                                # Create new patron
                                new_patron = Patron(
                                    roll_no=row[1],
                                    name=row[2],
                                    email=row[3] if len(row) > 3 else None,
                                    phone=row[4] if len(row) > 4 else None,
                                    patron_type=row[5] if len(row) > 5 else 'student',
                                    department=row[6] if len(row) > 6 else None,
                                    division=row[7] if len(row) > 7 else None,
                                    status=row[8] if len(row) > 8 else 'active',
                                    max_books=int(row[9]) if len(row) > 9 and row[9] else 3
                                )
                                db.session.add(new_patron)
                            success_count += 1

                        except Exception as e:
                            error_count += 1

                elif table_name == 'books':
                    for row in csv_input:
                        try:
                            if len(row) < 9:
                                continue

                            # Check if book already exists
                            existing = Book.query.filter_by(id=row[0]).first() if row[0] else None

                            if existing:
                                # Update existing book
                                existing.title = row[1]
                                existing.author = row[2]
                                existing.isbn = row[3] if len(row) > 3 else None
                                existing.publisher = row[4] if len(row) > 4 else None
                                existing.publication_year = int(row[5]) if len(row) > 5 and row[5] else None
                                existing.accession_number = row[6]
                                existing.category_id = int(row[7]) if len(row) > 7 and row[7] else 1
                                existing.status = row[8] if len(row) > 8 else 'available'
                                existing.updated_at = datetime.utcnow()
                            else:
                                # Create new book
                                new_book = Book(
                                    title=row[1],
                                    author=row[2],
                                    isbn=row[3] if len(row) > 3 else None,
                                    publisher=row[4] if len(row) > 4 else None,
                                    publication_year=int(row[5]) if len(row) > 5 and row[5] else None,
                                    accession_number=row[6],
                                    category_id=int(row[7]) if len(row) > 7 and row[7] else 1,
                                    status=row[8] if len(row) > 8 else 'available'
                                )
                                db.session.add(new_book)
                            success_count += 1

                        except Exception as e:
                            error_count += 1

                elif table_name == 'categories':
                    for row in csv_input:
                        try:
                            if len(row) < 3:
                                continue

                            # Check if category already exists
                            existing = Category.query.filter_by(id=row[0]).first() if row[0] else None

                            if existing:
                                # Update existing category
                                existing.name = row[1]
                                existing.description = row[2] if len(row) > 2 else None
                                existing.is_active = bool(row[3]) if len(row) > 3 else True
                            else:
                                # Create new category
                                new_category = Category(
                                    name=row[1],
                                    description=row[2] if len(row) > 2 else None,
                                    is_active=bool(row[3]) if len(row) > 3 else True
                                )
                                db.session.add(new_category)
                            success_count += 1

                        except Exception as e:
                            error_count += 1

                db.session.commit()

                flash(f'Restore completed! {success_count} records restored, {error_count} errors.', 'success')

            except Exception as e:
                flash(f'Restore failed: {str(e)}', 'error')

    return render_template('restore_table.html', table_name=table_name)

@backup_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_data():
    """Basic import functionality"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

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

                # Detect file type based on headers
                headers = next(csv_input)

                if 'roll_no' in headers and 'name' in headers:
                    # Import patrons
                    for row in csv_input:
                        if len(row) >= 4:  # At least roll_no, name, email, phone
                            # Check if patron already exists
                            existing = Patron.query.filter_by(roll_no=row[0]).first()

                            if not existing:
                                # Create new patron
                                new_patron = Patron(
                                    roll_no=row[0],
                                    name=row[1],
                                    email=row[2] if len(row) > 2 else None,
                                    phone=row[3] if len(row) > 3 else None,
                                    patron_type='student',
                                    status='active',
                                    max_books=3
                                )
                                db.session.add(new_patron)

                elif 'title' in headers and 'author' in headers:
                    # Import books
                    for row in csv_input:
                        if len(row) >= 3:  # At least title, author, accession_number
                            # Check if book already exists
                            existing = Book.query.filter_by(accession_number=row[4] if len(row) > 4 else row[0]).first()

                            if not existing:
                                # Create new book
                                new_book = Book(
                                    title=row[0],
                                    author=row[1],
                                    isbn=row[2] if len(row) > 2 else None,
                                    publisher=row[3] if len(row) > 3 else None,
                                    accession_number=row[4] if len(row) > 4 else row[0],
                                    category_id=1,
                                    status='available'
                                )
                                db.session.add(new_book)

                db.session.commit()
                flash('Data imported successfully!', 'success')

            except Exception as e:
                flash(f'Import failed: {str(e)}', 'error')

    return render_template('import.html')

@backup_bp.route('/complete_restore', methods=['GET', 'POST'])
@login_required
def complete_restore():
    """Complete system restoration using 4 coordinated backup files"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

    restore_results = None
    validation_errors = []
    manifest_data = None

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'validate_manifest' and 'manifest_file' in request.files:
            # Step 1: Validate manifest file
            manifest_file = request.files['manifest_file']
            if manifest_file and manifest_file.filename.endswith('.json'):
                try:
                    manifest_content = json.loads(manifest_file.read().decode('utf-8'))
                    manifest_data = validate_backup_manifest(manifest_content)

                    if manifest_data['valid']:
                        flash(f'Manifest validated! Found {manifest_data["total_files"]} backup files ready for restoration.', 'success')
                    else:
                        validation_errors = manifest_data['errors']
                        flash('Manifest validation failed. Please check the errors below.', 'error')

                except Exception as e:
                    flash(f'Error reading manifest file: {str(e)}', 'error')

        elif action == 'restore' and manifest_data:
            try:
                # Step 2: Perform complete restoration
                restore_results = perform_complete_restore(manifest_data)

                if restore_results['success']:
                    flash(f'COMPLETE SYSTEM RESTORED! {restore_results["total_restored"]} records restored successfully.', 'success')
                    flash(f'📋 Categories: {restore_results["categories"]} | Patrons: {restore_results["patrons"]} | Books: {restore_results["books"]} | Transactions: {restore_results["transactions"]}', 'info')
                    manifest_data = None  # Clear after successful restore
                else:
                    flash(f'Restoration failed: {restore_results["error"]}', 'error')

            except Exception as e:
                flash(f'Restoration error: {str(e)}', 'error')

    return render_template('complete_restore.html',
                         restore_results=restore_results,
                         validation_errors=validation_errors,
                         manifest_data=manifest_data,
                         backup_summary=manifest_data.get('backup_summary') if manifest_data else None)

@backup_bp.route('/enhanced_import', methods=['GET', 'POST'])
@login_required
def enhanced_import():
    """Enhanced import with validation and one-by-one processing"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('core.dashboard'))

    import_results = None
    validation_errors = []
    preview_data = []
    validated_data = []  # Store all validated data for import

    if request.method == 'POST':
        # Handle import type selection
        import_type = request.form.get('import_type', '')
        action = request.form.get('action', '')

        if action == 'validate' and 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith('.csv'):
                try:
                    # Read and validate CSV file
                    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                    csv_input = csv.reader(stream)

                    headers = next(csv_input)
                    headers = [h.lower().strip() for h in headers]

                    validation_result = validate_import_file(import_type, headers, csv_input)

                    if validation_result['valid']:
                        preview_data = validation_result['preview']
                        validated_data = validation_result.get('all_validated_data', preview_data)  # Use all data if available
                        total_records = validation_result['total_rows']
                        flash(f'File validation successful! {total_records} records ready for import.', 'success')
                    else:
                        validation_errors = validation_result['errors']
                        flash('File validation failed. Please check the errors below.', 'error')

                except Exception as e:
                    flash(f'Error reading file: {str(e)}', 'error')

        elif action == 'import' and preview_data:
            try:
                # Use all validated data for import, not just preview
                import_data = validated_data if validated_data else preview_data
                import_results = process_import(import_type, import_data)
                if import_results['success']:
                    total_imported = import_results["imported"]
                    flash(f'Import completed successfully! {total_imported} records imported.', 'success')
                    preview_data = []  # Clear preview after successful import
                    validated_data = []  # Clear validated data
                else:
                    flash(f'Import failed: {import_results["error"]}', 'error')
            except Exception as e:
                flash(f'Import error: {str(e)}', 'error')

    # Get available categories for books import using SQLAlchemy
    categories = Category.query.filter_by(is_active=True).all()

    # Get available patrons and books for transaction import validation using SQLAlchemy
    patrons_for_import = Patron.query.filter_by(status='active').all()
    books_for_import = Book.query.filter_by(status='available').all()

    return render_template('enhanced_import.html',
                         import_results=import_results,
                         validation_errors=validation_errors,
                         preview_data=preview_data,
                         categories=categories,
                         patrons_for_import=patrons_for_import,
                         books_for_import=books_for_import)

@backup_bp.route('/delete_backup', methods=['POST'])
@login_required
def delete_backup():
    """Delete a backup file"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        return jsonify({'success': False, 'error': 'Access denied. Admin or librarian privileges required.'})

    try:
        file_path = request.form.get('file_path')
        if not file_path:
            return jsonify({'success': False, 'error': 'File path not provided'})

        # Security check - only allow deletion from backups directory
        if not file_path.startswith('development/backups/'):
            return jsonify({'success': False, 'error': 'Invalid file path'})

        # Check if file exists
        import os
        full_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': 'File not found'})

        # Delete the file
        os.remove(full_path)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Helper functions for backup and import operations

def validate_backup_manifest(manifest_content):
    """Validate the backup manifest file"""
    errors = []

    # Check required fields
    required_fields = ['backup_type', 'timestamp', 'version', 'total_files', 'files', 'restore_instructions']
    for field in required_fields:
        if field not in manifest_content:
            errors.append(f"Missing required field: {field}")

    if errors:
        return {'valid': False, 'errors': errors}

    # Validate file structure
    if manifest_content.get('total_files') != 4:
        errors.append("Manifest must contain exactly 4 files for complete restoration")

    # Check file types
    expected_types = ['categories', 'patrons', 'books', 'transactions']
    actual_types = [file.get('type') for file in manifest_content.get('files', [])]

    for expected_type in expected_types:
        if expected_type not in actual_types:
            errors.append(f"Missing file type: {expected_type}")

    # Validate import order
    for file_info in manifest_content.get('files', []):
        if 'import_order' not in file_info:
            errors.append(f"Missing import_order for file: {file_info.get('filename', 'unknown')}")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'total_files': manifest_content.get('total_files', 0),
        'files': manifest_content.get('files', []),
        'instructions': manifest_content.get('restore_instructions', [])
    }

def perform_complete_restore(manifest_data):
    """Perform complete system restoration using manifest"""
    try:
        with db.engine.connect() as conn:
            total_restored = 0
            results = {
                'categories': 0,
                'patrons': 0,
                'books': 0,
                'transactions': 0
            }

            # Get files in correct import order
            sorted_files = sorted(manifest_data['files'], key=lambda x: x['import_order'])

            for file_info in sorted_files:
                filename = file_info['filename']
                file_type = file_info['type']

                # Construct full file path
                file_path = os.path.join('backups', filename)

                if not os.path.exists(file_path):
                    return {
                        'success': False,
                        'error': f'Required backup file not found: {filename}',
                        'total_restored': total_restored
                    }

                # Import each file
                if file_type == 'categories':
                    results['categories'] = import_categories_file(conn, file_path)
                    total_restored += results['categories']

                elif file_type == 'patrons':
                    results['patrons'] = import_patrons_file(conn, file_path)
                    total_restored += results['patrons']

                elif file_type == 'books':
                    results['books'] = import_books_file(conn, file_path)
                    total_restored += results['books']

                elif file_type == 'transactions':
                    results['transactions'] = import_transactions_file(conn, file_path)
                    total_restored += results['transactions']

            conn.commit()

            return {
                'success': True,
                'total_restored': total_restored,
                **results
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'total_restored': 0,
            **results
        }

def import_categories_file(conn, file_path):
    """Import categories from backup file"""
    imported = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)

            for row in csv_reader:
                if len(row) >= 3:
                    conn.execute(text('''
                        INSERT OR REPLACE INTO categories (id, name, description, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    '''), (row[0] if row[0] else None, row[1], row[2] if len(row) > 2 else None,
                          row[3] if len(row) > 3 else 1, row[4] if len(row) > 4 else None))
                    imported += 1
    except Exception as e:
        print(f"Error importing categories: {e}")
    return imported

def import_patrons_file(conn, file_path):
    """Import patrons from backup file"""
    imported = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)

            for row in csv_reader:
                if len(row) >= 4:  # At least id, roll_no, name, patron_type
                    conn.execute(text('''
                        INSERT OR REPLACE INTO patrons
                        (id, roll_no, name, email, phone, patron_type, department, division, status, max_books, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''), (row[0] if row[0] else None, row[1], row[2], row[3] if len(row) > 3 else None,
                          row[4] if len(row) > 4 else None, row[5] if len(row) > 5 else 'student',
                          row[6] if len(row) > 6 else None, row[7] if len(row) > 7 else None,
                          row[8] if len(row) > 8 else 'active', row[9] if len(row) > 9 else 3,
                          row[10] if len(row) > 10 else None, row[11] if len(row) > 11 else None))
                    imported += 1
    except Exception as e:
        print(f"Error importing patrons: {e}")
    return imported

def import_books_file(conn, file_path):
    """Import books from backup file"""
    imported = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)

            for row in csv_reader:
                if len(row) >= 4:  # At least id, title, author, accession_number
                    conn.execute(text('''
                        INSERT OR REPLACE INTO books
                        (id, title, author, isbn, publisher, publication_year, accession_number, category_id, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''), (row[0] if row[0] else None, row[1], row[2], row[3] if len(row) > 3 else None,
                          row[4] if len(row) > 4 else None, row[5] if len(row) > 5 else None,
                          row[6], row[7] if len(row) > 7 else 1, row[8] if len(row) > 8 else 'available',
                          row[9] if len(row) > 9 else None, row[10] if len(row) > 10 else None))
                    imported += 1
    except Exception as e:
        print(f"Error importing books: {e}")
    return imported

def import_transactions_file(conn, file_path):
    """Import transactions from backup file"""
    imported = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)

            for row in csv_reader:
                if len(row) >= 4:  # At least id, patron_id, book_id, issue_date
                    conn.execute(text('''
                        INSERT OR REPLACE INTO transactions
                        (id, patron_id, book_id, issue_date, due_date, return_date, status, fine_amount, fine_paid, issued_by, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''), (row[0] if row[0] else None, row[1], row[2], row[3], row[4] if len(row) > 4 else None,
                          row[5] if len(row) > 5 else None, row[6] if len(row) > 6 else 'issued',
                          row[7] if len(row) > 7 else 0.0, row[8] if len(row) > 8 else 0,
                          row[9] if len(row) > 9 else 1, row[10] if len(row) > 10 else None,
                          row[11] if len(row) > 11 else None))
                    imported += 1
    except Exception as e:
        print(f"Error importing transactions: {e}")
    return imported

def validate_import_file(import_type, headers, csv_reader):
    """Validate CSV file structure and data"""
    errors = []
    preview = []
    all_validated_data = []  # Store all validated data for import
    rows = list(csv_reader)  # Convert to list to allow multiple iterations

    if import_type == 'patrons':
        # Validate patrons CSV structure
        required_fields = ['roll_no', 'name']
        optional_fields = ['email', 'phone', 'patron_type', 'department', 'division', 'status', 'max_books']

        missing_required = [field for field in required_fields if field not in headers]
        if missing_required:
            errors.append(f"Missing required fields: {', '.join(missing_required)}")

        # Validate first 10 rows for preview, but check all rows for errors and collect all valid data
        preview_rows = min(10, len(rows))  # Show up to 10 rows in preview

        for i, row in enumerate(rows):
            if len(row) < 2:
                errors.append(f"Row {i+2}: Insufficient data")
                continue

            try:
                roll_no = row[headers.index('roll_no')].strip()
                name = row[headers.index('name')].strip()

                if not roll_no or not name:
                    errors.append(f"Row {i+2}: Roll number and name are required")

                # Check email format if provided
                if 'email' in headers and headers.index('email') < len(row):
                    email = row[headers.index('email')].strip()
                    if email and '@' not in email:
                        errors.append(f"Row {i+2}: Invalid email format")

                # Create validated data record for all valid rows
                if roll_no and name:  # Only add if required fields are present
                    validated_record = {
                        'row': i+2,
                        'roll_no': roll_no,
                        'name': name,
                        'email': row[headers.index('email')].strip() if 'email' in headers and headers.index('email') < len(row) else '',
                        'phone': row[headers.index('phone')].strip() if 'phone' in headers and headers.index('phone') < len(row) else ''
                    }
                    all_validated_data.append(validated_record)

                    # Add to preview only for first 10 rows
                    if i < preview_rows:
                        preview.append(validated_record)
            except (ValueError, IndexError) as e:
                errors.append(f"Row {i+2}: Data format error - {str(e)}")

    elif import_type == 'books':
        # Validate books CSV structure
        required_fields = ['title', 'author', 'accession_number']
        optional_fields = ['isbn', 'publisher', 'publication_year', 'category']

        missing_required = [field for field in required_fields if field not in headers]
        if missing_required:
            errors.append(f"Missing required fields: {', '.join(missing_required)}")

        # Validate first 10 rows for preview, but check all rows for errors and collect all valid data
        preview_rows = min(10, len(rows))

        for i, row in enumerate(rows):
            if len(row) < 3:
                errors.append(f"Row {i+2}: Insufficient data")
                continue

            try:
                title = row[headers.index('title')].strip()
                author = row[headers.index('author')].strip()
                accession_number = row[headers.index('accession_number')].strip()

                if not title or not author or not accession_number:
                    errors.append(f"Row {i+2}: Title, author, and accession number are required")

                # Validate publication year if provided
                if 'publication_year' in headers and headers.index('publication_year') < len(row):
                    pub_year = row[headers.index('publication_year')].strip()
                    if pub_year and (not pub_year.isdigit() or len(pub_year) != 4):
                        errors.append(f"Row {i+2}: Publication year must be a 4-digit number")

                # Create validated data record for all valid rows
                if title and author and accession_number:  # Only add if required fields are present
                    validated_record = {
                        'row': i+2,
                        'title': title,
                        'author': author,
                        'accession_number': accession_number,
                        'isbn': row[headers.index('isbn')].strip() if 'isbn' in headers and headers.index('isbn') < len(row) else ''
                    }
                    all_validated_data.append(validated_record)

                    # Add to preview only for first 10 rows
                    if i < preview_rows:
                        preview.append(validated_record)
            except (ValueError, IndexError) as e:
                errors.append(f"Row {i+2}: Data format error - {str(e)}")

    elif import_type == 'transactions':
        # Validate transactions CSV structure
        required_fields = ['patron_id', 'book_id', 'issue_date', 'due_date']
        optional_fields = ['return_date', 'status', 'fine_amount']

        missing_required = [field for field in required_fields if field not in headers]
        if missing_required:
            errors.append(f"Missing required fields: {', '.join(missing_required)}")

        # Validate first 10 rows for preview, but check all rows for errors and collect all valid data
        preview_rows = min(10, len(rows))

        for i, row in enumerate(rows):
            if len(row) < 4:
                errors.append(f"Row {i+2}: Insufficient data")
                continue

            try:
                patron_id = row[headers.index('patron_id')].strip()
                book_id = row[headers.index('book_id')].strip()
                issue_date = row[headers.index('issue_date')].strip()
                due_date = row[headers.index('due_date')].strip()

                if not all([patron_id, book_id, issue_date, due_date]):
                    errors.append(f"Row {i+2}: All required fields must have values")

                # Validate date formats
                try:
                    from datetime import datetime
                    datetime.strptime(issue_date, '%Y-%m-%d')
                    datetime.strptime(due_date, '%Y-%m-%d')
                except ValueError:
                    errors.append(f"Row {i+2}: Invalid date format (use YYYY-MM-DD)")

                # Validate patron_id and book_id exist (if data is available)
                if patron_id and book_id:
                    try:
                        patron_id_int = int(patron_id)
                        book_id_int = int(book_id)
                        if patron_id_int <= 0 or book_id_int <= 0:
                            errors.append(f"Row {i+2}: Patron ID and Book ID must be positive numbers")
                    except ValueError:
                        errors.append(f"Row {i+2}: Patron ID and Book ID must be valid numbers")

                # Create validated data record for all valid rows
                if patron_id and book_id and issue_date and due_date:  # Only add if required fields are present
                    validated_record = {
                        'row': i+2,
                        'patron_id': patron_id,
                        'book_id': book_id,
                        'issue_date': issue_date,
                        'due_date': due_date
                    }
                    all_validated_data.append(validated_record)

                    # Add to preview only for first 10 rows
                    if i < preview_rows:
                        preview.append(validated_record)
            except (ValueError, IndexError) as e:
                errors.append(f"Row {i+2}: Data format error - {str(e)}")

    elif import_type == 'categories':
        # Validate categories CSV structure
        required_fields = ['name']
        optional_fields = ['description', 'is_active']

        missing_required = [field for field in required_fields if field not in headers]
        if missing_required:
            errors.append(f"Missing required fields: {', '.join(missing_required)}")

        # Validate first 10 rows for preview, but check all rows for errors and collect all valid data
        preview_rows = min(10, len(rows))

        for i, row in enumerate(rows):
            if len(row) < 1:
                errors.append(f"Row {i+2}: Insufficient data")
                continue

            try:
                name = row[headers.index('name')].strip()

                if not name:
                    errors.append(f"Row {i+2}: Category name is required")

                # Create validated data record for all valid rows
                if name:  # Only add if required field is present
                    validated_record = {
                        'row': i+2,
                        'name': name,
                        'description': row[headers.index('description')].strip() if 'description' in headers and headers.index('description') < len(row) else ''
                    }
                    all_validated_data.append(validated_record)

                    # Add to preview only for first 10 rows
                    if i < preview_rows:
                        preview.append(validated_record)
            except (ValueError, IndexError) as e:
                errors.append(f"Row {i+2}: Data format error - {str(e)}")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'preview': preview,
        'all_validated_data': all_validated_data,  # Return all validated data for import
        'total_rows': len(rows)
    }

def process_import(import_type, preview_data):
    """Process the actual import after validation"""
    try:
        imported = 0
        errors = []

        if import_type == 'patrons':
            for item in preview_data:
                try:
                    # Check if patron exists using SQLAlchemy
                    existing = Patron.query.filter_by(roll_no=item['roll_no']).first()

                    if existing:
                        # Update existing patron
                        existing.name = item['name']
                        existing.email = item['email'] or None
                        existing.phone = item['phone'] or None
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new patron
                        new_patron = Patron(
                            roll_no=item['roll_no'],
                            name=item['name'],
                            email=item['email'] or None,
                            phone=item['phone'] or None,
                            patron_type='student',
                            status='active',
                            max_books=3
                        )
                        db.session.add(new_patron)

                    imported += 1
                except Exception as e:
                    errors.append(f"Error importing patron {item['roll_no']}: {str(e)}")

        elif import_type == 'books':
            for item in preview_data:
                try:
                    # Check if book exists using SQLAlchemy
                    existing = Book.query.filter_by(accession_number=item['accession_number']).first()

                    if existing:
                        # Update existing book
                        existing.title = item['title']
                        existing.author = item['author']
                        existing.isbn = item['isbn'] or None
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new book
                        new_book = Book(
                            title=item['title'],
                            author=item['author'],
                            isbn=item['isbn'] or None,
                            accession_number=item['accession_number'],
                            category_id=1,  # Default category
                            status='available'
                        )
                        db.session.add(new_book)

                    imported += 1
                except Exception as e:
                    errors.append(f"Error importing book {item['accession_number']}: {str(e)}")

        elif import_type == 'transactions':
            for item in preview_data:
                try:
                    # Check if transaction already exists using SQLAlchemy
                    existing = Transaction.query.filter_by(
                        patron_id=item['patron_id'],
                        book_id=item['book_id'],
                        issue_date=item['issue_date']
                    ).first()

                    if not existing:
                        # Create new transaction
                        new_transaction = Transaction(
                            patron_id=item['patron_id'],
                            book_id=item['book_id'],
                            issue_date=item['issue_date'],
                            due_date=item['due_date'],
                            status='issued'
                        )
                        db.session.add(new_transaction)
                        imported += 1
                    else:
                        errors.append(f"Transaction already exists for patron {item['patron_id']}, book {item['book_id']} on {item['issue_date']}")
                except Exception as e:
                    errors.append(f"Error importing transaction: {str(e)}")

        elif import_type == 'categories':
            for item in preview_data:
                try:
                    # Check if category exists using SQLAlchemy
                    existing = Category.query.filter_by(name=item['name']).first()

                    if not existing:
                        # Create new category
                        new_category = Category(
                            name=item['name'],
                            description=item['description'] or None,
                            is_active=True
                        )
                        db.session.add(new_category)
                        imported += 1
                    else:
                        errors.append(f"Category '{item['name']}' already exists")
                except Exception as e:
                    errors.append(f"Error importing category {item['name']}: {str(e)}")

        db.session.commit()

        return {
            'success': True,
            'imported': imported,
            'errors': errors,
            'total_processed': len(preview_data)
        }

    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e),
            'imported': 0,
            'errors': []
        }
