#!/usr/bin/env python3
"""
Script to set default password "12345" for all existing patrons
This script will:
1. Update all existing patrons with password "12345"
2. Set first_login = True for all patrons to force password change
3. Display progress and results
"""

import sys
import os
import logging

# Add the parent directory to the path to import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app first to set up context
from app import create_app
from werkzeug.security import generate_password_hash

# Create Flask app context
app = create_app()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def set_default_passwords():
    """Set default password for all existing patrons"""
    with app.app_context():
        try:
            from app.models import Patron, get_db
            # Get database connection
            db = get_db()

            # Get all patrons
            patrons = Patron.query.all()

            if not patrons:
                logger.info("No patrons found in database")
                return 0

            logger.info(f"Found {len(patrons)} patrons in database")

            updated_count = 0
            skipped_count = 0

            for patron in patrons:
                try:
                    # Set default password hash
                    patron.password_hash = generate_password_hash('12345')
                    # Set first_login to True to force password change
                    patron.first_login = True
                    updated_count += 1

                    logger.info(f"Updated patron: {patron.roll_no} - {patron.name}")

                except Exception as e:
                    logger.error(f"Error updating patron {patron.roll_no}: {str(e)}")
                    skipped_count += 1

            # Commit all changes
            db.session.commit()

            logger.info("\n=== SUMMARY ===")
            logger.info(f"Successfully updated: {updated_count} patrons")
            if skipped_count > 0:
                logger.warning(f"Skipped: {skipped_count} patrons (due to errors)")

            return updated_count

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return 0

def main():
    """Main function"""
    print("=" * 60)
    print("DEFAULT PATRON PASSWORD SETUP")
    print("=" * 60)
    print("This script will set '12345' as the default password for all existing patrons.")
    print("All patrons will be required to change their password on first login.")
    print()

    # Auto-confirm for automated execution
    print("Auto-confirming execution...")
    confirm = 'yes'

    if confirm not in ['yes', 'y']:
        print("Operation cancelled.")
        return

    print("Setting default passwords...")
    updated_count = set_default_passwords()

    print()
    print("=" * 60)
    if updated_count > 0:
        print(f"✅ SUCCESS: Updated {updated_count} patrons with default password '12345'")
        print("📝 All patrons will be required to change their password on first login")
    else:
        print("❌ No patrons were updated")
    print("=" * 60)

if __name__ == "__main__":
    main()
