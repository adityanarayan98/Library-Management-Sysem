#!/usr/bin/env python3
import sqlite3
import os

# Path to the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'library.db')

print(f"🔍 Checking database: {db_path}")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        print("❌ Users table does not exist!")
        conn.close()
        exit()

    # Get all users
    cursor.execute("SELECT id, username, role, is_active FROM users;")
    users = cursor.fetchall()

    print('\n📋 Current users in database:')
    for user in users:
        print(f'  ID: {user[0]}, Username: {user[1]}, Role: {user[2]}, Active: {user[3]}')

    # Check if admin user exists
    cursor.execute("SELECT id, username, role, is_active FROM users WHERE username = 'admin';")
    admin_user = cursor.fetchone()

    if admin_user:
        print(f'\n👤 Admin user found: {admin_user[1]}, Role: {admin_user[2]}')
        if admin_user[2] != 'admin':
            print('❌ ISSUE: Admin user does not have admin role!')
            print(f'   Current role: {admin_user[2]}')
            print('   Expected role: admin')

            # Fix the role
            print('\n🔧 Fixing admin user role...')
            cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'admin';")
            conn.commit()
            print('✅ Admin user role updated to admin')

        else:
            print('✅ Admin user has correct role')
    else:
        print('\n❌ No admin user found!')

    conn.close()

except Exception as e:
    print(f"❌ Error checking database: {e}")
