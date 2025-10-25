#!/usr/bin/env python3

from app import create_app
from app.models import LibrarySettings

def check_settings():
    app = create_app()
    with app.app_context():
        # Check current librarian email setting
        librarian_email = LibrarySettings.get_setting('librarian_email', 'NOT_FOUND')
        print(f"Current librarian_email setting: {librarian_email}")

        # List all settings
        all_settings = LibrarySettings.query.all()
        print("\nAll settings in database:")
        for setting in all_settings:
            print(f"  {setting.setting_key}: {setting.setting_value}")

        # Initialize default settings if none exist
        if not all_settings:
            print("\nNo settings found. Initializing defaults...")
            LibrarySettings.initialize_defaults()
            print("Default settings initialized.")

            # Check librarian email again
            librarian_email = LibrarySettings.get_setting('librarian_email', 'NOT_FOUND')
            print(f"Librarian email after initialization: {librarian_email}")
        else:
            print(f"\nFound {len(all_settings)} settings in database.")

if __name__ == "__main__":
    check_settings()
