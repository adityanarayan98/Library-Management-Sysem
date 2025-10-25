@echo off
echo ========================================
echo    Stopping Library System
echo ========================================
echo.

echo Stopping Flask server on port 5000...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000"') do (
    echo Killing process %%p...
    taskkill /PID %%p /F >nul 2>&1
    if errorlevel 1 (
        echo ❌ Failed to kill process %%p
    ) else (
        echo ✅ Process %%p killed successfully
    )
)

REM Also try to kill any Python processes that might be the server
echo.
echo Stopping any Python processes...
taskkill /IM python.exe /F >nul 2>&1
if errorlevel 1 (
    echo No Python processes found to kill
) else (
    echo ✅ Python processes stopped
)

echo.
echo Checking if port 5000 is now free...
netstat -an | findstr ":5000" >nul
if errorlevel 1 (
    echo ✅ Port 5000 is now free
) else (
    echo ⚠️  Port 5000 may still be in use
    netstat -an | findstr ":5000"
)

echo.
echo Library Management System has been stopped.
echo Use 'start_library.bat' to start it again.
echo.
pause
