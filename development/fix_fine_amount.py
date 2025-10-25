#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'library_management'))

from app import create_app
from app.db import db
from sqlalchemy import text

def fix_fine_amount():
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        print("Checking for invalid fine_amount values...")

        # Check how many have invalid values
        result = conn.execute(text("SELECT COUNT(*) FROM transactions WHERE fine_amount IS NULL OR fine_amount = ''"))
        count = result.fetchone()[0]
        print(f"Found {count} transactions with invalid fine_amount")

        if count > 0:
            # Update them to 0.0
            conn.execute(text("UPDATE transactions SET fine_amount = 0.0 WHERE fine_amount IS NULL OR fine_amount = ''"))
            conn.commit()
            print(f"Updated {count} records to set fine_amount = 0.0")

            # Verify the fix
            result = conn.execute(text("SELECT COUNT(*) FROM transactions WHERE fine_amount IS NULL OR fine_amount = ''"))
            remaining = result.fetchone()[0]
            if remaining == 0:
                print("✅ All invalid fine_amount values have been fixed!")
            else:
                print(f"⚠️ Still {remaining} invalid values remaining")
        else:
            print("✅ No invalid fine_amount values found")

if __name__ == "__main__":
    fix_fine_amount()
