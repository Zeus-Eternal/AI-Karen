# CoPilot Architecture Deployment Guide

## Overview

This document provides a comprehensive guide for deploying the CoPilot Architecture in a production environment. The CoPilot Architecture integrates a sophisticated UI/UX layer with Karen's agent architecture to provide an intuitive interface for agent capabilities.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ or equivalent)
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **RAM**: 8GB minimum, 16GB recommended
- **CPU**: 4 cores minimum, 8 cores recommended
- **Storage**: 100GB minimum, 500GB recommended
- **Network**: Stable internet connection for downloading Docker images

### Software Dependencies
- Git
- OpenSSL (for SSL certificate generation)
- Bash (for deployment scripts)

### Ports
Ensure the following ports are available:
- **8010**: CoPilot Web UI
- **8000**: Backend API
- **9090**: Prometheus metrics
- **3001**: Grafana dashboard
- **5432**: PostgreSQL database
- **6380**: Redis cache
- **9200**: Elasticsearch
- **19530**: Milvus vector database

## Deployment Preparation

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/ai-karen.git
cd ai-karen
```

### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp config/copilot_production.env .env

# Edit the environment file with your configuration
nano .env
```

Key configuration parameters to update:
- Database credentials
- Redis password
- SSL certificate paths
- Domain names
- Email settings for notifications

### 3. Generate SSL Certificates
```bash
# Create SSL certificates directory
mkdir -p certs

# Generate self-signed certificates (for testing)
openssl req -x509 -newkey rsa:4096 -keyout certs/tls.key -out certs/tls.crt -days 365 -nodes -subj "/CN=localhost"

# For production, use certificates from a trusted CA
```

## Deployment Options

### Option 1: Automated Deployment (Recommended)

This method uses the provided deployment scripts for a fully automated deployment.

#### Steps:
1. **Run the Deployment Script**
   ```bash
   ./scripts/deploy-copilot.sh
   ```

2. **Verify Deployment**
   ```bash
   # Check service status
   docker-compose -f docker-compose-copilot.yml ps

   # Check health endpoints
   curl http://localhost:8000/health
   curl http://localhost:8010
   ```

3. **Access the Application**
   - CoPilot Web UI: http://localhost:8010
   - Backend API: http://localhost:8000
   - Grafana Dashboard: http://localhost:3001 (admin/admin)

### Option 2: Manual Deployment

This method provides more control over the deployment process.

#### Steps:
1. **Create Necessary Directories**
   ```bash
   mkdir -p logs backups data/postgres data/redis data/elasticsearch data/milvus
   mkdir -p monitoring/grafana/provisioning/dashboards monitoring/grafana/provisioning/datasources
   ```

2. **Start Infrastructure Services**
   ```bash
   # Start database and cache services
   docker-compose -f docker-compose-copilot.yml up -d postgres-copilot redis-copilot elasticsearch-copilot

   # Wait for services to be ready
   sleep 30
   ```

3. **Start Milvus Services**
   ```bash
   # Start Milvus dependencies
   docker-compose -f docker-compose-copilot.yml up -d milvus-etcd-copilot milvus-minio-copilot

   # Wait for services to be ready
   sleep 20

   # Start Milvus
   docker-compose -f docker-compose-copilot.yml up -d milvus-copilot

   # Wait for Milvus to be ready
   sleep 60
   ```

4. **Start Monitoring Services**
   ```bash
   # Start Prometheus and Grafana
   docker-compose -f docker-compose-copilot.yml up -d prometheus-copilot grafana-copilot

   # Wait for services to be ready
   sleep 20
   ```

5. **Start Application Services**
   ```bash
   # Build and start API and web services
   docker-compose -f docker-compose-copilot.yml up -d --build api-copilot web-copilot

   # Wait for services to be ready
   sleep 60
   ```

6. **Verify Deployment**
   ```bash
   # Check service status
   docker-compose -f docker-compose-copilot.yml ps

   # Check health endpoints
   curl http://localhost:8000/health
   curl http://localhost:8010
   ```

### Option 3: Production Deployment with Reverse Proxy

For production deployment, it's recommended to use a reverse proxy like Nginx.

#### Steps:
1. **Install and Configure Nginx**
   ```bash
   # Install Nginx
   sudo apt update
   sudo apt install nginx

   # Create Nginx configuration
   sudo nano /etc/nginx/sites-available/ai-karen-copilot
   ```

2. **Nginx Configuration Example**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       # Redirect to HTTPS
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name your-domain.com;

       # SSL configuration
       ssl_certificate /path/to/your/certificate.crt;
       ssl_certificate_key /path/to/your/private.key;

       # Security headers
       add_header X-Frame-Options DENY;
       add_header X-Content-Type-Options nosniff;
       add_header X-XSS-Protection "1; mode=block";
       add_header Referrer-Policy "strict-origin-when-cross-origin";

       # CoPilot Web UI
       location / {
           proxy_pass http://localhost:8010;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # Backend API
       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # WebSocket support
       location /ws/ {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Enable the Site**
   ```bash
   # Enable the site
   sudo ln -s /etc/nginx/sites-available/ai-karen-copilot /etc/nginx/sites-enabled/

   # Test Nginx configuration
   sudo nginx -t

   # Restart Nginx
   sudo systemctl restart nginx
   ```

4. **Deploy CoPilot**
   ```bash
   # Deploy using the automated script
   ./scripts/deploy-copilot.sh
   ```

## Post-Deployment Configuration

### 1. Initialize the System
1. **Access the Web Interface**
   - Open http://your-domain.com in your browser
   - Create an admin account

2. **Configure Model Orchestrator**
   - Navigate to Settings > Model Orchestrator
   - Configure model registry and settings
   - Test model connections

3. **Set Up Extensions**
   - Navigate to Extensions > Available Extensions
   - Install required extensions
   - Configure extension settings

### 2. Configure Monitoring
1. **Access Grafana Dashboard**
   - Open http://your-domain.com:3001 in your browser
   - Log in with admin/admin (change password on first login)

2. **Configure Data Sources**
   - Add Prometheus as a data source
   - URL: http://prometheus-copilot:9090

3. **Import Dashboards**
   - Import the CoPilot dashboard from `monitoring/dashboards/copilot/`

### 3. Set Up Backups
1. **Configure Automated Backups**
   ```bash
   # Add to crontab
   crontab -e

   # Add the following line for daily backups at 2 AM
   0 2 * * * /path/to/ai-karen/scripts/backup-copilot.sh
   ```

2. **Verify Backups**
   ```bash
   # List available backups
   ls -la backups/
   ```

## Management Operations

### Starting and Stopping Services
```bash
# Start all services
docker-compose -f docker-compose-copilot.yml up -d

# Stop all services
docker-compose -f docker-compose-copilot.yml down

# Stop services and remove containers
docker-compose -f docker-compose-copilot.yml down -v

# Restart specific service
docker-compose -f docker-compose-copilot.yml restart api-copilot
```

### Updating the Deployment
```bash
# Update using the automated script
./scripts/update-copilot.sh

# Manual update
docker-compose -f docker-compose-copilot.yml pull
docker-compose -f docker-compose-copilot.yml up -d --build
```

### Backing Up and Restoring
```bash
# Create backup
./scripts/backup-copilot.sh

# Restore from backup
./scripts/restore-copilot.sh
```

### Viewing Logs
```bash
# View all logs
docker-compose -f docker-compose-copilot.yml logs -f

# View specific service logs
docker-compose -f docker-compose-copilot.yml logs -f api-copilot

# View logs from last hour
docker-compose -f docker-compose-copilot.yml logs --since 1h
```

### Scaling Services
```bash
# Scale API service
docker-compose -f docker-compose-copilot.yml up -d --scale api-copilot=3

# Scale web service
docker-compose -f docker-compose-copilot.yml up -d --scale web-copilot=2
```

## Troubleshooting

### Common Issues

#### 1. Services Fail to Start
**Symptoms**: Containers exit immediately or fail to start
**Solution**:
```bash
# Check container logs
docker-compose -f docker-compose-copilot.yml logs

# Check resource usage
docker stats

# Check port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :8010
```

#### 2. Database Connection Issues
**Symptoms**: API service unable to connect to database
**Solution**:
```bash
# Check database service status
docker-compose -f docker-compose-copilot.yml ps postgres-copilot

# Check database logs
docker-compose -f docker-compose-copilot.yml logs postgres-copilot

# Test database connection
docker-compose -f docker-compose-copilot.yml exec postgres-copilot psql -U karen_user -d ai_karen_copilot -c "SELECT 1"
```

#### 3. High Memory Usage
**Symptoms**: Services become slow or unresponsive
**Solution**:
```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose-copilot.yml

# Restart services
docker-compose -f docker-compose-copilot.yml restart
```

#### 4. SSL Certificate Issues
**Symptoms**: Browser warnings about insecure connection
**Solution**:
```bash
# Check certificate expiration
openssl x509 -in certs/tls.crt -noout -dates

# Renew certificate if expired
# For production, use Let's Encrypt or your organization's CA
```

### Debug Mode
To enable debug mode for troubleshooting:
```bash
# Edit the environment file
nano .env

# Change DEBUG to true
DEBUG=true

# Restart services
docker-compose -f docker-compose-copilot.yml restart api-copilot web-copilot
```

### Health Checks
Check the health of all services:
```bash
# API health
curl http://localhost:8000/health

# Web health
curl http://localhost:8010

# Prometheus health
curl http://localhost:9090

# Grafana health
curl http://localhost:3001
```

## Security Considerations

### 1. Network Security
- Use firewall rules to restrict access to ports
- Only expose necessary ports to the internet
- Use VPN or private networks for internal communication

### 2. Authentication and Authorization
- Change default passwords
- Use strong passwords for all services
- Enable two-factor authentication where possible
- Implement proper RBAC (Role-Based Access Control)

### 3. Data Security
- Encrypt sensitive data at rest and in transit
- Regularly back up data
- Store backups in secure locations
- Implement data retention policies

### 4. Application Security
- Keep all dependencies up to date
- Regularly scan for vulnerabilities
- Use security headers in web responses
- Implement proper input validation and sanitization

## Performance Optimization

### 1. Resource Allocation
- Allocate sufficient memory and CPU to containers
- Monitor resource usage and adjust as needed
- Consider using dedicated servers for database services

### 2. Database Optimization
- Use connection pooling
- Optimize database queries
- Implement proper indexing
- Consider read replicas for high read loads

### 3. Caching Strategy
- Use Redis for application caching
- Cache frequently accessed data
- Implement cache invalidation strategies

### 4. Content Delivery
- Use CDN for static assets
- Enable HTTP/2 for better performance
- Compress responses where appropriate

## Support and Maintenance

### Regular Maintenance Tasks
1. **Daily**
   - Monitor system health
   - Check error logs
   - Verify backup completion

2. **Weekly**
   - Review performance metrics
   - Check disk usage
   - Update security patches

3. **Monthly**
   - Test backup and restore procedures
   - Review user feedback and issues
   - Plan for capacity upgrades

### Support Contacts
- **Documentation**: This guide and other documentation in the `docs/` directory
- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join our community forum for questions and discussions

### Getting Help
If you encounter issues during deployment:
1. Check the troubleshooting section in this guide
2. Search existing issues on GitHub
3. Ask questions in the community forum
4. Contact the development team for critical issues

## Conclusion

This deployment guide provides all the information needed to successfully deploy the CoPilot Architecture in a production environment. By following these instructions, you can ensure a smooth and reliable deployment that meets your organization's needs.

Remember to regularly update your deployment and follow security best practices to maintain a secure and stable system.