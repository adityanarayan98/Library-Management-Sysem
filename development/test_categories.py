#!/usr/bin/env python3
"""
Test script to check existing categories in the database
"""

import sys
import os

# Add the library_management directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'library_management'))

try:
    from app import create_app
    from app.models import Category

    def test_categories():
        """Test if categories exist in database"""
        print("Testing categories in database...")

        # Create the app
        app = create_app()

        with app.app_context():
            # Query categories
            categories = Category.query.filter_by(is_active=True).all()

            print(f"Found {len(categories)} active categories:")
            for cat in categories:
                print(f"  - ID {cat.id}: '{cat.name}' - {cat.description or 'No description'}")

            if len(categories) == 0:
                print("No categories found. The autocomplete will allow creating new ones.")
            else:
                print("\nAutocomplete will suggest these categories when users type.")

        return True

    if __name__ == "__main__":
        success = test_categories()
        if success:
            print("\nCategories test completed successfully!")
        else:
            print("\nCategories test failed!")
            sys.exit(1)

except Exception as e:
    print(f"Error testing categories: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
