#!/usr/bin/env python3
import sqlite3
import os

# Check database structure
db_path = os.path.join(os.getcwd(), 'development', 'library_management', 'app', 'instance', 'library.db')
print(f"Checking database structure: {db_path}")
print(f"Database file exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")

        # Check users table structure
        if tables:
            cursor.execute("PRAGMA table_info(users)")
            users_columns = cursor.fetchall()
            print(f"Users table columns: {[col[1] for col in users_columns]}")

            # Check if admin user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
            admin_count = cursor.fetchone()[0]
            print(f"Admin users: {admin_count}")

            cursor.execute("SELECT username, role FROM users")
            all_users = cursor.fetchall()
            print(f"All users: {all_users}")

        conn.close()
        print("Database check completed successfully!")
    except Exception as e:
        print(f"Database check failed: {e}")
else:
    print("Database file does not exist!")
