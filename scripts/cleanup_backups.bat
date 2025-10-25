@echo off
echo ========================================
echo    Backup Cleanup Utility
echo ========================================
echo.

set PROJECT_DIR=%~dp0..
cd /d "%PROJECT_DIR%" || (
    echo ERROR: Cannot enter project folder %PROJECT_DIR%
    pause
    exit /b
)

echo Checking backup folder...
if not exist "backups" (
    echo No backups folder found.
    pause
    exit /b
)

echo.
echo Current backup files:
dir /b "backups" 2>nul | findstr /c:".csv" /c:".json" || echo No backup files found.

echo.
echo This utility will help you manage backup files.
echo Options:
echo 1. Show backup statistics
echo 2. Remove backups older than 7 days
echo 3. Keep only latest 10 backups
echo 4. Exit
echo.

:menu
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto show_stats
if "%choice%"=="2" goto remove_old
if "%choice%"=="3" goto keep_latest
if "%choice%"=="4" goto exit

echo Invalid choice. Please try again.
goto menu

:show_stats
echo.
echo ========================================
echo Backup Statistics:
echo ========================================
echo.

set backup_count=0
for %%f in ("backups\*.csv" "backups\*.json") do (
    set /a backup_count+=1
)

echo Total backup files: %backup_count%

REM Calculate total size
set total_size=0
for %%f in ("backups\*.csv" "backups\*.json") do (
    for %%s in (%%f) do set /a total_size+=%%~zs
)

if %total_size% lss 1048576 (
    echo Total size: %total_size% bytes
) else (
    set /a size_mb=%total_size%/1048576
    echo Total size: %size_mb% MB
)

echo.
echo Oldest backup files:
for /f "tokens=*" %%f in ('dir /b /o:d "backups\*.csv" "backups\*.json" 2^>nul') do echo %%f
echo.
pause
goto menu

:remove_old
echo.
echo Removing backups older than 7 days...
forfiles /p "backups" /m "*.csv" /m "*.json" /d -7 /c "cmd /c del @path" 2>nul
forfiles /p "backups" /m "*.csv" /m "*.json" /d -7 /c "cmd /c del @path" 2>nul
echo Cleanup completed.
echo.
pause
goto menu

:keep_latest
echo.
echo Keeping only the latest 10 backups...
echo This will remove older backup files.

REM Get list of files sorted by date (newest first)
set file_list=
for /f "tokens=*" %%f in ('dir /b /o:-d "backups\*.csv" "backups\*.json" 2^>nul') do (
    set file_list=!file_list! "%%f"
)

REM Count files and remove older ones
set count=0
for %%f in (!file_list!) do (
    set /a count+=1
    if !count! gtr 10 (
        echo Removing: %%f
        del "backups\%%f" 2>nul
    )
)
echo Cleanup completed.
echo.
pause
goto menu

:exit
echo Goodbye!
