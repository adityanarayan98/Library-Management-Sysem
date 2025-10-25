#!/usr/bin/env python3
"""
Database table fix script for Library Management System
This script will recreate the database tables with correct names
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

def fix_database_tables():
    """Fix database tables to match model expectations"""

    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///development/data/library.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy
    db = SQLAlchemy(app)

    with app.app_context():
        print("🔧 Fixing database tables...")

        # Drop existing tables that have wrong names
        print("🗑️ Dropping existing tables with incorrect names...")
        try:
            # Drop tables that exist but have wrong names
            db.engine.execute("DROP TABLE IF EXISTS book")
            db.engine.execute("DROP TABLE IF EXISTS patron")
            print("✅ Dropped tables: book, patron")
        except Exception as e:
            print(f"⚠️ Warning dropping tables: {e}")

        # Create all tables with correct names using raw SQL
        print("🏗️ Creating tables with correct names...")

        # Create users table
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(120) NOT NULL UNIQUE,
                password_hash VARCHAR(128) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'librarian',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create category table
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS category (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create patrons table
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS patrons (
                id INTEGER PRIMARY KEY,
                roll_no VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120),
                phone VARCHAR(20),
                patron_type VARCHAR(20) NOT NULL,
                department VARCHAR(100),
                division VARCHAR(100),
                status VARCHAR(20) DEFAULT 'active',
                max_books INTEGER DEFAULT 3,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create books table
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(100) NOT NULL,
                isbn VARCHAR(20) UNIQUE,
                publisher VARCHAR(100),
                publication_year INTEGER,
                accession_number VARCHAR(50) NOT NULL UNIQUE,
                category_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'available',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES category (id)
            )
        """)

        # Create transactions table (plural to match the model)
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                patron_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                issue_date DATE NOT NULL,
                due_date DATE NOT NULL,
                return_date DATE,
                status VARCHAR(20) DEFAULT 'issued',
                fine_amount FLOAT DEFAULT 0.0,
                fine_paid BOOLEAN DEFAULT 0,
                issued_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patron_id) REFERENCES patrons (id),
                FOREIGN KEY (book_id) REFERENCES books (id),
                FOREIGN KEY (issued_by) REFERENCES users (id)
            )
        """)

        # Create library_settings table
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS library_settings (
                id INTEGER PRIMARY KEY,
                setting_key VARCHAR(50) NOT NULL UNIQUE,
                setting_value TEXT NOT NULL,
                description VARCHAR(200),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("✅ All tables created successfully")

        # Verify tables were created correctly
        print("🔍 Verifying table creation...")
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        print(f"📋 Current tables: {existing_tables}")

        # Check if all required tables exist
        required_tables = ['users', 'books', 'patrons', 'category', 'transactions', 'library_settings']
        missing_tables = [table for table in required_tables if table not in existing_tables]

        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print("✅ All required tables exist")

        # Initialize default settings
        print("⚙️ Initializing library settings...")
        try:
            # Default settings
            default_settings = {
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

            for key, value in default_settings.items():
                # Check if setting already exists
                existing = db.engine.execute(
                    "SELECT id FROM library_settings WHERE setting_key = ?",
                    (key,)
                ).fetchone()

                if existing:
                    db.engine.execute(
                        "UPDATE library_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
                        (json.dumps(value) if isinstance(value, (dict, list)) else str(value), key)
                    )
                else:
                    db.engine.execute(
                        "INSERT INTO library_settings (setting_key, setting_value, description) VALUES (?, ?, ?)",
                        (key, json.dumps(value) if isinstance(value, (dict, list)) else str(value), f'Default {key}')
                    )

            print("✅ Default library settings initialized")
        except Exception as e:
            print(f"⚠️ Warning during settings initialization: {e}")

        # Create default librarian user
        print("👤 Creating default librarian user...")
        try:
            # Check if librarian user already exists
            existing_librarian = db.engine.execute(
                "SELECT id FROM users WHERE role = 'librarian'"
            ).fetchone()

            if not existing_librarian:
                # Create default librarian user
                password_hash = generate_password_hash('library123')
                db.engine.execute(
                    "INSERT INTO users (username, email, password_hash, role, is_active) VALUES (?, ?, ?, ?, ?)",
                    ('librarian', 'librarian@library.com', password_hash, 'librarian', True)
                )
                print("✅ Default librarian user created: librarian/library123")
            else:
                print("ℹ️ Librarian user already exists")
        except Exception as e:
            print(f"⚠️ Warning during librarian user creation: {e}")

        print("🎉 Database fix completed successfully!")
        return True

if __name__ == "__main__":
    success = fix_database_tables()
    if success:
        print("\n🚀 Database is now ready for use!")
        print("📝 You can start the application with: python start_server.py")
    else:
        print("\n❌ Database fix failed. Please check the errors above.")
        sys.exit(1)
