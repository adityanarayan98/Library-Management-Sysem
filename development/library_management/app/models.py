"""
Database models for the Enhanced Library Management System
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json
from .db import db

class User(db.Model, UserMixin):
    """User model for authentication (Admin/Librarian)"""
    __tablename__ = 'users'  # Explicitly set table name to match database.py

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='librarian')  # admin, librarian
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    """Book categories/genres"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    books = db.relationship('Book', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Patron(db.Model):
    """Library patrons (students, faculty, staff)"""
    __tablename__ = 'patrons'  # Explicitly set table name to match code expectations

    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    patron_type = db.Column(db.String(20), nullable=False)  # student, faculty, staff
    department = db.Column(db.String(100))
    division = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, active, inactive, suspended
    password_hash = db.Column(db.String(128))
    first_login = db.Column(db.Boolean, default=True)  # Track if password has been changed
    max_books = db.Column(db.Integer, default=3)
    password_changed_at = db.Column(db.DateTime)  # When password was last changed
    password_changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Who changed the password
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Librarian who approved
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = db.relationship('Transaction', backref='patron', lazy=True)

    def __repr__(self):
        return f'<Patron {self.roll_no}: {self.name}>'

    def books_issued_count(self):
        """Get count of currently issued books"""
        return len([t for t in self.transactions if t.status == 'issued'])

    def can_issue_books(self):
        """Check if patron can issue more books"""
        return self.books_issued_count() < self.max_books and self.status == 'active'

    def set_password(self, password, changed_by_user_id=None):
        """Set patron password"""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
        if changed_by_user_id:
            self.password_changed_by = changed_by_user_id
        if self.first_login:
            self.first_login = False

    def reset_to_default_password(self, changed_by_user_id=None):
        """Reset patron password to default '12345'"""
        self.set_password('12345', changed_by_user_id)
        self.first_login = True  # Force password change on next login

    def check_password(self, password):
        """Check patron password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_active(self):
        """Check if patron is active"""
        return self.status == 'active'



    def approve_patron(self, approved_by_user_id):
        """Approve patron account"""
        self.status = 'active'
        self.approved_by = approved_by_user_id
        self.approved_at = datetime.utcnow()

class Book(db.Model):
    """Library books"""
    __tablename__ = 'books'  # Explicitly set table name to match code expectations

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), index=True)
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    accession_number = db.Column(db.String(50), unique=True, nullable=False)
    call_number = db.Column(db.String(50))  # Library call number (e.g., '669 TAY', '668.9 TAD')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, issued, lost, damaged
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = db.relationship('Transaction', backref='book', lazy=True)

    def __repr__(self):
        return f'<Book {self.accession_number}: {self.title}>'

    def is_available(self):
        return self.status == 'available'

class Transaction(db.Model):
    """Book issue/return transactions"""
    __tablename__ = 'transactions'  # Explicitly set table name to match existing queries
    id = db.Column(db.Integer, primary_key=True)
    patron_id = db.Column(db.Integer, db.ForeignKey('patrons.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='issued')  # issued, returned, overdue
    fine_amount = db.Column(db.Float, default=0.0)
    fine_paid = db.Column(db.Boolean, default=False)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.id}: Book {self.book_id} to Patron {self.patron_id}>'

    def calculate_fine(self):
        """Calculate fine for overdue books"""
        if self.status == 'returned' or self.return_date:
            print(f"DEBUG: Transaction {self.id} is returned or has return_date, fine: 0.0")
            return 0.0

        try:
            # Handle both date objects and string dates
            if isinstance(self.due_date, str):
                due_date = date.fromisoformat(self.due_date)
                print(f"DEBUG: Transaction {self.id} due_date string: {self.due_date}, converted to: {due_date}")
            else:
                due_date = self.due_date
                print(f"DEBUG: Transaction {self.id} due_date object: {due_date}")

            today = date.today()
            print(f"DEBUG: Today: {today}, due_date: {due_date}, today > due_date: {today > due_date}")
            if today > due_date:
                overdue_days = (today - due_date).days
                # Get fine rate from settings with error handling
                try:
                    fine_rate = LibrarySettings.get_setting('fine_per_day', 1.0)
                    fine = overdue_days * fine_rate
                    print(f"DEBUG: Transaction {self.id} overdue by {overdue_days} days, fine: {fine}")
                    return fine
                except Exception as e:
                    print(f"DEBUG: Transaction {self.id} error getting fine rate: {e}")
                    return overdue_days * 1.0
            else:
                print(f"DEBUG: Transaction {self.id} not overdue")
        except (ValueError, TypeError, AttributeError) as e:
            print(f"DEBUG: Transaction {self.id} error in calculate_fine: {e}, due_date: {self.due_date}, type: {type(self.due_date)}")
        return 0.0

    def is_overdue(self):
        """Check if transaction is overdue"""
        if self.status == 'returned' or self.return_date:
            print(f"DEBUG: Transaction {self.id} is returned or has return_date, not overdue")
            return False
        try:
            # Handle both date objects and string dates
            if isinstance(self.due_date, str):
                due_date = date.fromisoformat(self.due_date)
                print(f"DEBUG: Transaction {self.id} due_date string: {self.due_date}, converted to: {due_date}")
            else:
                due_date = self.due_date
                print(f"DEBUG: Transaction {self.id} due_date object: {due_date}")
            today = date.today()
            print(f"DEBUG: Today: {today}, due_date: {due_date}, today > due_date: {today > due_date}")
            return today > due_date
        except (ValueError, TypeError, AttributeError) as e:
            print(f"DEBUG: Transaction {self.id} error in is_overdue: {e}, due_date: {self.due_date}, type: {type(self.due_date)}")
            return False

class LibrarySettings(db.Model):
    """Library configuration settings"""
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_setting(key, default=None):
        """Get setting value by key"""
        try:
            setting = LibrarySettings.query.filter_by(setting_key=key).first()
            if setting:
                try:
                    return json.loads(setting.setting_value)
                except:
                    return setting.setting_value
            return default
        except Exception:
            # Fallback to default if database query fails
            return default

    @staticmethod
    def set_setting(key, value, description=None):
        """Set or update setting"""
        try:
            setting = LibrarySettings.query.filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                if description:
                    setting.description = description
            else:
                new_setting = LibrarySettings(
                    setting_key=key,
                    setting_value=json.dumps(value) if isinstance(value, (dict, list)) else str(value),
                    description=description
                )
                db.session.add(new_setting)
            db.session.commit()
        except Exception as e:
            print(f"Warning: Could not save setting {key}: {e}")
            # Don't raise exception - allow system to continue

    @staticmethod
    def initialize_defaults():
        """Initialize default library settings"""
        defaults = {
            'fine_per_day': 1.0,
            'student_due_days': 14,
            'faculty_due_days': 30,
            'staff_due_days': 21,
            'student_max_books': 3,
            'faculty_max_books': 5,
            'staff_max_books': 4,
            'library_name': 'Library',
            'librarian_email': 'library@example.com'
        }

        for key, value in defaults.items():
            if not LibrarySettings.query.filter_by(setting_key=key).first():
                LibrarySettings.set_setting(key, value, f'Default {key}')

    def __repr__(self):
        return f'<LibrarySettings {self.setting_key}>'
