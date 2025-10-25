#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'library_management'))

from app import create_app
from app.db import db
from sqlalchemy import text

def test_fines():
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        print("Testing fines query...")

        try:
            # Test the main fines query
            outstanding_fines = conn.execute(text('''
                SELECT t.*, p.name as patron_name, p.roll_no, b.title as book_title, b.accession_number
                FROM transactions t
                JOIN patrons p ON t.patron_id = p.id
                JOIN books b ON t.book_id = b.id
                WHERE CAST(t.fine_amount AS REAL) > 0 AND t.fine_paid = 0 AND t.status = 'returned'
                ORDER BY CAST(t.fine_amount AS REAL) DESC
            ''')).fetchall()
            print(f"Query successful! Found {len(outstanding_fines)} outstanding fines")

            # Test stats query
            stats_result = conn.execute(text('''
                SELECT
                    COUNT(*) as total_outstanding,
                    COALESCE(SUM(CASE WHEN fine_amount IS NULL OR fine_amount = '' THEN 0.0 ELSE CAST(fine_amount AS REAL) END), 0) as total_amount,
                    COALESCE(AVG(CASE WHEN fine_amount IS NULL OR fine_amount = '' THEN 0.0 ELSE CAST(fine_amount AS REAL) END), 0) as avg_fine
                FROM transactions
                WHERE CAST(COALESCE(fine_amount, '0') AS REAL) > 0 AND fine_paid = 0 AND status = 'returned'
            ''')).fetchone()
            print(f"Stats query successful! Result: {stats_result}")

            # Check for any problematic fine_amount values
            result = conn.execute(text("SELECT id, fine_amount FROM transactions WHERE fine_amount IS NULL OR fine_amount = ''"))
            problematic = result.fetchall()
            if problematic:
                print(f"Found {len(problematic)} problematic records:")
                for row in problematic:
                    print(f"  ID {row[0]}: fine_amount = '{row[1]}'")
            else:
                print("No problematic fine_amount values found")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_fines()
