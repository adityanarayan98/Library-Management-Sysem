#!/usr/bin/env python3
import sys
import os

# Add the library_management directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library_management'))

try:
    from app import create_app
    from app.models import User

    print("🔐 Testing admin user authentication...")

    app = create_app()
    with app.app_context():
        # Test the admin user authentication
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f'✅ Admin user found: {admin_user.username}')
            print(f'   Role: {admin_user.role}')
            print(f'   Active: {admin_user.is_active}')
            print(f'   Password check: {admin_user.check_password("admin123")}')
            print(f'   is_admin() method: {admin_user.is_admin()}')

            # Test role-based access logic
            role_check = admin_user.role in ['admin', 'librarian']
            print(f'   Role access check: {role_check}')

        else:
            print('❌ Admin user not found!')

except Exception as e:
    print(f"❌ Error testing authentication: {e}")
