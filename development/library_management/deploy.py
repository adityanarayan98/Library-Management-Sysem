#!/usr/bin/env python3
"""
Deployment script for the Enhanced Library Management System
"""

import os
import sys
import shutil
from pathlib import Path

def create_production_config():
    """Create production configuration files"""
    print("🔧 Creating production configuration...")

    # Create .env file for production
    env_content = """# Production Environment Variables
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-change-this-in-production
DATABASE_URL=sqlite:///instance/library.db
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print("✅ Created .env file")

    # Create gunicorn configuration
    gunicorn_config = """# Gunicorn configuration for production
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
"""

    with open('gunicorn.conf.py', 'w') as f:
        f.write(gunicorn_config)

    print("✅ Created gunicorn.conf.py")

def create_requirements_prod():
    """Create production requirements file"""
    print("📦 Creating production requirements...")

    prod_requirements = """Flask==2.3.3
Flask-Login==0.6.3
Flask-WTF==1.1.1
python-dotenv==1.0.0
Werkzeug==2.3.7
gunicorn==21.2.0
"""

    with open('requirements-prod.txt', 'w') as f:
        f.write(prod_requirements)

    print("✅ Created requirements-prod.txt")

def create_dockerfile():
    """Create Dockerfile for containerized deployment"""
    print("🐳 Creating Dockerfile...")

    dockerfile_content = """FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Create instance directory for SQLite
RUN mkdir -p instance

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "run.py"]
"""

    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)

    print("✅ Created Dockerfile")

def create_docker_compose():
    """Create docker-compose.yml for easy deployment"""
    print("🐳 Creating docker-compose.yml...")

    docker_compose_content = """version: '3.8'

services:
  library-management:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./instance:/app/instance
      - ./backups:/app/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Add a reverse proxy with SSL
  # nginx:
  #   image: nginx:alpine
  #   ports:
  #     - "80:80"
  #     - "443:443"
  #   volumes:
  #     - ./nginx.conf:/etc/nginx/nginx.conf
  #     - ./ssl:/etc/nginx/ssl
  #   depends_on:
  #     - library-management
"""

    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose_content)

    print("✅ Created docker-compose.yml")

def create_nginx_config():
    """Create nginx configuration for production"""
    print("🌐 Creating nginx configuration...")

    nginx_config = """upstream library_management {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name localhost;

    # Redirect HTTP to HTTPS (optional)
    # return 301 https://$server_name$request_uri;

    client_max_body_size 16M;

    location / {
        proxy_pass http://library_management;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Serve static files directly
    location /static {
        proxy_pass http://library_management/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# HTTPS configuration (uncomment and configure SSL certificates)
# server {
#     listen 443 ssl http2;
#     server_name localhost;
#
#     ssl_certificate /etc/nginx/ssl/cert.pem;
#     ssl_certificate_key /etc/nginx/ssl/key.pem;
#
#     # SSL Security settings
#     ssl_protocols TLSv1.2 TLSv1.3;
#     ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
#     ssl_prefer_server_ciphers off;
#
#     location / {
#         proxy_pass http://library_management;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }
# }
"""

    with open('nginx.conf', 'w') as f:
        f.write(nginx_config)

    print("✅ Created nginx.conf")

def create_deployment_script():
    """Create deployment script"""
    print("Creating deployment script...")

    deploy_script = """#!/bin/bash
# Deployment script for Library Management System

echo "Deploying Library Management System..."

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Pull latest images
echo "Pulling latest images..."
docker-compose pull

# Build and start containers
echo "Building and starting containers..."
docker-compose up -d --build

# Wait for application to be ready
echo "Waiting for application to be ready..."
sleep 10

# Check if application is running
if curl -f http://localhost:5000/ > /dev/null 2>&1; then
    echo "Deployment successful!"
    echo "Application is running at: http://localhost:5000"
    echo "Admin setup: http://localhost:5000/create_admin"
else
    echo "Deployment failed!"
    echo "Check logs: docker-compose logs"
    exit 1
fi
"""

    with open('deploy.sh', 'w') as f:
        f.write(deploy_script)

    # Make it executable
    os.chmod('deploy.sh', 0o755)

    print("Created deploy.sh")

def create_readme_deploy():
    """Create deployment README"""
    print("📚 Creating deployment documentation...")

    deploy_readme = """# Deployment Guide

## Local Deployment

### Using Python (Development)
```bash
pip install -r requirements.txt
python run.py
```

### Using Docker (Recommended for Production)
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use the deployment script
./deploy.sh
```

## Production Deployment Options

### 1. Docker Container
```bash
# Build the image
docker build -t library-management .

# Run the container
docker run -d \\
  --name library-management \\
  -p 5000:5000 \\
  -v $(pwd)/instance:/app/instance \\
  -v $(pwd)/backups:/app/backups \\
  library-management
```

### 2. Gunicorn + Nginx
```bash
# Install production dependencies
pip install -r requirements-prod.txt

# Start with Gunicorn
gunicorn --config gunicorn.conf.py run:app

# Or use Nginx as reverse proxy
# Configure nginx.conf and start nginx
```

### 3. Cloud Deployment

#### Heroku
```bash
# Create requirements.txt for Heroku
pip freeze > requirements.txt

# Create Procfile
echo "web: gunicorn --bind 0.0.0.0:$PORT run:app" > Procfile

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

#### AWS (EC2)
```bash
# Install Docker and Docker Compose on EC2 instance
# Copy the project files
# Run: docker-compose up -d
```

#### DigitalOcean App Platform
- Connect your Git repository
- Set build command: `pip install -r requirements-prod.txt`
- Set start command: `gunicorn --config gunicorn.conf.py run:app`

## Environment Variables

Create a `.env` file for production:
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/library.db
```

## Security Checklist

- [ ] Change the default SECRET_KEY
- [ ] Set up HTTPS in production
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Monitor application logs
- [ ] Update dependencies regularly

## Monitoring

### Health Check
The application includes a health check endpoint that can be used for monitoring.

### Logs
- Application logs: Check the console output
- Web server logs: Check nginx/gunicorn logs
- Database: SQLite doesn't require separate logging

## Backup Strategy

- Automated backups: Use the built-in backup feature
- Database backups: Copy `instance/library.db` regularly
- File backups: Backup the entire project directory

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port 5000
   lsof -i :5000
   # Kill the process or use different port
   python run.py --port=5001
   ```

2. **Database locked**
   ```bash
   # Delete and recreate database
   rm instance/library.db
   python run.py
   ```

3. **Permission errors**
   ```bash
   # Fix file permissions
   chmod 644 library_management/*
   chmod 755 run.py
   ```

### Getting Help

1. Check the application logs
2. Verify all dependencies are installed
3. Ensure Python 3.7+ is installed
4. Check file permissions
5. Verify database file exists and is writable

## Support

For deployment issues:
- Check the logs in the console
- Verify environment variables
- Ensure all ports are accessible
- Check firewall settings
"""

    with open('DEPLOYMENT.md', 'w') as f:
        f.write(deploy_readme)

    print("✅ Created DEPLOYMENT.md")

def main():
    """Main deployment setup function"""
    print("Setting up deployment configuration for Library Management System")
    print("=" * 60)

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    try:
        create_production_config()
        create_requirements_prod()
        create_dockerfile()
        create_docker_compose()
        create_nginx_config()
        create_deployment_script()
        create_readme_deploy()

        print("=" * 60)
        print("Deployment configuration completed successfully!")
        print()
        print("Next steps:")
        print("1. Review the generated configuration files")
        print("2. Update SECRET_KEY in .env file")
        print("3. Configure SSL certificates if needed")
        print("4. Deploy using: docker-compose up --build")
        print()
        print("Your application will be available at: http://localhost:5000")
        print("Admin setup: http://localhost:5000/create_admin")

    except Exception as e:
        print(f"Error during deployment setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
