"""
Book routes for the Library Management System
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
from sqlalchemy.exc import IntegrityError
from app.models import User, Patron, Book, Category, Transaction, LibrarySettings
from app import db

books_bp = Blueprint('books', __name__)

# Form classes
class BookForm(FlaskForm):
    title = StringField('Book Title', validators=[DataRequired(), Length(min=1, max=200)])
    author = StringField('Author', validators=[DataRequired(), Length(min=1, max=100)])
    isbn = StringField('ISBN', validators=[Optional(), Length(max=20)])
    publisher = StringField('Publisher', validators=[Optional(), Length(max=100)])
    publication_year = IntegerField('Publication Year', validators=[Optional(), NumberRange(min=1000, max=2030)])
    accession_number = StringField('Accession Number', validators=[DataRequired(), Length(min=1, max=50)])
    category = StringField('Category', validators=[DataRequired(), Length(min=1, max=100)])
    submit = SubmitField('Add Book')

@books_bp.route('/books')
@login_required
def books():
    """List all books with pagination and search"""
    # Pagination parameters
    try:
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    per_page = 25

    # Search parameters
    search = request.args.get('search', '')

    # Build query using SQLAlchemy
    books_query = Book.query
    if search:
        books_query = books_query.filter(
            db.or_(
                Book.title.like(f'%{search}%'),
                Book.author.like(f'%{search}%'),
                Book.accession_number.like(f'%{search}%'),
                Book.isbn.like(f'%{search}%')
            )
        )

    # Get total count for pagination
    total_books = books_query.count()

    # Apply pagination and ordering
    books_page = books_query.order_by(Book.title).paginate(page=page, per_page=per_page, error_out=False)
    books = books_page.items

    # Get categories using SQLAlchemy
    categories = Category.query.filter_by(is_active=True).all()

    # Calculate pagination info
    total_pages = books_page.pages
    has_next = books_page.has_next
    has_prev = books_page.has_prev

    return render_template('books.html',
                         books=books,
                         categories=categories,
                         page=page,
                         total_pages=total_pages,
                         has_next=has_next,
                         has_prev=has_prev,
                         per_page=per_page,
                         search=search,
                         total_books=total_books)

@books_bp.route('/api/categories')
@login_required
def api_categories():
    """API endpoint to get categories for autocomplete"""
    try:
        # Get search term if provided
        search = request.args.get('q', '').strip()

        # Query categories using SQLAlchemy
        categories_query = Category.query.filter_by(is_active=True)

        if search:
            # Filter by search term (case-insensitive)
            categories_query = categories_query.filter(
                Category.name.like(f'%{search}%')
            )

        # Get categories ordered by name
        categories = categories_query.order_by(Category.name).all()

        # Return as JSON
        categories_list = [{'id': cat.id, 'name': cat.name, 'description': cat.description}
                          for cat in categories]

        return jsonify(categories_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@books_bp.route('/books/<int:book_id>')
@login_required
def book_details(book_id):
    """Show detailed information about a specific book"""
    # Get book details using SQLAlchemy
    book = Book.query.outerjoin(Category).filter(Book.id == book_id).first()

    if not book:
        flash('Book not found', 'error')
        return redirect(url_for('books.books'))

    # Get transaction history for this book
    transactions = Transaction.query.join(Patron).filter(
        Transaction.book_id == book_id
    ).order_by(Transaction.created_at.desc()).all()

    # Get current transaction (if book is issued)
    current_transaction = Transaction.query.filter_by(
        book_id=book_id, status='issued'
    ).first()

    return render_template('book_details.html',
                         book=book,
                         transactions=transactions,
                         current_transaction=current_transaction,
                         today_date=date.today())

@books_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
def add_book():
    """Add or edit book"""
    form = BookForm()

    # Check if this is an edit request from URL parameters
    edit_accession = request.args.get('accession_number')
    is_edit = edit_accession is not None

    # Pre-populate form with URL parameters if provided
    if request.args.get('title'):
        form.title.data = request.args.get('title')
    if request.args.get('author'):
        form.author.data = request.args.get('author')
    if request.args.get('isbn'):
        form.isbn.data = request.args.get('isbn')
    if request.args.get('publisher'):
        form.publisher.data = request.args.get('publisher')
    if request.args.get('publication_year'):
        try:
            publication_year_str = request.args.get('publication_year', '').strip()
            if publication_year_str:
                form.publication_year.data = int(publication_year_str)
            else:
                form.publication_year.data = None
        except (ValueError, TypeError):
            form.publication_year.data = None
    if request.args.get('accession_number'):
        form.accession_number.data = request.args.get('accession_number')
    if request.args.get('status'):
        status = request.args.get('status')
    else:
        status = 'available'
    if request.args.get('call_number'):
        call_number = request.args.get('call_number')
    else:
        call_number = ''

    # Check for existing accession number
    existing_book = None
    if form.accession_number.data:
        existing_book = Book.query.filter_by(accession_number=form.accession_number.data).first()

    # If editing, get the existing book data to pre-populate category
    if is_edit and existing_book:
        # Get category name for the category field using SQLAlchemy
        if existing_book.category_id:
            category_obj = Category.query.filter_by(id=existing_book.category_id, is_active=True).first()
            if category_obj:
                # We'll set this via URL parameter in the template
                pass

    if form.validate_on_submit():
        try:
            # Get category name from form
            category_name = form.category.data.strip() if form.category.data else ''
            if not category_name:
                flash('Category is required', 'error')
                return redirect(request.url)

            # Get status from form submission, default to 'available'
            status = request.form.get('status', 'available')

            # Find or create category using SQLAlchemy
            category = Category.query.filter_by(name=category_name, is_active=True).first()
            if category:
                category_id = category.id
            else:
                # Create new category
                new_category = Category(name=category_name, is_active=True)
                db.session.add(new_category)
                db.session.flush()  # Get the ID without committing
                category_id = new_category.id

            # Check if accession_number already exists (for both edit and new book scenarios)
            existing_accession_book = None
            if form.accession_number.data:
                existing_accession_book = Book.query.filter_by(accession_number=form.accession_number.data).first()

            if existing_accession_book:
                # Update existing book with matching accession number
                existing_accession_book.title = form.title.data
                existing_accession_book.author = form.author.data
                existing_accession_book.isbn = form.isbn.data or None
                existing_accession_book.publisher = form.publisher.data or None
                existing_accession_book.publication_year = form.publication_year.data
                existing_accession_book.call_number = request.form.get('call_number', '').strip() or None
                existing_accession_book.category_id = category_id
                existing_accession_book.status = status
                existing_accession_book.updated_at = datetime.utcnow()

                db.session.commit()
                flash(f'Book with accession number "{form.accession_number.data}" updated successfully!', 'success')
            else:
                # Insert new book only if accession number doesn't exist
                new_book = Book(
                    title=form.title.data,
                    author=form.author.data,
                    isbn=form.isbn.data or None,
                    publisher=form.publisher.data or None,
                    publication_year=form.publication_year.data,
                    accession_number=form.accession_number.data,
                    call_number=request.form.get('call_number', '').strip() or None,
                    category_id=category_id,
                    status=status
                )
                db.session.add(new_book)
                db.session.commit()
                flash('Book added successfully!', 'success')

            return redirect(url_for('books.books'))

        except (ValueError, TypeError) as e:
            flash(f'Error saving book: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error saving book: {str(e)}', 'error')

    return render_template('add_book.html', form=form, is_edit=is_edit)

@books_bp.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    """Delete a book and all its transactions"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        return jsonify({'success': False, 'error': 'Access denied. Admin or librarian privileges required.'})

    try:
        # Check if book exists using SQLAlchemy
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'success': False, 'error': 'Book not found'})

        # Check if book is currently issued
        active_transactions = Transaction.query.filter_by(book_id=book_id, status='issued').count()

        if active_transactions > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete book that is currently issued. Please return the book first.'
            })

        # Delete all transactions for this book using SQLAlchemy
        Transaction.query.filter_by(book_id=book_id).delete()

        # Delete the book using SQLAlchemy
        db.session.delete(book)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Book "{book.title}" deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@books_bp.route('/bulk_upload_books', methods=['GET', 'POST'])
@login_required
def bulk_upload_books():
    """Bulk upload books from CSV file"""
    if not current_user.is_authenticated or current_user.role not in ['admin', 'librarian']:
        flash('Access denied. Admin or librarian privileges required.', 'error')
        return redirect(url_for('books.books'))

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

                # Validate headers - expect exact order: title, author, accession_number, isbn, publisher, publication_year, category
                expected_headers = ['title', 'author', 'accession_number', 'isbn', 'publisher', 'publication_year', 'category']
                if headers != expected_headers:
                    flash(f'Invalid CSV format. Expected columns in order: {", ".join(expected_headers)}', 'error')
                    flash(f'Found columns: {", ".join(headers)}', 'error')
                    return redirect(request.url)

                success_count = 0
                error_count = 0
                errors = []
                warnings = []

                # Get default category
                default_category = Category.query.filter_by(is_active=True).order_by(Category.id).first()
                default_category_id = default_category.id if default_category else 1

                for row_num, row in enumerate(csv_input, start=2):  # Start at 2 for header row
                    # Process each row individually with its own transaction
                    row_success = False

                    try:
                        if len(row) < 3:
                            error_count += 1
                            errors.append(f'Row {row_num}: Insufficient data (need at least 3 columns)')
                            continue

                        # Map CSV columns to database fields in exact order
                        title = row[0].strip() if len(row) > 0 else ''
                        author = row[1].strip() if len(row) > 1 else ''
                        accession_number = row[2].strip() if len(row) > 2 else ''

                        # Validate required fields
                        if not title:
                            error_count += 1
                            errors.append(f'Row {row_num}: Title is required')
                            continue
                        if not author:
                            error_count += 1
                            errors.append(f'Row {row_num}: Author is required')
                            continue
                        if not accession_number:
                            error_count += 1
                            errors.append(f'Row {row_num}: Accession number is required')
                            continue

                        # Get optional fields
                        isbn = row[3].strip() if len(row) > 3 else None
                        publisher = row[4].strip() if len(row) > 4 else None
                        publication_year = None
                        if len(row) > 5 and row[5].strip():
                            try:
                                publication_year = int(row[5].strip())
                            except ValueError:
                                warnings.append(f'Row {row_num}: Invalid publication year, using None')
                        category_id = default_category_id

                        # Handle category
                        if len(row) > 6 and row[6].strip():
                            category_name = row[6].strip()
                            # Find or create category
                            category = Category.query.filter_by(name=category_name, is_active=True).first()
                            if category:
                                category_id = category.id
                            else:
                                # Create new category
                                new_category = Category(name=category_name, is_active=True)
                                db.session.add(new_category)
                                db.session.flush()  # Get the ID
                                category_id = new_category.id

                        # Check if book already exists by accession number
                        existing = Book.query.filter_by(accession_number=accession_number).first()

                        if existing:
                            # Update existing book
                            existing.title = title
                            existing.author = author
                            existing.isbn = isbn
                            existing.publisher = publisher
                            existing.publication_year = publication_year
                            existing.category_id = category_id
                            existing.updated_at = datetime.utcnow()
                            warnings.append(f'Row {row_num}: Updated existing book "{accession_number}"')
                            row_success = True
                        else:
                            # Create new book - this is where IntegrityError can occur
                            new_book = Book(
                                title=title,
                                author=author,
                                isbn=isbn,
                                publisher=publisher,
                                publication_year=publication_year,
                                accession_number=accession_number,
                                category_id=category_id,
                                status='available'
                            )
                            db.session.add(new_book)
                            row_success = True

                        # Commit this individual row
                        if row_success:
                            db.session.commit()
                            success_count += 1

                    except IntegrityError as e:
                        # Handle database constraint violations (duplicate ISBN, accession number, etc.)
                        db.session.rollback()  # Rollback this specific row's transaction
                        error_count += 1
                        # Provide specific error message based on the constraint violation
                        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                        if 'isbn' in error_msg.lower():
                            errors.append(f'Row {row_num}: Duplicate ISBN "{isbn}" - book with this ISBN already exists')
                        elif 'accession_number' in error_msg.lower():
                            errors.append(f'Row {row_num}: Duplicate accession number "{accession_number}" - book with this accession number already exists')
                        else:
                            errors.append(f'Row {row_num}: Database constraint violation - {error_msg}')
                    except Exception as e:
                        # Handle other types of errors
                        db.session.rollback()  # Rollback this specific row's transaction
                        error_count += 1
                        errors.append(f'Row {row_num}: {str(e)}')

                # Provide comprehensive feedback
                if success_count > 0:
                    flash(f'Bulk upload completed! {success_count} books processed successfully, {error_count} errors.', 'success')
                else:
                    flash(f'Bulk upload completed with {error_count} errors and no successful uploads.', 'warning')

                if warnings:
                    flash(f'Warnings: {"; ".join(warnings[:3])}', 'warning')  # Show first 3 warnings
                if errors:
                    flash(f'Errors: {"; ".join(errors[:3])}', 'danger')  # Show first 3 errors

            except Exception as e:
                flash(f'Bulk upload failed: {str(e)}', 'error')

    return render_template('bulk_upload_books.html')
