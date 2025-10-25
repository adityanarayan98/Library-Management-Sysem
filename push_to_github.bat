@echo off
echo Library Management System - GitHub Push Script
echo =============================================

echo Step 1: Installing Git...
echo Please download and install Git from: https://git-scm.com/downloads
echo After installation, run this script again.

echo.
echo Step 2: After Git installation, run these commands:
echo.
echo cd "c:\Users\iitgn\OneDrive - iitgn.ac.in\Project\Own 2.0"
echo git init
echo git add .
echo git commit -m "Initial commit: Library Management System v2.0"
echo git remote add origin https://github.com/adityanarayan98/Library-Management-Sysem.git
echo git branch -M main
echo git push -u origin main
echo.
echo Step 3: If you encounter authentication issues, set up GitHub credentials:
echo git config --global user.name "Your Name"
echo git config --global user.email "your.email@example.com"
echo.
echo Then try pushing again.
echo.
pause
