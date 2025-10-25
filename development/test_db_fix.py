#!/usr/bin/env python3
"""
Test script to verify database fix
"""

import sqlite3
import os

def test_database():
    """Test that the database and transactions table work correctly"""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'data', 'library.db')

    print(f"🔍 Testing database at: {db_path}")

    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        existing_tables = [table[0] for table in tables]
        print(f"📋 Current tables: {existing_tables}")

        # Test the original failing query
        print("🧪 Testing original failing query...")
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE patron_id = ? AND status = ?', (1, 'issued'))
        count = cursor.fetchone()
        print(f"✅ Query successful! Count: {count[0]}")

        # Test a few more queries to ensure everything works
        print("🧪 Testing additional queries...")

        # Check if we can query all tables
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        print(f"👥 Users count: {users_count}")

        cursor.execute('SELECT COUNT(*) FROM books')
        books_count = cursor.fetchone()[0]
        print(f"📚 Books count: {books_count}")

        cursor.execute('SELECT COUNT(*) FROM patrons')
        patrons_count = cursor.fetchone()[0]
        print(f"👤 Patrons count: {patrons_count}")

        cursor.execute('SELECT COUNT(*) FROM category')
        categories_count = cursor.fetchone()[0]
        print(f"🏷️ Categories count: {categories_count}")

        cursor.execute('SELECT COUNT(*) FROM library_settings')
        settings_count = cursor.fetchone()[0]
        print(f"⚙️ Settings count: {settings_count}")

        print("✅ All tests passed! Database is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_database()
    if success:
        print("\n🎉 Database verification completed successfully!")
        print("🚀 Your book issuing functionality should now work correctly.")
    else:
        print("\n❌ Database verification failed.")
        exit(1)
