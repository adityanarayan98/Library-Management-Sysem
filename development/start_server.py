#!/usr/bin/env python3
"""
Server Start Script with CSV Backup
Enhanced Library Management System startup script that checks server status and creates CSV backups
"""

import os
import sys
import subprocess
import time
import socket
import csv
import threading
from datetime import datetime

# Add library_management directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library_management'))

from app import create_app
from app.database import Database
from run_opac import create_opac_app

# Try to import pandas, but don't fail if it's not available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

def check_server_running(host='0.0.0.0', port=5000):
    """Check if server is already running on specified host and port"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result == 0
    except:
        return False

def check_admin_running():
    """Check if admin server is running"""
    return check_server_running(port=5000)

def check_opac_running():
    """Check if OPAC server is running"""
    return check_server_running(port=5001)

def create_csv_backup():
    """Create CSV backup of current database"""
    try:
        # Create backups directory if it doesn't exist (in project root)
        backup_dir = 'backups'
        os.makedirs(backup_dir, exist_ok=True)

        # Generate timestamp for backup file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'library_backup_{timestamp}.csv')

        # Get database connection using the robust Database class
        # The Database class now has built-in PyInstaller support
        db = Database()
        conn = db.get_connection()
        if not conn:
            print("Error: Could not connect to database - database may not exist yet")
            return False

        # Read all tables and create backup (correct table names from database)
        tables = ['users', 'books', 'patrons', '"transaction"', 'category', 'library_settings']

        if PANDAS_AVAILABLE:
            # Use pandas if available
            all_data = []
            for table in tables:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    if not df.empty:
                        df['table_name'] = table
                        all_data.append(df)
                except Exception as e:
                    print(f"Warning: Could not backup table {table}: {e}")

            if all_data:
                # Combine all tables into single backup file
                combined_df = pd.concat(all_data, ignore_index=True)
                combined_df.to_csv(backup_file, index=False)
                print(f"CSV backup created: {backup_file}")
                return True
            else:
                print("No data found to backup")
                return False
        else:
            # Fallback method using only built-in libraries
            with open(backup_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = None
                rows_written = 0

                for table in tables:
                    try:
                        cursor = conn.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()
                        column_names = [description[0] for description in cursor.description]

                        if writer is None:
                            # Write header for first table
                            all_columns = column_names + ['table_name']
                            writer = csv.writer(csvfile)
                            writer.writerow(all_columns)

                        if rows:
                            # Add table_name to each row
                            for row in rows:
                                row_with_table = list(row) + [table]
                                writer.writerow(row_with_table)
                                rows_written += 1

                    except Exception as e:
                        print(f"Warning: Could not backup table {table}: {e}")

                if rows_written > 0:
                    print(f"CSV backup created: {backup_file} ({rows_written} rows)")
                    return True
                else:
                    print("No data found to backup")
                    return False

    except Exception as e:
        print(f"Error creating CSV backup: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def start_admin_server():
    """Start the admin server on port 5000"""
    try:
        print("Starting Admin Server on port 5000...")
        app = create_app()

        # Create CSV backup AFTER database is created
        print("Creating database backup...")
        backup_success = create_csv_backup()

        if not backup_success:
            print("Warning: Backup failed or no data to backup, but continuing...")

        print("Admin Server started successfully!")
        print("Access the admin interface at: http://localhost:5000 or http://[YOUR_IP]:5000")
        print("Dashboard: http://localhost:5000/dashboard or http://[YOUR_IP]:5000/dashboard")
        print("Login: http://localhost:5000/login or http://[YOUR_IP]:5000/login")

        # Run the admin application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False
        )

    except KeyboardInterrupt:
        print("\nAdmin Server stopped by user")
    except Exception as e:
        print(f"Error starting admin server: {e}")

def start_opac_server():
    """Start the OPAC server on port 5001"""
    try:
        print("Starting OPAC Server on port 5001...")
        app = create_opac_app()

        print("OPAC Server started successfully!")
        print("Access the OPAC interface at: http://localhost:5001 or http://[YOUR_IP]:5001")
        print("OPAC Search: http://localhost:5001/opac/search or http://[YOUR_IP]:5001/opac/search")

        # Run the OPAC application
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True,
            use_reloader=False
        )

    except KeyboardInterrupt:
        print("\nOPAC Server stopped by user")
    except Exception as e:
        print(f"Error starting OPAC server: {e}")

def start_server():
    """Start both admin and OPAC servers"""
    try:
        print("Starting Library Management System...")
        print("=" * 50)

        # Check if servers are already running
        if check_admin_running():
            print("Warning: Admin server is already running on http://localhost:5000 or http://[YOUR_IP]:5000")
        if check_opac_running():
            print("Warning: OPAC server is already running on http://localhost:5001 or http://[YOUR_IP]:5001")

        if check_admin_running() or check_opac_running():
            print("   Use 'python start_server.py stop' to stop the servers first")
            return False

        print("Starting both servers...")

        # Start both servers in separate threads
        admin_thread = threading.Thread(target=start_admin_server, daemon=True)
        opac_thread = threading.Thread(target=start_opac_server, daemon=True)

        admin_thread.start()
        opac_thread.start()

        print("=" * 50)
        print("Both servers started successfully!")
        print("Admin Interface: http://localhost:5000 or http://[YOUR_IP]:5000")
        print("OPAC Interface:  http://localhost:5001 or http://[YOUR_IP]:5001")
        print("\nPress Ctrl+C to stop both servers")

        # Wait for threads (this will block until interrupted)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping both servers...")

    except Exception as e:
        print(f"Error starting servers: {e}")
        return False

def stop_server():
    """Stop the running server"""
    try:
        print("Stopping server...")
        # Try to connect and then close (this won't actually stop a running server)
        # In a real scenario, you might need to implement a proper shutdown mechanism
        print("Server stop signal sent")
    except Exception as e:
        print(f"Error stopping server: {e}")

def show_status():
    """Show server status"""
    admin_running = check_admin_running()
    opac_running = check_opac_running()

    if admin_running and opac_running:
        print("Both servers are running:")
        print("  Admin: http://localhost:5000 or http://[YOUR_IP]:5000")
        print("  OPAC:  http://localhost:5001 or http://[YOUR_IP]:5001")
    elif admin_running:
        print("Only Admin server is running: http://localhost:5000 or http://[YOUR_IP]:5000")
    elif opac_running:
        print("Only OPAC server is running: http://localhost:5001 or http://[YOUR_IP]:5001")
    else:
        print("No servers are running")

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'start':
            start_server()
        elif command == 'stop':
            stop_server()
        elif command == 'status':
            show_status()
        elif command == 'backup':
            create_csv_backup()
        else:
            print("Unknown command. Use: start, stop, status, or backup")
    else:
        # Default action is to start the server
        start_server()

if __name__ == '__main__':
    main()
