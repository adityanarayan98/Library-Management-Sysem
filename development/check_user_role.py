#!/usr/bin/env python3
import sys
import os

# Add the library_management directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library_management'))

try:
    from app import create_app
    from app.models import User

    print("🔍 Checking user roles in database...")

    app = create_app()
    with app.app_context():
        # Check all users in the database
        users = User.query.all()
        print('\n📋 Current users in database:')
        for user in users:
            print(f'  ID: {user.id}, Username: {user.username}, Role: {user.role}, Active: {user.is_active}')

        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f'\n👤 Admin user found: {admin_user.username}, Role: {admin_user.role}')
            if admin_user.role != 'admin':
                print('❌ ISSUE: Admin user does not have admin role!')
                print(f'   Current role: {admin_user.role}')
                print('   Expected role: admin')
            else:
                print('✅ Admin user has correct role')
        else:
            print('\n❌ No admin user found!')

except Exception as e:
    print(f"❌ Error checking database: {e}")
    print("This might indicate database connection issues or missing tables.")
