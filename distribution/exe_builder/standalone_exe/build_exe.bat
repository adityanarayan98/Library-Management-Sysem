@echo off
echo ========================================
echo Library Management System - EXE Builder
echo ========================================
echo.

echo This script will package your Library Management System into a standalone .exe file
echo that can run on any Windows computer without requiring Python installation.
echo.

pause

echo.
echo Step 1: Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo.
echo Step 2: Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo Step 3: Building the executable...
echo This may take several minutes...
pyinstaller library.spec --clean
if errorlevel 1 (
    echo ERROR: Failed to build executable
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo Step 4: Creating launcher script...
cd ..
echo @echo off > "Library Management System.exe.bat"
echo title Library Management System >> "Library Management System.exe.bat"
echo echo Starting Library Management System... >> "Library Management System.exe.bat"
echo echo. >> "Library Management System.exe.bat"
echo echo The web interface will open at: http://localhost:5001 >> "Library Management System.exe.bat"
echo echo. >> "Library Management System.exe.bat"
echo echo Press Ctrl+C to stop the server >> "Library Management System.exe.bat"
echo echo. >> "Library Management System.exe.bat"
echo cd /d "%%~dp0" >> "Library Management System.exe.bat"
echo start /b "%%~dp0\library_management\dist\LibraryManagementSystem\LibraryManagementSystem.exe" >> "Library Management System.exe.bat"
echo echo. >> "Library Management System.exe.bat"
echo echo Server is running... >> "Library Management System.exe.bat"
echo pause >> "Library Management System.exe.bat"

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Your executable has been created successfully!
echo.
echo Location: library_management\dist\LibraryManagementSystem\
echo Main file: LibraryManagementSystem.exe
echo.
echo To run the application:
echo 1. Double-click: "Library Management System.exe.bat"
echo    OR
echo 2. Run: library_management\dist\LibraryManagementSystem\LibraryManagementSystem.exe
echo.
echo The web interface will be available at: http://localhost:5001
echo.
echo ========================================
echo.

pause
