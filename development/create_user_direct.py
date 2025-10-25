import sqlite3
import os
from werkzeug.security import generate_password_hash

# Create user directly in the database
db_path = 'development/data/library.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute('SELECT username FROM users WHERE username = ?', ('Rasmi',))
    existing_user = cursor.fetchone()

    if not existing_user:
        # Create the user
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Rasmi', 'rasmi@iitgn.ac.in', generate_password_hash('Admin@159'), 'librarian', 1))

        conn.commit()
        print("✅ User 'Rasmi' created successfully in library_management database!")
    else:
        print("ℹ️  User 'Rasmi' already exists in library_management database")

    # Verify the user was created
    cursor.execute('SELECT username, role, is_active FROM users WHERE username = ?', ('Rasmi',))
    user = cursor.fetchone()
    if user:
        print(f"✅ Verified user: {user[0]} (role: {user[1]}, active: {user[2]})")

    conn.close()
else:
    print("❌ Database file not found!")
