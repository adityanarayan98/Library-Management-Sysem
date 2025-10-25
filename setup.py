#!/usr/bin/env python3
"""
Setup script for Library Management System
This script helps users set up the library management system easily
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} - Compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")

    requirements_path = "library_management/requirements.txt"
    if not os.path.exists(requirements_path):
        print(f"❌ Requirements file not found: {requirements_path}")
        return False

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_database():
    """Check database setup"""
    print("\n🗃 Checking database setup...")

    db_path = "development/data/library.db"
    if os.path.exists(db_path):
        print(f"✅ Database found: {db_path}")
        return True
    else:
        print(f"ℹ️ Database will be created on first run: {db_path}")
        return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    print("\n⚙️ Checking environment configuration...")

    env_path = "library_management/.env"
    if os.path.exists(env_path):
        print(f"✅ .env file already exists: {env_path}")
        return True

    print("ℹ️ Creating default .env file...")
    try:
        with open(env_path, 'w') as f:
            f.write("SECRET_KEY=your-secret-key-change-this-in-production\n")
            f.write("FLASK_ENV=development\n")
            f.write("DATABASE_URL=sqlite:///instance/library.db\n")
        print(f"✅ Created .env file: {env_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀  Library Management System Setup")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        return 1

    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        print("Please run: pip install -r library_management/requirements.txt")
        return 1

    # Check database
    check_database()

    # Create .env file
    if not create_env_file():
        print("\n⚠️ Setup completed with warnings")
        return 0

    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n🚀 To start the application:")
    print("   Option 1: python start_server.py start")
    print("   Option 2: cd library_management && python run.py")
    print("\n🌐 Access the application at: http://localhost:5000")
    print("\n📖 For more information, see README.md")
    return 0

if __name__ == "__main__":
    sys.exit(main())
