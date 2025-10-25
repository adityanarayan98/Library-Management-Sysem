@echo off
title Library Management System
echo Starting Library Management System...
echo.
echo Admin interface will open at: http://localhost:5000 or http://[YOUR_IP]:5000
echo OPAC interface available at: http://localhost:5001 or http://[YOUR_IP]:5001
echo.
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
start /b "%~dp0\standalone_exe\dist\LibraryManagementSystem.exe"
echo.
echo Server is running...
pause
