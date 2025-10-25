#!/usr/bin/env python3
"""
Simple database fix script using only sqlite3
"""

import sqlite3
import json
import os
from werkzeug.security import generate_password_hash

def fix_database():
    """Fix database tables using raw SQL"""

    # Use absolute path to ensure correct database location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'data', 'library.db')
    print(f"🔧 Fixing database at: {db_path}")

    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        print(f"📁 Looking for database at: {db_path}")
        print("💡 Make sure you're running this script from the development directory")
        return False

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Drop existing tables with wrong names
        print("🗑️ Dropping existing tables with incorrect names...")
        cursor.execute("DROP TABLE IF EXISTS book")
        cursor.execute("DROP TABLE IF EXISTS patron")
        print("✅ Dropped tables: book, patron")

        # Create users table
        print("🏗️ Creating users table...")
        cursor.execute("""
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
        print("🏗️ Creating category table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create patrons table
        print("🏗️ Creating patrons table...")
        cursor.execute("""
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
        print("🏗️ Creating books table...")
        cursor.execute("""
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
        print("🏗️ Creating transactions table...")
        cursor.execute("""
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
        print("🏗️ Creating library_settings table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS library_settings (
                id INTEGER PRIMARY KEY,
                setting_key VARCHAR(50) NOT NULL UNIQUE,
                setting_value TEXT NOT NULL,
                description VARCHAR(200),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        existing_tables = [table[0] for table in tables]
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
            cursor.execute("SELECT id FROM library_settings WHERE setting_key = ?", (key,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    "UPDATE library_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
                    (json.dumps(value) if isinstance(value, (dict, list)) else str(value), key)
                )
            else:
                cursor.execute(
                    "INSERT INTO library_settings (setting_key, setting_value, description) VALUES (?, ?, ?)",
                    (key, json.dumps(value) if isinstance(value, (dict, list)) else str(value), f'Default {key}')
                )

        print("✅ Default library settings initialized")

        # Create default librarian user
        print("👤 Creating default librarian user...")
        cursor.execute("SELECT id FROM users WHERE role = 'librarian'")
        existing_librarian = cursor.fetchone()

        if not existing_librarian:
            # Create default librarian user
            password_hash = generate_password_hash('library123')
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role, is_active) VALUES (?, ?, ?, ?, ?)",
                ('librarian', 'librarian@library.com', password_hash, 'librarian', True)
            )
            print("✅ Default librarian user created: librarian/library123")
        else:
            print("ℹ️ Librarian user already exists")

        # Commit all changes
        conn.commit()
        print("🎉 Database fix completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during database fix: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("\n🚀 Database is now ready for use!")
        print("📝 You can start the application with: python start_server.py")
    else:
        print("\n❌ Database fix failed. Please check the errors above.")
        exit(1)
