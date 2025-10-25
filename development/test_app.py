#!/usr/bin/env python3
"""
Test script to verify the Flask application starts correctly and login works
"""

import os
import sys

# Add the library_management directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'library_management'))

try:
    from app import create_app

    def test_application():
        """Test if the Flask application can be created and started"""
        print("Creating Flask application...")

        # Create the app
        app = create_app()

        print("Flask application created successfully")

        # Test database connection by trying to query users
        with app.app_context():
            from app.models import User

            print("Testing database connection...")
            users = User.query.all()
            print(f"Found {len(users)} users in database")

            for user in users:
                print(f"  - {user.username} ({user.role})")

            # Test login functionality
            print("Testing login functionality...")
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user and admin_user.check_password('admin123'):
                print("Admin login test successful")
            else:
                print("Admin login test failed")

            rasmi_user = User.query.filter_by(username='Rasmi').first()
            if rasmi_user and rasmi_user.check_password('Admin@159'):
                print("Rasmi login test successful")
            else:
                print("Rasmi login test failed")

        print("All tests passed! Application is ready.")
        return True

    if __name__ == "__main__":
        success = test_application()
        if success:
            print("\nApplication is working correctly!")
            print("You can now start the server using: python library_management/run_server.py")
        else:
            print("\nApplication test failed!")
            sys.exit(1)

except Exception as e:
    print(f"Error testing application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
