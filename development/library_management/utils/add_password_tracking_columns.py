#!/usr/bin/env python3
"""
Script to add password tracking columns to existing patrons table
This script adds the missing columns:
- password_changed_at (DateTime)
- password_changed_by (Integer, Foreign Key to users.id)
"""

import sys
import os
import logging

# Add the parent directory to the path to import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app first to set up context
from app import create_app

# Create Flask app context
app = create_app()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_password_tracking_columns():
    """Add password tracking columns to patrons table"""
    with app.app_context():
        try:
            from app.models import get_db

            # Get database connection
            db = get_db()

            # Check if columns already exist and add them if needed
            with db.engine.connect() as conn:
                # Check for password_changed_at column
                result = conn.execute("PRAGMA table_info(patrons)").fetchall()
                columns = [col[1] for col in result]

                if 'password_changed_at' not in columns:
                    logger.info("Adding password_changed_at column...")
                    conn.execute("ALTER TABLE patrons ADD COLUMN password_changed_at DATETIME")
                    logger.info("✅ Added password_changed_at column")
                else:
                    logger.info("ℹ️ password_changed_at column already exists")

                if 'password_changed_by' not in columns:
                    logger.info("Adding password_changed_by column...")
                    conn.execute("ALTER TABLE patrons ADD COLUMN password_changed_by INTEGER")
                    logger.info("✅ Added password_changed_by column")
                else:
                    logger.info("ℹ️ password_changed_by column already exists")

                # Note: SQLite commits automatically for DDL statements
                logger.info("✅ Database schema updated successfully")

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return False

    return True

def main():
    """Main function"""
    print("=" * 60)
    print("ADD PASSWORD TRACKING COLUMNS")
    print("=" * 60)
    print("This script will add password tracking columns to the patrons table:")
    print("- password_changed_at (DateTime)")
    print("- password_changed_by (Integer, Foreign Key)")
    print()

    # Auto-confirm for automated execution
    print("Auto-confirming execution...")
    confirm = 'yes'

    if confirm not in ['yes', 'y']:
        print("Operation cancelled.")
        return

    print("Updating database schema...")
    success = add_password_tracking_columns()

    print()
    print("=" * 60)
    if success:
        print("✅ SUCCESS: Database schema updated successfully!")
        print("📝 You can now use the password reset functionality")
    else:
        print("❌ FAILED: Could not update database schema")
    print("=" * 60)

if __name__ == "__main__":
    main()
