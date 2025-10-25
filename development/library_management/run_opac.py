#!/usr/bin/env python3
"""
OPAC (Online Public Access Catalog) Server
Public interface for library catalog access
"""

import sys
import os
import webbrowser
from threading import Timer

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, redirect, url_for
from app.db import db
from app.routes.opac import opac_bp
from app.routes.patron_auth import patron_auth_bp

def open_browser():
    """Open web browser after a delay"""
    url = "http://localhost:5001"
    print(f"\nOpening web browser: {url}")
    webbrowser.open(url)

def create_opac_app():
    """Create OPAC-only application"""
    app = Flask(__name__, template_folder='templates')

    # Configuration
    app.config['SECRET_KEY'] = 'opac-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False

    # Database path
    if getattr(sys, 'frozen', False):
        db_path = os.path.join(os.getcwd(), 'data', 'library.db')
    else:
        basedir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(basedir, 'development', 'data', 'library.db')

    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Register only OPAC blueprints
    app.register_blueprint(opac_bp)
    app.register_blueprint(patron_auth_bp)

    # Override the root route to go to OPAC
    @app.route('/')
    def index():
        return redirect(url_for('opac.opac_home'))

    return app

app = create_opac_app()

if __name__ == '__main__':
    # Create instance folder if it doesn't exist
    os.makedirs('instance', exist_ok=True)

    # Schedule browser opening
    Timer(3.0, open_browser).start()

    print("=" * 50)
    print("Library Management System - OPAC")
    print("=" * 50)
    print("Starting OPAC server...")
    print("The web interface will open automatically at: http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    # Run the application
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
