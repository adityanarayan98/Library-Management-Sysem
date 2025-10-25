# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller configuration for Library Management System
Creates a standalone .exe file that can run on any Windows computer
"""

import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(SPEC))
sys.path.insert(0, current_dir)

block_cipher = None

# Define the main application files to include
app_files = [
    (os.path.join(current_dir, '..', '..', '..', 'development', 'library_management', 'run.py'), '.'),
    (os.path.join(current_dir, '..', '..', '..', 'development', 'library_management', 'app'), 'app'),
    (os.path.join(current_dir, '..', '..', '..', 'development', 'library_management', 'instance'), 'instance'),  # Database files (created at runtime)
    (os.path.join(current_dir, '..', '..', '..', 'development', 'library_management', 'backups'), 'backups'),    # Backup files (created at runtime)
]

# Define hidden imports that PyInstaller might miss
# Only include dependencies that are actually used
hidden_imports = [
    'flask',
    'flask_login',
    'flask_wtf',
    'flask_sqlalchemy',
    'werkzeug',
    'wtforms',
    'sqlalchemy',
    'sqlite3',
    'werkzeug.security',
    'werkzeug.utils',
    'sqlalchemy.orm',
    'wtforms.fields',
    'wtforms.widgets',
    'wtforms.validators',
    'flask_wtf.csrf',
]

# Define data files to include (templates, static files, etc.)
data_files = [
    (os.path.join(current_dir, '..', '..', '..', 'development', 'library_management', 'templates'), 'templates'),
    (os.path.join(current_dir, '..', '..', '..', 'development', 'library_management', 'app.manifest'), '.'),
]

# Create the Analysis object
a = Analysis(
    [os.path.join(current_dir, '..', '..', '..', 'development', 'library_management', 'run_standalone.py')],  # Main script to package
    pathex=[current_dir],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create the PYZ object (pure Python modules)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create the EXE object
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LibraryManagementSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress the executable
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console window for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='library_icon.ico',  # Professional library icon
)

# Single file mode - no COLLECT object needed
# This creates a single .exe file with everything embedded
