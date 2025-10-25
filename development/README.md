# Development Environment - Library Management System

This folder contains your active development environment for the Library Management System.

## 📁 Structure

```
development/
├── 📄 README.md                    (This file)
├── 📄 start_server.py              (Development server script)
├── 📄 run_server.bat               (Windows development launcher)
├── 📁 library_management/          (Main Flask application)
│   ├── 📁 app/                     (Application modules)
│   ├── 📁 templates/               (HTML templates)
│   ├── 📁 instance/                (Database and config)
│   └── [other app files]
└── 📁 instance/                    (Main database)
```

## 🚀 Quick Start (Development)

### Option 1: Quick Starter (Easiest) ⭐
```bash
# Just double-click this file:
quick_dev_start.bat
```

### Option 2: Python Script (Recommended)
```bash
cd development
python start_server.py start
```

### Option 3: Windows Batch
```bash
cd development
run_server.bat
```

### Option 4: Direct Flask
```bash
cd development/library_management
python run.py
```

## 🌐 Access URLs

### Development Servers
- **Admin Interface** (Librarians): http://localhost:5000 or http://[YOUR_IP]:5000
- **OPAC Interface** (Patrons): http://localhost:5001 or http://[YOUR_IP]:5001
- **Dashboard**: http://localhost:5000/dashboard
- **Login**: http://localhost:5000/login

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

## 🌐 Network Access

Your development environment supports network access:

- **Local Testing**: Use localhost URLs for local development
- **Network Testing**: Use [YOUR_IP] URLs to test from other devices
- **Role-Based Access**: Separate interfaces for different user types
- **Shared Database**: Both interfaces use the same database

## 💾 Database

Your development database is located at:
- `development/instance/library.db` (main database)
- `development/library_management/app/instance/` (app-specific data)

## 🔧 Development Features

- ✅ **Hot Reload** - Code changes restart server automatically
- ✅ **Debug Mode** - Detailed error messages and logging
- ✅ **Your Data** - All your existing data preserved
- ✅ **Real-time Testing** - Test changes instantly

## 📝 What You Can Do Here

### Development Work
- Modify application code in `library_management/`
- Test new features with your existing data
- Debug and troubleshoot issues
- Add new functionality

### Database Operations
- Your existing data is preserved and active
- All patron, book, and transaction records available
- Settings and configurations maintained

## 🚨 Important Notes

- **Never delete** this folder - it contains your active development work
- **Backup regularly** - Contains your valuable data and code
- **Version control** - Consider using Git for code management

## 🔄 Workflow

1. **Make changes** in `library_management/` files
2. **Test immediately** - Server auto-reloads with changes
3. **Verify functionality** with your existing data
4. **Debug if needed** - Full debug information available

---

## 🎯 **Your Active Development Environment**

This is where you continue your Library Management System development with all your existing data and latest code changes!

**Ready to develop!** 🚀
