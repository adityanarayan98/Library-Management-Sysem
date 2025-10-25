@echo off
echo Building Library Management System executable...
echo.

echo Step 1: Installing PyInstaller...
pip install pyinstaller

echo.
echo Step 2: Building executable...
cd library_management
pyinstaller library.spec

echo.
echo Build process completed!
echo.

echo Checking if executable was created...
if exist "dist\LibraryManagementSystem\LibraryManagementSystem.exe" (
    echo.
    echo SUCCESS! Your executable has been created:
    echo Location: library_management\dist\LibraryManagementSystem\LibraryManagementSystem.exe
    echo.
    echo You can now run your Library Management System by double-clicking the .exe file
    echo.
) else (
    echo.
    echo The executable was not found. Please check the build process.
    echo.
)

pause
