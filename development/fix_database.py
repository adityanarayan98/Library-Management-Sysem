#!/usr/bin/env python3
"""
Database initialization script for the Library Management System
This script creates the database with proper SQLAlchemy schema
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the library_management directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'library_management'))

try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from app.models import db, User, LibrarySettings

    def create_database():
        """Create the database with proper SQLAlchemy schema"""

        # Create Flask app context
        app = Flask(__name__)

        # Configure database path
        db_path = os.path.join(os.getcwd(), 'development', 'library_management', 'app', 'instance', 'library.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'your-secret-key-change-this'

        # Initialize database
        db.init_app(app)

        with app.app_context():
            print("🔧 Creating database tables...")

            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")

            # Initialize default settings
            print("⚙️ Initializing library settings...")
            LibrarySettings.initialize_defaults()
            print("✅ Default library settings initialized")

            # Create default admin user
            print("👤 Checking for admin user...")
            admin_exists = User.query.filter_by(role='admin').first()
            if not admin_exists:
                print("🔧 Creating default admin user...")
                default_admin = User(
                    username='admin',
                    email='admin@library.com',
                    role='admin',
                    is_active=True
                )
                default_admin.set_password('admin123')
                db.session.add(default_admin)
                db.session.commit()
                print("✅ Default admin user created: admin/admin123")
                print("🔐 Login credentials: admin / admin123")
            else:
                print("ℹ️  Admin user already exists")

            # Create the Rasmi user as mentioned in auth.py
            print("👤 Checking for Rasmi user...")
            rasmi_exists = User.query.filter_by(username='Rasmi').first()
            if not rasmi_exists:
                print("🔧 Creating Rasmi user...")
                rasmi_user = User(
                    username='Rasmi',
                    email='rasmi@iitgn.ac.in',
                    role='librarian',
                    is_active=True
                )
                rasmi_user.set_password('Admin@159')
                db.session.add(rasmi_user)
                db.session.commit()
                print("✅ Rasmi user created: Rasmi/Admin@159")
                print("🔐 Login credentials: Rasmi / Admin@159")
            else:
                print("ℹ️  Rasmi user already exists")

            # Final verification
            print("🔍 Final verification...")
            users_count = User.query.count()
            settings_count = LibrarySettings.query.count()
            print(f"📊 Users in database: {users_count}")
            print(f"📊 Settings in database: {settings_count}")

            print("✅ Database initialization completed successfully!")
            return True

    if __name__ == "__main__":
        success = create_database()
        if success:
            print("\n🎉 Database is ready! You can now start the application.")
        else:
            print("\n❌ Database initialization failed!")
            sys.exit(1)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure all dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during database initialization: {e}")
    sys.exit(1)
