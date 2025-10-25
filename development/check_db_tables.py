import sqlite3
import os

# Check database path
db_path = 'development/data/library.db'
print(f"Checking database at: {db_path}")

if os.path.exists(db_path):
    print("✅ Database file exists")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"\n📋 Existing tables ({len(tables)}):")
    if tables:
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("  No tables found")

    # Check if required tables exist
    required_tables = ['users', 'books', 'patrons', 'category', 'transaction', 'library_settings']
    existing_table_names = [table[0] for table in tables]

    print("\n🔍 Required tables check:")
    for table in required_tables:
        if table in existing_table_names:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} (missing)")

    conn.close()
else:
    print("❌ Database file does not exist")
