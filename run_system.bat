@echo off
echo ========================================
echo    Library Management System
echo ========================================
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%" || (
    echo ERROR: Cannot enter project folder %PROJECT_DIR%
    pause
    exit /b
)

echo [1/2 Quick system check...
python --version >nul 2>&1 || (
    echo ❌ ERROR: Python not found
    echo Please run 'setup_first_time.bat' first
    pause
    exit /b
)
echo ✅ Python available
echo.


echo [2/2 Starting Library Management System...
echo ========================================
echo Server starting...
echo.
echo Access URLs:
echo - Main Site: http://localhost:5000
echo - Dashboard: http://localhost:5000/dashboard
echo - Login: http://localhost:5000/login
echo.
echo Default Credentials:
echo - Username: admin
echo - Password: admin123
echo.
echo Press Ctrl+C to stop the server
echo ========================================

python development/start_server.py start

echo.
echo ========================================
echo Server stopped.
echo ========================================
pause
