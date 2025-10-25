import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta

def add_sample_data():
    db_path = 'development/data/library.db'

    if not os.path.exists(db_path):
        print("Database not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add sample categories
        categories = [
            ('Computer Science', 'Books related to computer science and programming'),
            ('Mathematics', 'Mathematics textbooks and references'),
            ('Physics', 'Physics books and research materials'),
            ('Literature', 'Fiction and non-fiction literature'),
            ('Engineering', 'Engineering textbooks and manuals')
        ]

        print("Adding sample categories...")
        for category in categories:
            cursor.execute('''
                INSERT OR IGNORE INTO category (name, description, is_active)
                VALUES (?, ?, 1)
            ''', category)

        # Add sample patrons
        patrons = [
            ('2023BCS001', 'Alice Johnson', 'alice@email.com', '9876543210', 'student', 'CSE', 'B.Tech', 'active', 3),
            ('2023BCS002', 'Bob Smith', 'bob@email.com', '9876543211', 'student', 'CSE', 'B.Tech', 'active', 3),
            ('FAC001', 'Dr. Sarah Wilson', 'sarah.wilson@iitgn.ac.in', '9876543212', 'faculty', 'CSE', 'PhD', 'active', 5),
            ('STF001', 'Mr. Mike Davis', 'mike.davis@iitgn.ac.in', '9876543213', 'staff', 'Library', 'Staff', 'active', 4),
            ('2023BME001', 'Carol Brown', 'carol@email.com', '9876543214', 'student', 'ME', 'B.Tech', 'active', 3)
        ]

        print("Adding sample patrons...")
        for patron in patrons:
            cursor.execute('''
                INSERT OR IGNORE INTO patrons (roll_no, name, email, phone, patron_type, department, division, status, max_books)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', patron)

        # Add sample books
        books = [
            ('Introduction to Algorithms', 'Thomas H. Cormen', '9780262033848', 'MIT Press', 2009, 'CS001', 1, 'available'),
            ('Computer Networking: A Top-Down Approach', 'James F. Kurose', '9780133594140', 'Pearson', 2016, 'CS002', 1, 'available'),
            ('Clean Code', 'Robert C. Martin', '9780132350884', 'Prentice Hall', 2008, 'CS003', 1, 'issued'),
            ('The Pragmatic Programmer', 'Andrew Hunt', '9780201616224', 'Addison-Wesley', 1999, 'CS004', 1, 'available' ),
            ('Calculus: Early Transcendentals', 'James Stewart', '9781285741550', 'Cengage Learning', 2015, 'MATH001', 2, 'available'),
            ('University Physics', 'Young and Freedman', '9780133969290', 'Pearson', 2015, 'PHY001', 3, 'available'),
            ('To Kill a Mockingbird', 'Harper Lee', '9780061120084', 'Harper Perennial', 2002, 'LIT001', 4, 'available'),
            ('1984', 'George Orwell', '9780451524935', 'Signet Classic', 1950, 'LIT002', 4, 'issued'),
            ('Thermodynamics: An Engineering Approach', 'Yunus Cengel', '9780073398174', 'McGraw-Hill', 2014, 'ENG001', 5, 'available'),
            ('Machine Learning', 'Tom M. Mitchell', '9780070428072', 'McGraw-Hill', 1997, 'CS005', 1, 'available')
        ]

        print("Adding sample books...")
        for book in books:
            cursor.execute('''
                INSERT OR IGNORE INTO books (title, author, isbn, publisher, publication_year, accession_number, category_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', book)

        # Add sample transactions (some books issued)
        # First get the patron and book IDs
        cursor.execute("SELECT id FROM patrons WHERE roll_no = '2023BCS001'")
        patron1_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM patrons WHERE roll_no = '2023BCS002'")
        patron2_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM books WHERE accession_number = 'CS003'")
        book1_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM books WHERE accession_number = 'LIT002'")
        book2_id = cursor.fetchone()[0]

        # Add some overdue transactions for testing fines
        overdue_date = (date.today() - timedelta(days=10)).strftime('%Y-%m-%d')  # 10 days ago
        transactions = [
            (patron1_id, book1_id, overdue_date, (date.today() - timedelta(days=5)).strftime('%Y-%m-%d'), None, 'issued', 0.0, 0, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            (patron2_id, book2_id, overdue_date, (date.today() - timedelta(days=5)).strftime('%Y-%m-%d'), None, 'issued', 0.0, 0, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ]

        print("Adding sample transactions...")
        for transaction in transactions:
            cursor.execute('''
                INSERT OR IGNORE INTO transactions (patron_id, book_id, issue_date, due_date, return_date, status, fine_amount, fine_paid, issued_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', transaction)

        # Update book status for issued books
        cursor.execute("UPDATE books SET status = 'issued' WHERE accession_number IN ('CS003', 'LIT002')")

        # Now return the overdue books to calculate fines
        print("Returning overdue books to calculate fines...")
        overdue_transactions = cursor.execute('''
            SELECT id, due_date FROM transactions
            WHERE status = 'issued' AND due_date < ?
        ''', (date.today().strftime('%Y-%m-%d'),)).fetchall()

        for trans in overdue_transactions:
            trans_id = trans[0]
            due_date = trans[1]
            overdue_days = (date.today() - date.fromisoformat(due_date)).days
            fine_amount = overdue_days * 1.0  # fine_per_day = 1.0

            cursor.execute('''
                UPDATE transactions
                SET return_date = ?, status = 'returned', fine_amount = ?
                WHERE id = ?
            ''', (date.today().strftime('%Y-%m-%d'), fine_amount, trans_id))

            # Update book status back to available
            cursor.execute('''
                UPDATE books SET status = 'available'
                WHERE id = (SELECT book_id FROM transactions WHERE id = ?)
            ''', (trans_id,))

        conn.commit()
        print("Overdue books returned and fines calculated!")

        conn.commit()
        print("Sample data added successfully!")

        # Show summary
        print("\nSummary:")
        cursor.execute("SELECT COUNT(*) FROM category")
        categories_count = cursor.fetchone()[0]
        print(f"   • Categories: {categories_count}")

        cursor.execute("SELECT COUNT(*) FROM patrons")
        patrons_count = cursor.fetchone()[0]
        print(f"   • Patrons: {patrons_count}")

        cursor.execute("SELECT COUNT(*) FROM books")
        books_count = cursor.fetchone()[0]
        print(f"   • Books: {books_count}")

        cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'issued'")
        issued_count = cursor.fetchone()[0]
        print(f"   • Books Issued: {issued_count}")

    except Exception as e:
        print(f"Error adding sample data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_sample_data()
