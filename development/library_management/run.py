#!/usr/bin/env python3
"""
Enhanced Library Management System
A modern web-based library management system built with Flask and SQLite
"""

import sys
import os
# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
import os

app = create_app()

# Remove OPAC blueprints for admin-only interface
opac_blueprints = ['opac', 'patron_auth']
app.blueprints = {k: v for k, v in app.blueprints.items() if k not in opac_blueprints}

if __name__ == '__main__':
    # Create instance folder if it doesn't exist
    os.makedirs('instance', exist_ok=True)

    # Run the application
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
