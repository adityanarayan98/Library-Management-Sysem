"""
Database migration script to add call_number column to books table
"""

import sqlite3
import os

def add_books_columns():
    """Add call_number column to books table"""

    # Determine database path
    if os.path.exists('development/data/library.db'):
        db_path = 'development/data/library.db'
    elif os.path.exists('instance/library.db'):
        db_path = 'instance/library.db'
    elif os.path.exists('data/library.db'):
        db_path = 'data/library.db'
    else:
        print("❌ Database not found!")
        return

    print(f"📍 Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check current books table structure
        print("🔍 Checking current books table structure...")
        cursor.execute("PRAGMA table_info(books)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"📋 Current columns: {column_names}")

        # Add call_number column if missing
        if 'call_number' not in column_names:
            print("➕ Adding call_number column to books table...")
            cursor.execute("ALTER TABLE books ADD COLUMN call_number VARCHAR(50)")
            print("✅ Successfully added call_number column")

            # Commit the change
            conn.commit()

            # Show final table structure
            print("\n📋 Updated books table structure:")
            cursor.execute("PRAGMA table_info(books)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        else:
            print("ℹ️ call_number column already exists")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Adding call_number column to books table...")
    add_books_columns()
    print("✨ Books table migration completed!")
