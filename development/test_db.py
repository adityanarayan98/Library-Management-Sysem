#!/usr/bin/env python3
import sqlite3
import os

# Test database connection
db_path = 'development/data/library.db'
print(f"Testing database connection to: {db_path}")
print(f"Database file exists: {os.path.exists(db_path)}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in database: {[table[0] for table in tables]}")

    # Test a simple query
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    print(f"Users in database: {user_count}")

    conn.close()
    print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed: {e}")
