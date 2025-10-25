@echo off
echo ========================================
echo    Library System Status Check
echo ========================================
echo.

echo Checking server status...
netstat -an | findstr ":5000" >nul
if errorlevel 1 (
    echo ❌ Server is NOT running
    echo Run 'start_library.bat' to start the server
) else (
    echo ✅ Server is running on port 5000

    REM Get local IP address
    for /f "tokens=2 delims=[]" %%i in ('ping -4 %COMPUTERNAME% -n 1 2^>nul') do set SERVER_IP=%%i
    if defined SERVER_IP (
        echo    Access at: http://%SERVER_IP%:5000
        echo    Dashboard: http://%SERVER_IP%:5000/dashboard
    ) else (
        echo    Access at: http://localhost:5000
        echo    Dashboard: http://localhost:5000/dashboard
    )
)
echo.

echo Checking Python processes...
tasklist | findstr python >nul
if errorlevel 1 (
    echo ❌ No Python processes found
) else (
    echo ✅ Python processes are running
    tasklist | findstr python
)
echo.

echo Checking database backup status...
if exist "backups" (
    echo ✅ Backups folder exists
    dir /b /o-d backups\*.csv 2>nul | findstr . >nul
    if errorlevel 1 (
        echo ⚠️  No CSV backups found
    ) else (
        echo 📦 Recent backups:
        dir /b /o-d backups\*.csv 2>nul | head -5
    )
) else (
    echo ❌ Backups folder not found
)
echo.

echo Press any key to continue...
pause >nul
