# Library Management System

A comprehensive library management system built with Flask for personal use.

## 📁 Project Structure

```
📦 Library Management System
├── 📄 setup_first_time.bat      # First-time setup script
├── 📄 run_system.bat           # Regular system runner
├── 📁 development/             # Development environment
│   ├── 📁 data/                # Data files (library.db)
│   ├── 📁 backups/             # Database backups
│   ├── check_library.bat       # Library system checker
│   ├── build_current.bat       # Build script
│   ├── start_server.py         # Python server starter
│   └── library_management/     # Main Flask application
├── 📁 scripts/                 # Utility scripts
│   └── stop_library.bat        # Stop server script
├── 📁 distribution/            # Executable builds and deployment files
├── 📁 docs/                    # Documentation
│   ├── DOCUMENTATION.txt       # Technical documentation
│   ├── USER_GUIDE.txt          # User manual
│   ├── INSTALLATION_PLAN.txt   # Installation guide
│   └── github_upload_guide.txt # GitHub upload instructions
└── 📁 instance/                # Flask instance folder
```

## 🚀 Quick Start

### First Time Setup
```batch
setup_first_time.bat
```
This script will:
- Check Python installation
- Install dependencies
- Set up databases
- Create sample data
- Create initial backup

### Regular Usage
```batch
run_system.bat
```
This script will:
- Quick system check
- Create backup
- Start the server

### Development Access
For development, navigate to the development folder and run:
```bash
cd development
python start_server.py start
```

## 🌐 Access Information

- **Main Site**: http://localhost:5000
- **Dashboard**: http://localhost:5000/dashboard
- **Login**: http://localhost:5000/login

### Default Credentials
- **Username**: admin
- **Password**: admin123

## 🛠️ Development

### Development Tools Location
All development-related scripts are in the `development/` folder:
- `check_library.bat` - System health checker
- `build_current.bat` - Build tools
- `start_server.py` - Development server

### Utility Scripts
Utility scripts are in the `scripts/` folder:
- `stop_library.bat` - Stop the running server
- `cleanup_backups.bat` - Backup management utility

## 📚 Documentation

Complete documentation is available in the `docs/` folder:
- **DOCUMENTATION.txt** - Technical documentation
- **USER_GUIDE.txt** - User manual
- **INSTALLATION_PLAN.txt** - Installation instructions
- **github_upload_guide.txt** - GitHub deployment guide

## 🔧 Features

- **User Management**: Admin, staff, and patron roles
- **Book Management**: Catalog management with categories
- **Transaction Tracking**: Issue/return with fine calculation
- **Backup & Restore**: Complete system backup/restore
- **Bulk Operations**: Bulk upload for books and patrons
- **Reports**: Comprehensive reporting system
- **Settings**: Configurable library settings

## 💾 Backup Management

### Single Backup Location
All backups are now consolidated in the `development/backups/` folder for easy management:
- **No more confusion** about where to find backups
- **Centralized location** within development environment
- **Consistent naming** across all backup types

### Backup Types
- **Server Backups**: `library_backup_*.csv` (created on server start)
- **System Backups**: `system_backup_*.csv` (manual complete backups)
- **Manifest Files**: `system_backup_manifest.json` (backup metadata)

### Backup Management Utility
Use `scripts/cleanup_backups.bat` to manage backup files:
```batch
scripts/cleanup_backups.bat
```
Options:
- **View Statistics**: See backup count and total size
- **Remove Old Backups**: Delete backups older than 7 days
- **Keep Latest Only**: Retain only the 10 most recent backups
- **Interactive Menu**: Easy-to-use management interface

## 🛑 Stopping the Server

To stop the server, you can:
1. Press `Ctrl+C` in the terminal
2. Use `scripts/stop_library.bat`

## 📞 Support

For technical support or questions:
- Check the documentation in `docs/`
- Review the installation guide
- Check the user guide for usage instructions

## 📄 License

This project is for educational and personal use at IIT Gandhinagar.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## 📞 Support

For technical support or questions:
- Email: 
- Check the documentation in `docs/`
- Review the installation guide
- Check the user guide for usage instructions
