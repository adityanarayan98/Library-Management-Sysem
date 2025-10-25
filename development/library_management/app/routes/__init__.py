"""
Route blueprints package for the Library Management System
"""

from .core import core_bp
from .patrons import patrons_bp
from .books import books_bp
from .transactions import transactions_bp
from .backup import backup_bp
from .settings import settings_bp

__all__ = ['core_bp', 'patrons_bp', 'books_bp', 'transactions_bp', 'backup_bp', 'settings_bp']
