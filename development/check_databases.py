import sqlite3
import os

def check_database(db_path, name):
    print(f"\n=== Checking {name} ===")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {[t[0] for t in tables]}")

            # Check users
            if any(t[0] == 'users' for t in tables):
                cursor.execute('SELECT username, role, is_active FROM users')
                users = cursor.fetchall()
                print(f"Users: {[(u[0], u[1], u[2]) for u in users]}")
            else:
                print("No users table found")

            # Check books
            if any(t[0] == 'books' for t in tables):
                cursor.execute('SELECT COUNT(*) FROM books')
                book_count = cursor.fetchone()[0]
                print(f"Books count: {book_count}")
                if book_count > 0:
                    cursor.execute('SELECT title, author, status FROM books LIMIT 5')
                    books = cursor.fetchall()
                    print(f"Sample books: {[(b[0], b[1], b[2]) for b in books]}")
            else:
                print("No books table found")

            conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Database file not found")

# Check both databases
check_database('data/library.db', 'Main database')
# Note: Using single database location now
