@echo off
echo ========================================
echo    Library Management System
echo       FIRST-TIME SETUP
echo ========================================
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%" || (
    echo ERROR: Cannot enter project folder %PROJECT_DIR%
    pause
    exit /b
)

echo [1/6] Checking Python installation...
python --version >nul 2>&1 || (
    echo ❌ ERROR: Python not found
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found
echo.

echo [2/6] Checking pip installation...
pip --version >nul 2>&1 || (
    echo ❌ ERROR: pip not found
    echo Please install pip for Python package management
    pause
    exit /b
)
for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
echo ✅ pip %PIP_VERSION% found
echo.

echo [3/6] Installing/updating dependencies...
echo Installing required packages...
pip install -r development/library_management/requirements.txt
if errorlevel 1 (
    echo ⚠️  WARNING: Some packages may have failed to install
    echo You may need to check your internet connection
    echo Continuing with setup...
) else (
    echo ✅ Dependencies installed successfully
)
echo.

echo [4/6] Checking databases...
python development/check_databases.py
if errorlevel 1 (
    echo ⚠️  WARNING: Database check had issues
    echo Continuing with setup...
) else (
    echo ✅ Database check completed
)
echo.

echo [5/6] Setting up sample data...
echo Creating sample books, patrons, and admin user...
python development/add_sample_data.py
if errorlevel 1 (
    echo ⚠️  WARNING: Could not add sample data
    echo You can still use the system, but you'll need to add data manually
) else (
    echo ✅ Sample data added successfully
)
echo.

echo [6/6] Creating initial backup...
python development/start_server.py backup
if errorlevel 1 (
    echo ⚠️  WARNING: Backup creation failed
) else (
    echo ✅ Initial backup created
)
echo.

echo ========================================
echo ✅ SETUP COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Your Library Management System is ready!
echo.
echo Default admin credentials:
echo - Username: admin
echo - Password: admin123
echo.
echo Next steps:
echo 1. Run 'run_system.bat' to start the system
echo 2. Access at http://localhost:5000
echo 3. Login with admin credentials above
echo.
echo ========================================
echo Setup log saved. Check for any warnings above.
pause
