"""
Database utility class for the Library Management System
Provides database connection and backup functionality
"""

import sqlite3
import os
import sys
from flask import current_app

class Database:
    """Database utility class with PyInstaller support"""

    def __init__(self):
        self.db_path = None
        self._get_db_path()

    def _get_db_path(self):
        """Get database path with PyInstaller compatibility"""
        # For exe environment, use current working directory
        if getattr(sys, 'frozen', False):
            # Running as exe - use current working directory
            exe_dir = os.getcwd()
            data_dir = os.path.join(exe_dir, 'data')  # Use 'data' folder for consistency
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, 'library.db')
            print(f"Exe environment detected, database path: {self.db_path}")
        else:
            # Development environment - try multiple fallback paths
            try:
                # Try to get the database path from Flask app context
                if current_app:
                    basedir = os.path.dirname(os.path.dirname(current_app.root_path))
                    self.db_path = os.path.join(basedir, 'data', 'library.db')
            except:
                # Fallback to relative path - use same location as Flask app
                basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                self.db_path = os.path.join(basedir, 'data', 'library.db')

            # Additional fallback - try absolute path from current working directory
            if not self.db_path or not os.path.exists(self.db_path):
                self.db_path = os.path.join(os.getcwd(), 'development', 'data', 'library.db')

            # Final fallback - try relative to current file
            if not self.db_path or not os.path.exists(self.db_path):
                self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'library.db')

        # Create database file if it doesn't exist
        if self.db_path:
            instance_dir = os.path.dirname(self.db_path)
            os.makedirs(instance_dir, exist_ok=True)

            if not os.path.exists(self.db_path):
                # Create SQLite database file by making a connection
                try:
                    temp_conn = sqlite3.connect(self.db_path)
                    temp_conn.close()
                    print(f"Created new SQLite database at: {self.db_path}")
                except Exception as e:
                    print(f"Error creating database file: {e}")
                    # Fallback to empty file creation
                    with open(self.db_path, 'w') as f:
                        f.write("")
                    print(f"Created empty database file as fallback: {self.db_path}")

    def get_connection(self):
        """Get database connection"""
        try:
            if not self.db_path or not os.path.exists(self.db_path):
                print(f"Database file not found at: {self.db_path}")
                return None

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None

    def test_connection(self):
        """Test database connection"""
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"✅ Database connected successfully. Found {len(tables)} tables.")
                return True
            except Exception as e:
                print(f"❌ Database connection test failed: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_table_names(self):
        """Get list of all table names"""
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
            except Exception as e:
                print(f"Error getting table names: {e}")
                return []
            finally:
                conn.close()
        return []

    def backup_table(self, table_name):
        """Backup a specific table"""
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return {
                    'columns': columns,
                    'rows': rows,
                    'count': len(rows)
                }
            except Exception as e:
                print(f"Error backing up table {table_name}: {e}")
                return None
            finally:
                conn.close()
        return None

    def backup_all_tables(self):
        """Backup all tables in the database"""
        tables = self.get_table_names()
        backup_data = {}

        for table in tables:
            backup_data[table] = self.backup_table(table)

        return backup_data

    def close_connection(self, conn):
        """Close database connection"""
        if conn:
            try:
                conn.close()
            except:
                pass
