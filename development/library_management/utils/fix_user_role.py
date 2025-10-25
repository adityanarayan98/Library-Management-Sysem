#!/usr/bin/env python3
"""
Quick script to fix user role from librarian to admin using direct database access
"""

import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_user_role():
    """Update existing user role to admin using direct SQL"""
    # Get database path
    basedir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(basedir, 'library_management', 'instance', 'library.db')

    if not os.path.exists(db_path):
        print("❌ Database not found at:", db_path)
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if users table exists and get users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table not found")
            return False

        # Get all users
        cursor.execute("SELECT id, username, role FROM users WHERE is_active = 1")
        users = cursor.fetchall()

        if not users:
            print("❌ No users found in database")
            return False

        print(f"📋 Found {len(users)} user(s) in database:")

        for user in users:
            user_id, username, role = user
            print(f"  - {username} (role: {role})")

            # Update role to admin if not already admin
            if role != 'admin':
                cursor.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
                print(f"  ✅ Updated {username} role to 'admin'")
            else:
                print(f"  ℹ️  {username} already has admin role")

        # Commit changes
        conn.commit()
        conn.close()
        print("✅ User role(s) updated successfully!")
        return True

    except Exception as e:
        print(f"❌ Error updating user roles: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing user role to admin...")
    success = fix_user_role()

    if success:
        print("🎉 All users now have admin privileges!")
        print("You can now access all export/backup features.")
    else:
        print("❌ Failed to update user roles.")
