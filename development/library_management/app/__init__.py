"""
Enhanced Library Management System
Main application factory
"""

from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os
import sys
from dotenv import load_dotenv
from .db import db

# Load environment variables
load_dotenv()

# Initialize extensions
csrf = CSRFProtect()

def create_app(config_class=None):
    """Application factory function"""
    app = Flask(__name__, template_folder='../templates')

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    app.config['WTF_CSRF_ENABLED'] = False

    # Use database path based on environment (exe vs development)
    if getattr(sys, 'frozen', False):
        # Running as exe - use data folder in current directory
        db_path = os.path.join(os.getcwd(), 'data', 'library.db')
        print(f"Exe environment: Using database at {db_path}")
    else:
        # Development environment - use development/data folder
        basedir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(basedir, 'data', 'library.db')
        print(f"Development environment: Using database at {db_path}")

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Verify connections before use
        'pool_recycle': 300,    # Recycle connections every 5 minutes
    }

    # Initialize extensions with app
    csrf.init_app(app)
    db.init_app(app)

    # Create database tables and default admin user
    with app.app_context():
        try:
            print("Initializing SQLAlchemy database...")

            # Import models - they'll use the Flask app's db instance
            from .models import User, LibrarySettings, Category, Patron, Book, Transaction
            print("Models imported successfully")

            # Now the models are registered with the correct db instance

            # Create all tables (only if they don't exist)
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully")

            # Verify tables were actually created
            print("Verifying table creation...")
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"Existing tables: {existing_tables}")

            # Check for required tables
            required_tables = ['users', 'books', 'patrons', 'category', 'transactions', 'library_settings']
            missing_tables = [table for table in required_tables if table not in existing_tables]

            if missing_tables:
                print(f"⚠️ Warning: Missing tables: {missing_tables}")
                print("🔄 Attempting to create missing tables...")
                # Try creating tables again (in case of timing issues)
                db.create_all()
                # Final check
                existing_tables = inspector.get_table_names()
                still_missing = [table for table in required_tables if table not in existing_tables]
                if still_missing:
                    print(f"❌ Failed to create tables: {still_missing}")
                else:
                    print("All required tables created successfully")
            else:
                print("All required tables exist")

            # Verify tables exist
            print("Verifying table creation...")
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"Existing tables: {existing_tables}")

            # Only proceed if tables were actually created
            if existing_tables:
                # Initialize default settings AFTER tables are created
                print("Initializing library settings...")
                try:
                    LibrarySettings.initialize_defaults()
                    print("Default library settings initialized")
                except Exception as e:
                    print(f" Warning during settings initialization: {e}")
                    print(" Continuing without settings initialization...")

                # Create default admin user if not exists
                print("Checking for admin user...")
                try:
                    admin_exists = User.query.filter_by(role='admin').first()
                    if not admin_exists:
                        print("Creating default admin user...")
                        default_admin = User(
                            username='admin',
                            email='admin@library.com',
                            role='admin',
                            is_active=True
                        )
                        default_admin.set_password('admin123')
                        db.session.add(default_admin)
                        db.session.commit()
                        print("Default admin user created: admin/admin123")
                        print("Login credentials: admin / admin123")
                    else:
                        print("Admin user already exists")

                    # Final verification
                    print("Final verification...")
                    users_count = User.query.count()
                    settings_count = LibrarySettings.query.count()
                    print(f" Users in database: {users_count}")
                    print(f" Settings in database: {settings_count}")

                except Exception as e:
                    print(f" Warning during user creation: {e}")
                    print(" Continuing without admin user creation...")
            else:
                print(" No tables were created - models may not be properly registered")

        except Exception as e:
            print(f"Error during database initialization: {e}")
            print("Attempting to continue with existing database...")
            # Continue even if initialization fails - database might already exist

    # Register blueprints first
    from .routes import core_bp, patrons_bp, books_bp, transactions_bp, backup_bp, settings_bp
    from .auth import auth_bp
    from .routes.opac import opac_bp
    from .routes.patron_auth import patron_auth_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(patrons_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(opac_bp)
    app.register_blueprint(patron_auth_bp)

    # Initialize login manager after blueprints are registered
    from .auth import login_manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'  # Protect against session fixation

    # Custom Jinja2 filters
    def date_filter(date_str):
        """Custom filter to parse date strings into datetime objects"""
        from datetime import datetime
        if not date_str or date_str == '':
            return None
        try:
            return datetime.strptime(str(date_str), '%Y-%m-%d')
        except (ValueError, TypeError):
            return None

    app.jinja_env.filters['date'] = date_filter

    # Context processors to make data available to all templates
    @app.context_processor
    def inject_global_data():
        from .models import LibrarySettings
        from flask import session
        from .models import Patron

        # Library name
        library_name = LibrarySettings.get_setting('library_name', 'Library')

        # Patron session (for OPAC and patron pages)
        patron_session = None
        if 'patron_id' in session:
            try:
                patron_session = Patron.query.get(session['patron_id'])
                # Debug logging
                if patron_session:
                    print(f"DEBUG: Found patron session for {patron_session.name} (ID: {patron_session.id}, Status: {patron_session.status})")
                    # If patron is not active, clear the session
                    if patron_session.status != 'active':
                        print(f"DEBUG: Patron {patron_session.name} is not active (status: {patron_session.status})")
                        # Clear the invalid session
                        session.pop('patron_id', None)
                        session.pop('patron_roll_no', None)
                        session.pop('require_password_change', None)
                        patron_session = None
                else:
                    print(f"DEBUG: No patron found for session ID: {session['patron_id']}")
            except Exception as e:
                print(f"DEBUG: Error getting patron session: {e}")
                patron_session = None

        return {
            'library_name': library_name,
            'patron_session': patron_session
        }

    return app
