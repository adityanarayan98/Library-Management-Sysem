#!/usr/bin/env python3

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import LibrarySettings

def set_librarian_email():
    app = create_app()
    with app.app_context():
        # Set librarian email to IITGN address
        LibrarySettings.set_setting('librarian_email', 'librarian@iitgn.ac.in', 'Contact email for library administration')
        print("✅ Librarian email set to: librarian@iitgn.ac.in")

        # Verify the setting was saved
        saved_email = LibrarySettings.get_setting('librarian_email', 'NOT_FOUND')
        print(f"✅ Verified setting: {saved_email}")

        # Show all settings for reference
        all_settings = LibrarySettings.query.all()
        print(f"\n📋 All settings ({len(all_settings)} total):")
        for setting in all_settings:
            print(f"  {setting.setting_key}: {setting.setting_value}")

if __name__ == "__main__":
    set_librarian_email()
