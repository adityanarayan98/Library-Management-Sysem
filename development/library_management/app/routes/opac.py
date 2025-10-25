"""
OPAC (Online Public Access Catalog) routes for the Library Management System
Public access to book catalog - no login required for browsing
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from app.models import User, Patron, Book, Category, Transaction, LibrarySettings
from app import db

opac_bp = Blueprint('opac', __name__)

@opac_bp.route('/opac')
def opac_home():
    """OPAC home page - shows search directly"""
    # Pagination parameters
    try:
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    per_page = 20  # More books per page for public view

    # Search parameters
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')

    # Build query using SQLAlchemy
    books_query = Book.query

    # Apply search filters
    if search:
        books_query = books_query.filter(
            db.or_(
                Book.title.like(f'%{search}%'),
                Book.author.like(f'%{search}%'),
                Book.accession_number.like(f'%{search}%'),
                Book.call_number.like(f'%{search}%'),
                Book.isbn.like(f'%{search}%')
            )
        )

    # Apply category filter
    if category_filter:
        books_query = books_query.join(Category).filter(Category.name == category_filter)

    # Apply status filter (only show available books by default for public)
    if status_filter:
        books_query = books_query.filter(Book.status == status_filter)
    else:
        # Default to available books for public view
        books_query = books_query.filter(Book.status == 'available')

    # Get total count for pagination
    total_books = books_query.count()

    # Apply pagination and ordering
    books_page = books_query.order_by(Book.title).paginate(page=page, per_page=per_page, error_out=False)
    books = books_page.items

    # Get categories for filter dropdown
    categories = Category.query.filter_by(is_active=True).all()

    # Calculate pagination info
    total_pages = books_page.pages
    has_next = books_page.has_next
    has_prev = books_page.has_prev

    return render_template('opac/search.html',
                         books=books,
                         categories=categories,
                         page=page,
                         total_pages=total_pages,
                         has_next=has_next,
                         has_prev=has_prev,
                         per_page=per_page,
                         search=search,
                         category_filter=category_filter,
                         status_filter=status_filter,
                         total_books=total_books)

@opac_bp.route('/opac/search')
def search():
    """Public book search - no login required"""
    # Pagination parameters
    try:
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    per_page = 20  # More books per page for public view

    # Search parameters
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')

    # Build query using SQLAlchemy
    books_query = Book.query

    # Apply search filters
    if search:
        books_query = books_query.filter(
            db.or_(
                Book.title.like(f'%{search}%'),
                Book.author.like(f'%{search}%'),
                Book.accession_number.like(f'%{search}%'),
                Book.call_number.like(f'%{search}%'),
                Book.isbn.like(f'%{search}%')
            )
        )

    # Apply category filter
    if category_filter:
        books_query = books_query.join(Category).filter(Category.name == category_filter)

    # Apply status filter (only show available books by default for public)
    if status_filter:
        books_query = books_query.filter(Book.status == status_filter)
    else:
        # Default to available books for public view
        books_query = books_query.filter(Book.status == 'available')

    # Get total count for pagination
    total_books = books_query.count()

    # Apply pagination and ordering
    books_page = books_query.order_by(Book.title).paginate(page=page, per_page=per_page, error_out=False)
    books = books_page.items

    # Get categories for filter dropdown
    categories = Category.query.filter_by(is_active=True).all()

    # Calculate pagination info
    total_pages = books_page.pages
    has_next = books_page.has_next
    has_prev = books_page.has_prev

    return render_template('opac/search.html',
                         books=books,
                         categories=categories,
                         page=page,
                         total_pages=total_pages,
                         has_next=has_next,
                         has_prev=has_prev,
                         per_page=per_page,
                         search=search,
                         category_filter=category_filter,
                         status_filter=status_filter,
                         total_books=total_books)

@opac_bp.route('/opac/book/<int:book_id>')
def book_details(book_id):
    """Public book details view"""
    # Get book details using SQLAlchemy
    book = Book.query.outerjoin(Category).filter(Book.id == book_id).first()

    if not book:
        flash('Book not found', 'error')
        return redirect(url_for('opac.search'))

    # Get current availability status
    current_transaction = Transaction.query.filter_by(
        book_id=book_id, status='issued'
    ).first()

    # Calculate availability info
    availability_info = {
        'is_available': book.status == 'available',
        'current_patron': current_transaction.patron.name if current_transaction else None,
        'due_date': current_transaction.due_date if current_transaction else None,
        'status': book.status
    }

    # Get library settings
    library_name = LibrarySettings.get_setting('library_name', 'Library')
    librarian_email = LibrarySettings.get_setting('librarian_email', 'library@example.com')

    return render_template('opac/book_details.html',
                         book=book,
                         availability_info=availability_info,
                         library_name=library_name,
                         librarian_email=librarian_email)

@opac_bp.route('/opac/categories')
def categories():
    """Browse books by category"""
    categories = Category.query.filter_by(is_active=True).all()

    category_books = {}
    for category in categories:
        # Get available books count for each category
        available_books = Book.query.filter_by(
            category_id=category.id,
            status='available'
        ).count()
        category_books[category] = available_books

    return render_template('opac/categories.html', category_books=category_books)

@opac_bp.route('/opac/categories/<int:category_id>')
def category_books(category_id):
    """Show books in a specific category"""
    category = Category.query.filter_by(id=category_id, is_active=True).first()

    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('opac.categories'))

    # Pagination parameters
    try:
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    per_page = 20

    # Get books in this category that are available
    books_query = Book.query.filter_by(
        category_id=category_id,
        status='available'
    )

    total_books = books_query.count()
    books_page = books_query.order_by(Book.title).paginate(page=page, per_page=per_page, error_out=False)
    books = books_page.items

    # Calculate pagination info
    total_pages = books_page.pages
    has_next = books_page.has_next
    has_prev = books_page.has_prev

    return render_template('opac/category_books.html',
                         category=category,
                         books=books,
                         page=page,
                         total_pages=total_pages,
                         has_next=has_next,
                         has_prev=has_prev,
                         per_page=per_page,
                         total_books=total_books)
