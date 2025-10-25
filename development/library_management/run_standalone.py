#!/usr/bin/env python3
"""
Standalone launcher for Library Management System
This script ensures the application runs correctly when packaged as .exe
"""

import os
import sys
import subprocess
import webbrowser
from threading import Timer

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        input("Press Enter to exit...")
        sys.exit(1)

def ensure_directories():
    """Ensure required directories exist"""
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as bundled .exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.abspath(__file__))

    directories = [
        os.path.join(base_dir, 'data'),  # Use 'data' for consistency with development
        os.path.join(base_dir, 'backups'),
        os.path.join(base_dir, 'templates')
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

    # For exe environment, change to exe directory so database path works
    if getattr(sys, 'frozen', False):
        os.chdir(base_dir)
        print(f"Changed working directory to: {base_dir}")

def open_browser():
    """Open web browser after a delay"""
    url = "http://localhost:5000"
    print(f"\nOpening web browser: {url}")
    webbrowser.open(url)

def main():
    """Main launcher function"""
    print("=" * 50)
    print("Library Management System")
    print("=" * 50)
    print("Starting the application...")
    print("Admin interface will open automatically at: http://localhost:5000 or http://[YOUR_IP]:5000")
    print("OPAC interface available at: http://localhost:5001 or http://[YOUR_IP]:5001")
    print("Using Gunicorn for better performance when available")
    print("Press Ctrl+C to stop both servers")
    print("-" * 50)

    # Check Python version
    check_python_version()

    # Ensure directories exist
    ensure_directories()

    # Set the working directory to the script location (only for development)
    if not getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)

    # Set environment variables for standalone mode
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'

    # Import and run the Flask app
    try:
        from app import create_app
        from run_opac import create_opac_app
        from app.database import Database
        from threading import Thread

        print("Creating and verifying database before starting servers...")
        # Create database instance to ensure database file exists
        db = Database()

        # Verify database connection
        if db.test_connection():
            print("✅ Database is ready!")
        else:
            print("❌ Database connection failed, but continuing...")

        # Create both apps
        full_app = create_app()
        opac_app = create_opac_app()

        def run_full_app():
            print("Starting full library management server on http://localhost:5000")
            try:
                from gunicorn.app.wsgiapp import WSGIApplication
                print("Using Gunicorn for better performance...")

                class StandaloneGunicornConfig:
                    bind = "0.0.0.0:5000"
                    workers = 2
                    worker_class = "sync"
                    timeout = 30
                    loglevel = "info"

                config = StandaloneGunicornConfig()
                WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]", config).run()

            except ImportError:
                print("Gunicorn not available, using Flask development server...")
                full_app.run(
                    host='0.0.0.0',
                    port=5000,
                    debug=False,
                    use_reloader=False
                )

        def run_opac_app():
            print("Starting OPAC server on http://localhost:5001")
            try:
                from gunicorn.app.wsgiapp import WSGIApplication
                print("Using Gunicorn for better performance...")

                class StandaloneGunicornConfig:
                    bind = "0.0.0.0:5001"
                    workers = 2
                    worker_class = "sync"
                    timeout = 30
                    loglevel = "info"

                config = StandaloneGunicornConfig()
                WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]", config).run()

            except ImportError:
                print("Gunicorn not available, using Flask development server...")
                opac_app.run(
                    host='0.0.0.0',
                    port=5001,
                    debug=False,
                    use_reloader=False
                )

        # Schedule browser opening after 3 seconds (open admin interface)
        Timer(3.0, open_browser).start()

        print("Database should be created and accessible now")
        print("-" * 50)
        print("Starting both servers...")
        print("Admin interface: http://localhost:5000 or http://[YOUR_IP]:5000")
        print("OPAC interface: http://localhost:5001 or http://[YOUR_IP]:5001")
        print("-" * 50)

        # Start both servers in separate threads
        full_thread = Thread(target=run_full_app)
        opac_thread = Thread(target=run_opac_app)

        full_thread.start()
        opac_thread.start()

        # Wait for both threads
        full_thread.join()
        opac_thread.join()

    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"ERROR: Failed to start application: {e}")
        print("Make sure all dependencies are installed")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    main()
