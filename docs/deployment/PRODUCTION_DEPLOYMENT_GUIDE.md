# AI Karen - Production Deployment Guide

This comprehensive guide covers the deployment of AI Karen to a production environment, including all necessary configuration, security, and monitoring setup.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Setup](#environment-setup)
4. [Database Configuration](#database-configuration)
5. [Security Configuration](#security-configuration)
6. [SSL/TLS Setup](#ssltls-setup)
7. [Application Deployment](#application-deployment)
8. [Monitoring Setup](#monitoring-setup)
9. [Backup Configuration](#backup-configuration)
10. [Post-Deployment Verification](#post-deployment-verification)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04 LTS or newer, CentOS 8+, or RHEL 8+
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Memory**: Minimum 8GB RAM, Recommended 16GB+ RAM
- **Storage**: Minimum 100GB SSD, Recommended 500GB+ SSD
- **Network**: Static IP address, Domain name with DNS configured

### Software Dependencies

- **Python**: 3.11 or newer
- **Node.js**: 18.x or newer
- **PostgreSQL**: 14.x or newer
- **Redis**: 6.x or newer
- **Milvus**: 2.3.x or newer
- **Docker**: 24.x or newer (optional but recommended)
- **Nginx**: 1.20+ (for reverse proxy)

### External Services

- **SSL Certificate**: Valid SSL certificate for your domain
- **Email Service**: SMTP server or email service provider
- **Monitoring**: Prometheus and Grafana (optional)
- **Backup Storage**: S3-compatible storage or local backup solution

## Pre-Deployment Checklist

### Security Checklist

- [ ] SSL certificate obtained and validated
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] SSH key-based authentication enabled
- [ ] Root login disabled
- [ ] Fail2ban installed and configured
- [ ] System updates applied
- [ ] Security patches installed

### Configuration Checklist

- [ ] Domain name configured and DNS propagated
- [ ] Database server prepared and secured
- [ ] Redis server configured
- [ ] Milvus vector database setup
- [ ] Email service configured
- [ ] Backup storage prepared
- [ ] Monitoring infrastructure ready

### Application Checklist

- [ ] Production configuration files prepared
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Application dependencies installed
- [ ] Build process verified
- [ ] Health checks implemented

## Environment Setup

### 1. Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash ai-karen
sudo usermod -aG sudo ai-karen

# Switch to application user
sudo su - ai-karen
```

### 2. Directory Structure

```bash
# Create application directories
mkdir -p /opt/ai-karen/{app,logs,backups,config,data}
mkdir -p /var/log/ai-karen
mkdir -p /etc/ai-karen

# Set proper permissions
sudo chown -R ai-karen:ai-karen /opt/ai-karen
sudo chown -R ai-karen:ai-karen /var/log/ai-karen
sudo chown -R ai-karen:ai-karen /etc/ai-karen
```

### 3. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nodejs \
    npm \
    postgresql-client \
    redis-tools \
    nginx \
    certbot \
    python3-certbot-nginx \
    fail2ban \
    ufw \
    htop \
    curl \
    wget \
    git
```

## Database Configuration

### PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE ai_karen_prod;
CREATE USER ai_karen_user WITH ENCRYPTED PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ai_karen_prod TO ai_karen_user;
ALTER USER ai_karen_user CREATEDB;
\q
EOF

# Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf
```

**PostgreSQL Configuration (`postgresql.conf`):**

```ini
# Connection settings
listen_addresses = 'localhost'
port = 5432
max_connections = 100

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_messages = warning
log_min_error_statement = error

# Security
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

### Redis Setup

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
```

**Redis Configuration:**

```ini
# Network
bind 127.0.0.1
port 6379
protected-mode yes

# Security
requirepass your_redis_password_here

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

### Milvus Setup

```bash
# Install Milvus using Docker Compose
curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
bash standalone_embed.sh start
```

## Security Configuration

### 1. Firewall Setup

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Fail2ban Configuration

```bash
# Configure Fail2ban
sudo nano /etc/fail2ban/jail.local
```

**Fail2ban Configuration:**

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
```

### 3. SSH Hardening

```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config
```

**SSH Configuration:**

```ini
Port 22
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

## SSL/TLS Setup

### 1. Obtain SSL Certificate

```bash
# Using Let's Encrypt
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Or using existing certificate
sudo cp your-certificate.crt /etc/ssl/certs/ai-karen.crt
sudo cp your-private-key.key /etc/ssl/private/ai-karen.key
sudo chmod 600 /etc/ssl/private/ai-karen.key
```

### 2. Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/ai-karen
```

**Nginx Configuration:**

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'; font-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none';" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Backend API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Auth endpoints with stricter rate limiting
    location /api/auth/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/ai-karen/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/ai-karen /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Application Deployment

### 1. Clone and Setup Application

```bash
# Clone the repository
cd /opt/ai-karen
git clone https://github.com/your-org/ai-karen.git app
cd app

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy production configuration
cp config/production.env .env

# Edit configuration for your environment
nano .env
```

**Critical Environment Variables to Update:**

```bash
# Domain and URLs
KAREN_BACKEND_URL=https://api.your-domain.com
NEXT_PUBLIC_KAREN_BACKEND_URL=https://api.your-domain.com
NEXT_PUBLIC_BASE_URL=https://your-domain.com

# Security (CHANGE THESE!)
AUTH_SECRET_KEY=your_secure_random_string_64_chars_minimum
JWT_SECRET_KEY=your_secure_random_string_64_chars_minimum

# Database
AUTH_DATABASE_URL=postgresql+asyncpg://ai_karen_user:your_secure_password@localhost:5432/ai_karen_prod

# MinIO/S3
MINIO_ACCESS_KEY=your_production_access_key
MINIO_SECRET_KEY=your_production_secret_key

# Email
SMTP_HOST=smtp.your-email-provider.com
SMTP_USER=your-email@your-domain.com
SMTP_PASSWORD=your_email_password
EMAIL_FROM=noreply@your-domain.com

# SSL
SSL_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 3. Database Migration

```bash
# Run database migrations
source venv/bin/activate
python -m alembic upgrade head

# Create initial admin user (if needed)
python scripts/create_admin_user.py
```

### 4. Build Frontend

```bash
# Install Node.js dependencies
cd ui_launchers/web_ui
npm install

# Build for production
npm run build

# Return to app root
cd ../..
```

### 5. Create Systemd Services

**Backend Service (`/etc/systemd/system/ai-karen-backend.service`):**

```ini
[Unit]
Description=AI Karen Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=ai-karen
Group=ai-karen
WorkingDirectory=/opt/ai-karen/app
Environment=PATH=/opt/ai-karen/app/venv/bin
ExecStart=/opt/ai-karen/app/venv/bin/python start.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-karen-backend

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/ai-karen /var/log/ai-karen

[Install]
WantedBy=multi-user.target
```

**Frontend Service (`/etc/systemd/system/ai-karen-frontend.service`):**

```ini
[Unit]
Description=AI Karen Frontend Service
After=network.target ai-karen-backend.service

[Service]
Type=exec
User=ai-karen
Group=ai-karen
WorkingDirectory=/opt/ai-karen/app/ui_launchers/web_ui
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-karen-frontend

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

### 6. Start Services

```bash
# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable ai-karen-backend ai-karen-frontend
sudo systemctl start ai-karen-backend ai-karen-frontend

# Check status
sudo systemctl status ai-karen-backend ai-karen-frontend
```

## Monitoring Setup

### 1. Log Rotation

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/ai-karen
```

**Logrotate Configuration:**

```
/var/log/ai-karen/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ai-karen ai-karen
    postrotate
        systemctl reload ai-karen-backend ai-karen-frontend
    endscript
}
```

### 2. Health Check Script

```bash
# Create health check script
sudo nano /opt/ai-karen/scripts/health_check.sh
```

**Health Check Script:**

```bash
#!/bin/bash

# Health check script for AI Karen
BACKEND_URL="http://localhost:8000/api/health"
FRONTEND_URL="http://localhost:3000"
LOG_FILE="/var/log/ai-karen/health_check.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check backend health
if curl -f -s "$BACKEND_URL" > /dev/null; then
    log_message "Backend health check: OK"
    backend_status=0
else
    log_message "Backend health check: FAILED"
    backend_status=1
fi

# Check frontend health
if curl -f -s "$FRONTEND_URL" > /dev/null; then
    log_message "Frontend health check: OK"
    frontend_status=0
else
    log_message "Frontend health check: FAILED"
    frontend_status=1
fi

# Exit with error if any service is down
if [ $backend_status -ne 0 ] || [ $frontend_status -ne 0 ]; then
    exit 1
fi

exit 0
```

```bash
# Make executable and add to cron
chmod +x /opt/ai-karen/scripts/health_check.sh

# Add to crontab
crontab -e
# Add this line:
# */5 * * * * /opt/ai-karen/scripts/health_check.sh
```

## Backup Configuration

### 1. Database Backup Script

```bash
# Create backup script
sudo nano /opt/ai-karen/scripts/backup_database.sh
```

**Database Backup Script:**

```bash
#!/bin/bash

# Database backup script
BACKUP_DIR="/opt/ai-karen/backups"
DB_NAME="ai_karen_prod"
DB_USER="ai_karen_user"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create database backup
PGPASSWORD="$DB_PASSWORD" pg_dump -h localhost -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Database backup successful: $BACKUP_FILE"
    
    # Remove backups older than 30 days
    find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +30 -delete
else
    echo "Database backup failed"
    exit 1
fi
```

### 2. Application Backup Script

```bash
# Create application backup script
sudo nano /opt/ai-karen/scripts/backup_application.sh
```

**Application Backup Script:**

```bash
#!/bin/bash

# Application backup script
BACKUP_DIR="/opt/ai-karen/backups"
APP_DIR="/opt/ai-karen/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/app_backup_$TIMESTAMP.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create application backup (excluding venv and node_modules)
tar -czf "$BACKUP_FILE" \
    --exclude="$APP_DIR/venv" \
    --exclude="$APP_DIR/node_modules" \
    --exclude="$APP_DIR/.git" \
    --exclude="$APP_DIR/__pycache__" \
    --exclude="$APP_DIR/*.pyc" \
    -C /opt/ai-karen app

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Application backup successful: $BACKUP_FILE"
    
    # Remove backups older than 7 days
    find "$BACKUP_DIR" -name "app_backup_*.tar.gz" -mtime +7 -delete
else
    echo "Application backup failed"
    exit 1
fi
```

### 3. Schedule Backups

```bash
# Make scripts executable
chmod +x /opt/ai-karen/scripts/backup_*.sh

# Add to crontab
crontab -e
# Add these lines:
# 0 2 * * * /opt/ai-karen/scripts/backup_database.sh
# 0 3 * * 0 /opt/ai-karen/scripts/backup_application.sh
```

## Post-Deployment Verification

### 1. Run Production Validation

```bash
# Run comprehensive validation
cd /opt/ai-karen/app
source venv/bin/activate
python scripts/validate_production_config.py
./scripts/run_production_validation.sh
```

### 2. Manual Testing Checklist

- [ ] Website loads over HTTPS
- [ ] SSL certificate is valid
- [ ] Admin login works with production credentials
- [ ] Chat functionality works
- [ ] Model selection displays production models only
- [ ] Response formatting works correctly
- [ ] Database connections are stable
- [ ] Email notifications work
- [ ] Health checks return success
- [ ] Logs are being written correctly
- [ ] Backups are created successfully

### 3. Performance Testing

```bash
# Install Apache Bench for load testing
sudo apt install -y apache2-utils

# Test frontend performance
ab -n 100 -c 10 https://your-domain.com/

# Test API performance
ab -n 100 -c 10 https://your-domain.com/api/health
```

### 4. Security Verification

```bash
# Run SSL test
curl -I https://your-domain.com/

# Check security headers
curl -I https://your-domain.com/ | grep -E "(Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options)"

# Verify firewall status
sudo ufw status

# Check fail2ban status
sudo fail2ban-client status
```

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed troubleshooting guide.

## Maintenance

### Regular Maintenance Tasks

1. **Daily**: Check logs and health status
2. **Weekly**: Review security logs and update system packages
3. **Monthly**: Review performance metrics and optimize
4. **Quarterly**: Security audit and penetration testing
5. **Annually**: SSL certificate renewal and disaster recovery testing

### Update Procedure

1. Create full backup
2. Test updates in staging environment
3. Schedule maintenance window
4. Deploy updates
5. Run validation tests
6. Monitor for issues

---

**Support**: For deployment support, contact your system administrator or refer to the troubleshooting guide.