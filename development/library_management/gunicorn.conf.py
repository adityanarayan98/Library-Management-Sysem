# Gunicorn configuration for production
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "library_management"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (configure these for HTTPS)
keyfile = None
certfile = None

# Restart mechanism
preload_app = True
worker_tmp_dir = "/dev/shm"
