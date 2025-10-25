"""
Database migration script to add new patron columns for OPAC system
Adds: password_hash, first_login, approved_by, approved_at, status columns
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def add_patron_columns():
    """Add missing columns to patrons table for OPAC functionality"""

    # Determine database path
    if os.path.exists('development/data/library.db'):
        db_path = 'development/data/library.db'
    elif os.path.exists('instance/library.db'):
        db_path = 'instance/library.db'
    elif os.path.exists('data/library.db'):
        db_path = 'data/library.db'
    else:
        print("❌ Database not found!")
        print("Available options:")
        print("  - development/data/library.db")
        print("  - instance/library.db")
        print("  - data/library.db")
        return

    print(f"📍 Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check current patrons table structure
        print("🔍 Checking current patrons table structure...")
        cursor.execute("PRAGMA table_info(patrons)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"📋 Current columns: {column_names}")

        # Add missing columns
        migrations = []

        # Add password_hash column
        if 'password_hash' not in column_names:
            print("➕ Adding password_hash column...")
            cursor.execute("ALTER TABLE patrons ADD COLUMN password_hash VARCHAR(128)")
            migrations.append("password_hash")

        # Add first_login column
        if 'first_login' not in column_names:
            print("➕ Adding first_login column...")
            cursor.execute("ALTER TABLE patrons ADD COLUMN first_login BOOLEAN DEFAULT 1")
            migrations.append("first_login")

        # Add approved_by column
        if 'approved_by' not in column_names:
            print("➕ Adding approved_by column...")
            cursor.execute("ALTER TABLE patrons ADD COLUMN approved_by INTEGER")
            migrations.append("approved_by")

        # Add approved_at column
        if 'approved_at' not in column_names:
            print("➕ Adding approved_at column...")
            cursor.execute("ALTER TABLE patrons ADD COLUMN approved_at DATETIME")
            migrations.append("approved_at")

        # Update status column default to 'pending' if it exists
        if 'status' in column_names:
            print("🔄 Updating status column defaults...")
            cursor.execute("UPDATE patrons SET status = 'pending' WHERE status IS NULL OR status = ''")
            migrations.append("status_defaults")



        # Commit all changes
        conn.commit()

        if migrations:
            print(f"✅ Successfully added: {', '.join(migrations)}")
            print("🎯 Database migration completed!")
        else:
            print("ℹ️ No migrations needed - columns already exist")

        # Show final table structure
        print("\n📋 Final patrons table structure:")
        cursor.execute("PRAGMA table_info(patrons)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")



    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting OPAC database migration...")
    add_patron_columns()
    print("\n✨ Migration script completed!")
