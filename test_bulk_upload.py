#!/usr/bin/env python3
"""
Test script for bulk upload functionality
"""
import requests
import os

# Test configuration
BASE_URL = "http://localhost:5000"
CSV_FILE = "test_patrons.csv"

def test_csv_file():
    """Test if CSV file exists and is readable"""
    print("📄 Testing CSV file...")
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r') as f:
            content = f.read()
            print(f"✅ CSV file found: {CSV_FILE}")
            print(f"📊 File size: {len(content)} characters")
            print(f"📋 Content preview: {content[:100]}...")
            return True
    else:
        print(f"❌ CSV file not found: {CSV_FILE}")
        return False

def test_flask_app():
    """Test if Flask app is running"""
    print("\n🌐 Testing Flask application...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 302:  # Redirect to login
            print("✅ Flask app is running (redirected to login)")
            return True
        else:
            print(f"⚠️ Flask app responded with status: {response.status_code}")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Flask app is not running")
        print("💡 Please start the app with: python development/start_server.py start")
        return False
    except Exception as e:
        print(f"❌ Error testing Flask app: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🗃️ Testing database connection...")
    try:
        import sqlite3
        db_path = "development/data/library.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✅ Database connected successfully")
            print(f"📋 Tables found: {[table[0] for table in tables]}")

            # Check existing patrons
            cursor.execute("SELECT COUNT(*) FROM patrons")
            patron_count = cursor.fetchone()[0]
            print(f"👥 Current patrons in database: {patron_count}")

            conn.close()
            return True
        else:
            print(f"❌ Database file not found: {db_path}")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Library Management System - Bulk Upload Test")
    print("=" * 60)

    # Run tests
    csv_ok = test_csv_file()
    flask_ok = test_flask_app()
    db_ok = test_database_connection()

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   • CSV File: {'✅ OK' if csv_ok else '❌ FAIL'}")
    print(f"   • Flask App: {'✅ OK' if flask_ok else '❌ FAIL'}")
    print(f"   • Database: {'✅ OK' if db_ok else '❌ FAIL'}")

    if csv_ok and flask_ok and db_ok:
        print("\n🎉 All tests passed! System is ready for bulk upload testing.")
        print("\n📋 Next Steps:")
        print("   1. Start the Flask app: python development/start_server.py start")
        print("   2. Login as admin (admin/admin123)")
        print("   3. Go to: http://localhost:5000/bulk_upload_patrons")
        print("   4. Upload the test_patrons.csv file")
        print("   5. Verify the patron was added successfully")
    else:
        print("\n⚠️ Some tests failed. Please fix the issues above before testing bulk upload.")

    return 0

if __name__ == "__main__":
    exit(main())
