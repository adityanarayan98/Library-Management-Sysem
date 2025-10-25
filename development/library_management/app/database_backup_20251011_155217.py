"""
Simple SQLite database utilities for the Enhanced Library Management System
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self, db_path=None):
        print("🚀 Database class initializing with comprehensive detection...")

        if db_path is None:
            # Ultimate PyInstaller path detection with maximum robustness
            basedir = self._get_application_directory_comprehensive()
            print(f"📁 Final application directory: {basedir}")

            # Create database in the same directory as the executable/script
            db_path = os.path.join(basedir, 'instance', 'library.db')
            print(f"💾 Database path will be: {db_path}")

            # Ensure the instance directory exists with absolute path
            instance_dir = os.path.join(basedir, 'instance')
            print(f"📂 Ensuring instance directory: {instance_dir}")

            # Create directory with bulletproof error handling
            success = self._ensure_directory_exists_bulletproof(instance_dir)
            if not success:
                print("❌ Primary directory creation failed, trying multiple fallbacks...")
                # Multiple fallback strategies
                db_path = self._get_fallback_database_path()
                instance_dir = os.path.dirname(db_path)
                print(f"🔄 Using fallback directory: {instance_dir}")
                self._ensure_directory_exists_bulletproof(instance_dir)

        self.db_path = db_path
        print(f"🎯 Final database path: {self.db_path}")

        # Comprehensive database creation testing
        if not self._test_database_creation_comprehensive():
            print("❌ Database creation test failed!")
            print("🔄 Attempting emergency fallback...")
            self.db_path = self._get_emergency_database_path()
            print(f"🚨 Using emergency database path: {self.db_path}")

        print("✅ Database initialization starting...")
        self.init_database()

    def _ensure_directory_exists_bulletproof(self, directory):
        """Bulletproof directory creation with multiple strategies"""
        print(f"🛡️ Attempting bulletproof directory creation for: {directory}")

        strategies = [
            lambda: self._create_directory_basic(directory),
            lambda: self._create_directory_with_permissions(directory),
            lambda: self._create_directory_with_alternate_path(directory),
            lambda: self._create_directory_in_cwd(directory)
        ]

        for i, strategy in enumerate(strategies, 1):
            print(f"📋 Trying strategy {i}/4...")
            try:
                if strategy():
                    print(f"✅ Strategy {i} succeeded!")
                    return True
            except Exception as e:
                print(f"❌ Strategy {i} failed: {e}")
                continue

        print("💥 All directory creation strategies failed!")
        return False

    def _create_directory_basic(self, directory):
        """Basic directory creation"""
        os.makedirs(directory, exist_ok=True)
        return True

    def _create_directory_with_permissions(self, directory):
        """Directory creation with permission handling"""
        try:
            os.makedirs(directory, exist_ok=True)
            # Test write permissions
            test_file = os.path.join(directory, 'perm_test.txt')
            with open(test_file, 'w') as f:
                f.write('permission_test')
            os.remove(test_file)
            return True
        except PermissionError:
            print(f"⚠️ Permission denied for {directory}, trying parent directory")
            parent_dir = os.path.dirname(directory)
            if parent_dir != directory:
                return self._create_directory_basic(parent_dir)
            return False

    def _create_directory_with_alternate_path(self, directory):
        """Try creating in alternate locations"""
        # Try user's home directory
        home_dir = os.path.expanduser('~')
        alt_dir = os.path.join(home_dir, 'LibraryManagementSystem', 'instance')
        print(f"🔄 Trying alternate directory: {alt_dir}")
        return self._create_directory_basic(alt_dir)

    def _create_directory_in_cwd(self, directory):
        """Create in current working directory as last resort"""
        cwd = os.getcwd()
        fallback_dir = os.path.join(cwd, 'instance')
        print(f"🏠 Creating in current working directory: {fallback_dir}")
        return self._create_directory_basic(fallback_dir)

    def _test_database_creation_comprehensive(self):
        """Comprehensive database creation testing"""
        print(f"🧪 Running comprehensive database creation test...")

        try:
            # Ensure directory exists first
            db_dir = os.path.dirname(self.db_path)
            os.makedirs(db_dir, exist_ok=True)

            # Test 1: Basic SQLite connection
            print("🔌 Testing basic SQLite connection...")
            test_conn = sqlite3.connect(self.db_path)
            test_conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            test_conn.execute("INSERT INTO test (id) VALUES (1)")
            test_conn.commit()

            # Test 2: Verify data can be read back
            cursor = test_conn.execute("SELECT * FROM test")
            rows = cursor.fetchall()
            if len(rows) != 1 or rows[0][0] != 1:
                raise Exception("Data verification failed")

            # Test 3: Test table creation (similar to actual app)
            test_conn.execute('''
                CREATE TABLE IF NOT EXISTS test_users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL
                )
            ''')

            test_conn.close()

            # Clean up test
            os.remove(self.db_path)
            print("✅ Comprehensive database creation test passed!")
            return True

        except Exception as e:
            print(f"❌ Comprehensive database test failed: {e}")
            print(f"🔍 Debug info - db_path: {self.db_path}")
            print(f"🔍 Debug info - db_dir: {os.path.dirname(self.db_path)}")
            print(f"🔍 Debug info - db_dir exists: {os.path.exists(os.path.dirname(self.db_path))}")
            return False

    def _get_fallback_database_path(self):
        """Get fallback database path using multiple strategies"""
        print("🔄 Getting fallback database path...")

        strategies = [
            self._get_path_from_executable,
            self._get_path_from_script_location,
            self._get_path_from_cwd,
            self._get_path_from_temp,
            self._get_path_from_home
        ]

        for strategy in strategies:
            try:
                path = strategy()
                if path:
                    print(f"✅ Fallback strategy succeeded: {path}")
                    return path
            except Exception as e:
                print(f"❌ Fallback strategy failed: {e}")
                continue

        # Ultimate fallback
        return os.path.join(os.getcwd(), 'instance', 'library.db')

    def _get_path_from_executable(self):
        """Get path from executable location"""
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            return os.path.join(exe_dir, 'instance', 'library.db')
        return None

    def _get_path_from_script_location(self):
        """Get path from script location"""
        if '__file__' in globals():
            script_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(script_dir, 'instance', 'library.db')
        return None

    def _get_path_from_cwd(self):
        """Get path from current working directory"""
        return os.path.join(os.getcwd(), 'instance', 'library.db')

    def _get_path_from_temp(self):
        """Get path from temp directory"""
        temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'), 'LibraryManagementSystem')
        return os.path.join(temp_dir, 'instance', 'library.db')

    def _get_path_from_home(self):
        """Get path from user home directory"""
        home_dir = os.path.expanduser('~')
        home_app_dir = os.path.join(home_dir, 'LibraryManagementSystem')
        return os.path.join(home_app_dir, 'instance', 'library.db')

    def _get_emergency_database_path(self):
        """Get emergency database path when all else fails"""
        print("🚨 Using emergency database path...")
        # Use a path that's almost guaranteed to work
        emergency_paths = [
            os.path.join(os.getcwd(), 'data', 'library.db'),
            os.path.join(os.getcwd(), 'library.db'),
            os.path.join(os.path.expanduser('~'), 'library.db')
        ]

        for path in emergency_paths:
            try:
                db_dir = os.path.dirname(path)
                os.makedirs(db_dir, exist_ok=True)
                print(f"🚨 Emergency path available: {path}")
                return path
            except Exception as e:
                print(f"❌ Emergency path failed: {path} - {e}")
                continue

        # Absolute last resort
        return 'library.db'

    def _get_application_directory_comprehensive(self):
        """Comprehensive application directory detection"""
        print("🔍 Running comprehensive application directory detection...")

        # Strategy 1: PyInstaller frozen executable
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            exe_dir = os.path.dirname(exe_path)
            print(f"📦 PyInstaller executable detected: {exe_path}")
            print(f"📁 Executable directory: {exe_dir}")

            # Additional validation
            if os.path.exists(exe_path):
                print("✅ Executable file exists")
                return exe_dir
            else:
                print("⚠️ Executable file not found, trying alternatives")

        # Strategy 2: PyInstaller _MEIPASS
        if hasattr(sys, '_MEIPASS'):
            meipass_path = sys._MEIPASS
            print(f"📦 PyInstaller _MEIPASS detected: {meipass_path}")
            if os.path.exists(meipass_path):
                return meipass_path

        # Strategy 3: Script file location
        if '__file__' in globals():
            script_path = os.path.abspath(__file__)
            script_dir = os.path.dirname(script_path)
            print(f"📄 Script file detected: {script_path}")
            print(f"📁 Script directory: {script_dir}")

            # Check for PyInstaller temp directory patterns
            if any(pattern in script_dir.lower() for pattern in ['temp', '_mei', 'pyinstaller']):
                print("📦 Detected PyInstaller temp directory pattern")
                return script_dir
            else:
                print("📄 Regular script directory")
                return script_dir

        # Strategy 4: Current working directory
        cwd = os.getcwd()
        print(f"📍 Using current working directory: {cwd}")
        return cwd

    def _ensure_directory_exists(self, directory):
        """Ensure directory exists with comprehensive error handling"""
        try:
            # Create directory with full permissions
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Directory created/verified: {directory}")

            # Test if we can write to the directory
            test_file = os.path.join(directory, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("✓ Directory write test successful")
            return True

        except Exception as e:
            print(f"✗ Error with directory {directory}: {e}")
            return False

    def _test_database_creation(self):
        """Test if database can be created at the specified path"""
        try:
            print(f"🧪 Testing database creation at: {self.db_path}")

            # Ensure directory exists
            db_dir = os.path.dirname(self.db_path)
            os.makedirs(db_dir, exist_ok=True)

            # Try to create a test database
            test_conn = sqlite3.connect(self.db_path)
            test_conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            test_conn.execute("INSERT INTO test (id) VALUES (1)")
            test_conn.commit()
            test_conn.close()

            # Clean up test
            os.remove(self.db_path)
            print("✓ Database creation test successful")
            return True

        except Exception as e:
            print(f"✗ Database creation test failed: {e}")
            return False

    def _get_application_directory(self):
        """Get the correct application directory with multiple detection methods"""
        print("🔍 Detecting application directory...")

        try:
            # Method 1: Check if running as PyInstaller bundle
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                print(f"📦 Detected PyInstaller bundle: {exe_path}")
                return os.path.dirname(exe_path)

            # Method 2: Check for _MEIPASS (PyInstaller temp directory)
            if hasattr(sys, '_MEIPASS'):
                print(f"📦 Detected PyInstaller _MEIPASS: {sys._MEIPASS}")
                return sys._MEIPASS

            # Method 3: Check if __file__ path suggests PyInstaller
            if '__file__' in globals():
                app_path = os.path.dirname(os.path.abspath(__file__))
                print(f"📄 Script file path: {app_path}")

                # Check if we're in a PyInstaller temp directory
                if 'temp' in app_path.lower() and '_mei' in app_path:
                    print(f"📦 Detected PyInstaller temp directory: {app_path}")
                    return app_path
                else:
                    print(f"📄 Regular script directory: {app_path}")
                    return os.path.dirname(app_path)

        except Exception as e:
            print(f"❌ Error in path detection: {e}")

        # Method 4: Ultimate fallback to current working directory
        print("📍 Using current working directory as final fallback")
        return os.getcwd()

    def get_connection(self):
        """Get database connection"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'librarian',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS patrons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    patron_type TEXT NOT NULL,
                    department TEXT,
                    division TEXT,
                    status TEXT DEFAULT 'active',
                    max_books INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    isbn TEXT,
                    publisher TEXT,
                    publication_year INTEGER,
                    accession_number TEXT UNIQUE NOT NULL,
                    category_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patron_id INTEGER NOT NULL,
                    book_id INTEGER NOT NULL,
                    issue_date DATE NOT NULL,
                    due_date DATE NOT NULL,
                    return_date DATE,
                    status TEXT DEFAULT 'issued',
                    fine_amount REAL DEFAULT 0.0,
                    fine_paid BOOLEAN DEFAULT 0,
                    issued_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patron_id) REFERENCES patrons (id),
                    FOREIGN KEY (book_id) REFERENCES books (id),
                    FOREIGN KEY (issued_by) REFERENCES users (id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS library_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Initialize default settings if not exists
            self.initialize_defaults()

    def initialize_defaults(self):
        """Initialize default library settings"""
        defaults = {
            'fine_per_day': '1.0',
            'student_due_days': '14',
            'faculty_due_days': '30',
            'staff_due_days': '21',
            'student_max_books': '3',
            'faculty_max_books': '5',
            'staff_max_books': '4',
            'library_name': 'Library',
            'librarian_email': 'library@example.com'
        }

        with self.get_connection() as conn:
            for key, value in defaults.items():
                conn.execute('''
                    INSERT OR IGNORE INTO library_settings (setting_key, setting_value, description)
                    VALUES (?, ?, ?)
                ''', (key, value, f'Default {key}'))

    def get_setting(self, key, default=None):
        """Get setting value by key"""
        with self.get_connection() as conn:
            result = conn.execute(
                'SELECT setting_value FROM library_settings WHERE setting_key = ?',
                (key,)
            ).fetchone()
            return result[0] if result else default

    def set_setting(self, key, value, description=None):
        """Set or update setting"""
        with self.get_connection() as conn:
            if description:
                conn.execute('''
                    UPDATE library_settings SET setting_value = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE setting_key = ?
                ''', (str(value), description, key))
            else:
                conn.execute('''
                    UPDATE library_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE setting_key = ?
                ''', (str(value), key))

    def create_user(self, username, email, password, role='librarian'):
        """Create a new user"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, generate_password_hash(password), role))
            return conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    def get_user_by_username(self, username):
        """Get user by username"""
        with self.get_connection() as conn:
            result = conn.execute(
                'SELECT * FROM users WHERE username = ? AND is_active = 1',
                (username,)
            ).fetchone()
            return self.row_to_dict(result, 'users') if result else None

    def row_to_dict(self, row, table_name):
        """Convert database row to dictionary"""
        if not row:
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]

            # Safely convert row to dictionary with null checking
            try:
                # Ensure all values are properly converted to strings or appropriate types
                safe_row = []
                for value in row:
                    if value is None:
                        safe_row.append(None)
                    else:
                        safe_row.append(str(value) if not isinstance(value, (int, float, bool)) else value)

                return dict(zip(columns, safe_row))
            except Exception as e:
                print(f"Warning: Error converting row to dict: {e}")
                # Fallback: create dict with safe string conversion
                return dict(zip(columns, [str(val) if val is not None else None for val in row]))

# Global database instance
db = Database()

# User class for Flask-Login
class User:
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.role = user_data['role']
        self.is_active = user_data['is_active']

    def get_id(self):
        """Required method for Flask-Login"""
        return str(self.id)

    @property
    def is_authenticated(self):
        """Required property for Flask-Login"""
        return True

    @property
    def is_anonymous(self):
        """Required property for Flask-Login"""
        return False

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    @staticmethod
    def get_by_username(username):
        user_data = db.get_user_by_username(username)
        return User(user_data) if user_data else None
