# Deployment Guide

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
docker run -d \
  --name library-management \
  -p 5000:5000 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/backups:/app/backups \
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
