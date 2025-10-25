@echo off
echo ========================================
echo Library Management System - Installer Builder
echo ========================================
echo.
echo This script will create a professional Windows installer (.exe) for your
echo Library Management System that behaves like other Windows applications.
echo.
echo The installer will provide:
echo - Professional installation wizard
echo - Desktop and Start Menu shortcuts
echo - Uninstall capability from Control Panel
echo - Proper Windows integration
echo.

pause

echo.
echo ========================================
echo STEP 1: Building PyInstaller executable...
echo ========================================

echo.
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo.
echo Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo Building the standalone executable...
echo This may take several minutes...
cd ..\development\library_management
pyinstaller ..\..\distribution\exe_builder\standalone_exe\library.spec --clean
if errorlevel 1 (
    echo ERROR: Failed to build executable
    echo Check the error messages above
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo PyInstaller executable built successfully!
echo.

echo.
echo ========================================
echo STEP 2: Installing NSIS (if needed)...
echo ========================================

echo.
echo Checking for NSIS installation...
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo NSIS found at: C:\Program Files (x86)\NSIS\makensis.exe
    set "NSIS_PATH=C:\Program Files (x86)\NSIS"
) else if exist "C:\Program Files\NSIS\makensis.exe" (
    echo NSIS found at: C:\Program Files\NSIS\makensis.exe
    set "NSIS_PATH=C:\Program Files\NSIS"
) else (
    echo NSIS not found. Downloading and installing NSIS...
    echo.

    echo Downloading NSIS...
    curl -L -o nsis.exe "https://downloads.sourceforge.net/project/nsis/NSIS%203/3.08/nsis-3.08-setup.exe"

    if errorlevel 1 (
        echo ERROR: Failed to download NSIS
        echo Please download and install NSIS manually from:
        echo https://nsis.sourceforge.net/Download
        pause
        exit /b 1
    )

    echo.
    echo Installing NSIS...
    echo NOTE: This will open the NSIS installer. Please complete the installation.
    pause

    start /wait nsis.exe /S

    if errorlevel 1 (
        echo ERROR: NSIS installation failed
        pause
        exit /b 1
    )

    echo.
    echo NSIS installed successfully!
    set "NSIS_PATH=C:\Program Files\NSIS"
)

echo.
echo ========================================
echo STEP 3: Creating Windows Installer...
echo ========================================

echo.
echo Creating the installer package...
echo This will create: LibraryManagementSystem-Setup.exe

"%NSIS_PATH%\makensis.exe" distribution\exe_builder\installer\installer.nsi
if errorlevel 1 (
    echo ERROR: Failed to create installer
    echo Check that NSIS is properly installed
    pause
    exit /b 1
)

echo.
echo ========================================
echo STEP 4: Finalizing...
echo ========================================

echo.
echo Moving installer to project root...
move "LibraryManagementSystem-Setup.exe" "." 2>nul

echo.
echo ========================================
echo INSTALLER CREATION COMPLETE!
echo ========================================
echo.
echo Your professional Windows installer has been created!
echo.
echo Installer file: LibraryManagementSystem-Setup.exe
echo Size: Check file size in Windows Explorer
echo.
echo ========================================
echo.
echo TO DISTRIBUTE YOUR APPLICATION:
echo.
echo 1. Share the file: LibraryManagementSystem-Setup.exe
echo.
echo 2. Users install it by:
echo    - Double-clicking the installer
echo    - Following the installation wizard
echo    - Choosing installation directory
echo    - Accepting the license agreement
echo.
echo 3. After installation:
echo    - Desktop shortcut will be created
echo    - Start Menu entry will be added
echo    - Can be uninstalled from Control Panel
echo.
echo 4. To run the application:
echo    - Double-click desktop shortcut, OR
echo    - Go to Start Menu > Library Management System
echo    - Web interface opens at http://localhost:5000
echo.
echo ========================================
echo.
echo The installer includes:
echo - Professional installation wizard
echo - Desktop and Start Menu shortcuts
echo - Windows registry integration
echo - Clean uninstall capability
echo - All dependencies bundled
echo - Complete Library Management System
echo.
echo ========================================
echo.

pause
