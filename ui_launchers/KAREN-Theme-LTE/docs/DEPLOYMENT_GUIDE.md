# KAREN AI Deployment and Configuration Guide

## Overview

This guide provides comprehensive instructions for deploying the KAREN AI system in various environments, from development to production. It covers configuration, security, monitoring, and maintenance procedures.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [Security Configuration](#security-configuration)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Performance Optimization](#performance-optimization)
8. [Maintenance and Updates](#maintenance-and-updates)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- Node.js 18.0+ 
- 4GB RAM
- 10GB storage
- 2 CPU cores

**Recommended Requirements:**
- Node.js 20.0+
- 8GB RAM
- 50GB storage
- 4+ CPU cores
- SSD storage

### External Services

- **Database**: PostgreSQL 14+ (recommended) or MongoDB 5.0+
- **Cache**: Redis 6.0+ (recommended)
- **Object Storage**: AWS S3, Google Cloud Storage, or compatible
- **Monitoring**: Prometheus + Grafana (recommended)
- **Logging**: ELK Stack or similar

## Environment Setup

### Development Environment

1. **Clone Repository**
```bash
git clone https://github.com/karen-ai/karen-theme-default.git
cd karen-theme-default
```

2. **Install Dependencies**
```bash
npm install
```

3. **Environment Configuration**
```bash
cp .env.example .env.local
```

4. **Start Development Server**
```bash
npm run dev
```

### Production Environment

1. **Server Preparation**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 for process management
sudo npm install -g pm2

# Install Nginx for reverse proxy
sudo apt install nginx -y
```

2. **Application Setup**
```bash
# Create application user
sudo useradd -m -s /bin/bash karenai
sudo su - karenai

# Clone and setup application
git clone https://github.com/karen-ai/karen-theme-default.git
cd karen-theme-default
npm install --production
```

## Configuration

### Environment Variables

Create `.env.production` with the following variables:

```bash
# Application
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/karenai
REDIS_URL=redis://localhost:6379

# AI Provider Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_AI_API_KEY=your_google_key
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
COHERE_API_KEY=your_cohere_key
HUGGINGFACE_API_KEY=your_huggingface_key
MISTRAL_API_KEY=your_mistral_key
PERPLEXITY_API_KEY=your_perplexity_key
GROQ_API_KEY=your_groq_key

# Local Model Configuration
OLLAMA_BASE_URL=http://localhost:11434
LM_STUDIO_BASE_URL=http://localhost:1234
LOCALAI_BASE_URL=http://localhost:8080
GPT4ALL_BASE_URL=http://localhost:4891

# Storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BUCKET=karenai-uploads

# Security
JWT_SECRET=your_jwt_secret
API_KEY_ENCRYPTION_KEY=your_encryption_key
RATE_LIMIT_SECRET=your_rate_limit_secret

# Monitoring
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

# Analytics
GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID
ANALYTICS_ENDPOINT=https://analytics.karen-ai.com

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
```

### Database Configuration

**PostgreSQL Setup:**
```sql
-- Create database
CREATE DATABASE karenai;

-- Create user
CREATE USER karenai_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE karenai TO karenai_user;

-- Connect to database and create extensions
\c karenai;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

**Redis Configuration:**
```bash
# /etc/redis/redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Deployment Options

### Option 1: PM2 Deployment

1. **Create PM2 Configuration**
```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'karen-ai',
    script: 'npm',
    args: 'start',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
```

2. **Start Application**
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Option 2: Docker Deployment

1. **Create Dockerfile**
```dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

2. **Create Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: karenai
      POSTGRES_USER: karenai_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

3. **Deploy with Docker**
```bash
docker-compose up -d
```

### Option 3: Kubernetes Deployment

1. **Create Deployment Manifest**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: karen-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: karen-ai
  template:
    metadata:
      labels:
        app: karen-ai
    spec:
      containers:
      - name: karen-ai
        image: karen-ai:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: karen-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

2. **Create Service Manifest**
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: karen-ai-service
spec:
  selector:
    app: karen-ai
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
```

3. **Deploy to Kubernetes**
```bash
kubectl apply -f k8s/
```

## Security Configuration

### SSL/TLS Setup

1. **Generate SSL Certificate**
```bash
sudo certbot --nginx -d your-domain.com
```

2. **Nginx Configuration**
```nginx
# /etc/nginx/sites-available/karen-ai
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Firewall Configuration

```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Security Headers

Add security headers to your application:

```javascript
// next.config.js
const securityHeaders = [
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on'
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload'
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'Referrer-Policy',
    value: 'origin-when-cross-origin'
  },
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https:; media-src 'self' https:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests;"
  }
];

module.exports = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
};
```

## Monitoring and Logging

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'karen-ai'
    static_configs:
      - targets: ['localhost:3000']
    metrics_path: '/api/metrics'
```

### Grafana Dashboard

1. **Import Dashboard**
```bash
# Download dashboard JSON
curl -o karen-ai-dashboard.json https://raw.githubusercontent.com/karen-ai/monitoring/main/grafana-dashboard.json

# Import via Grafana UI or API
```

### Log Management

**Winston Configuration:**
```javascript
// lib/logger.js
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'karen-ai' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

module.exports = logger;
```

## Performance Optimization

### Bundle Optimization

```javascript
// next.config.js
module.exports = {
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['@mui/material', '@emotion/react', '@emotion/styled']
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          framework: {
            name: 'framework',
            chunks: 'all',
            test: /[\\/]node_modules[\\/](react|react-dom|scheduler|prop-types|use-subscription)[\\/]/,
            priority: 40,
          },
          lib: {
            test: /[\\/]node_modules[\\/]/,
            name(module) {
              const packageName = module.context.match(/[\\/]node_modules[\\/](.*?)([\\/]|$)/)[1];
              return `npm.${packageName.replace('@', '')}`;
            },
            priority: 30,
            minChunks: 1,
            reuseExistingChunk: true,
          },
        },
      };
    }
    return config;
  },
};
```

### Caching Strategy

```javascript
// lib/cache.js
const Redis = require('redis');
const client = Redis.createClient(process.env.REDIS_URL);

class CacheService {
  async get(key) {
    try {
      const data = await client.get(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }

  async set(key, data, ttl = 3600) {
    try {
      await client.setex(key, ttl, JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Cache set error:', error);
      return false;
    }
  }

  async del(key) {
    try {
      await client.del(key);
      return true;
    } catch (error) {
      console.error('Cache delete error:', error);
      return false;
    }
  }
}

module.exports = new CacheService();
```

## Maintenance and Updates

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/karen-ai"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U karenai_user karenai > $BACKUP_DIR/db_$DATE.sql

# Application backup
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /home/karenai/karen-theme-default

# Upload to cloud storage (optional)
aws s3 cp $BACKUP_DIR/db_$DATE.sql s3://your-backup-bucket/
aws s3 cp $BACKUP_DIR/app_$DATE.tar.gz s3://your-backup-bucket/

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Update Process

```bash
#!/bin/bash
# update.sh

cd /home/karenai/karen-theme-default

# Pull latest changes
git pull origin main

# Install dependencies
npm install --production

# Build application
npm run build

# Restart application
pm2 restart karen-ai

# Verify health
curl -f http://localhost:3000/api/health || exit 1
```

### Health Checks

```javascript
// lib/health.js
const healthChecks = {
  database: async () => {
    try {
      await db.query('SELECT 1');
      return { status: 'healthy', responseTime: Date.now() - start };
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  },
  
  redis: async () => {
    try {
      await redis.ping();
      return { status: 'healthy' };
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  },
  
  aiProviders: async () => {
    const results = {};
    for (const provider of providers) {
      try {
        await provider.healthCheck();
        results[provider.id] = 'healthy';
      } catch (error) {
        results[provider.id] = 'unhealthy';
      }
    }
    return results;
  }
};

module.exports = healthChecks;
```

## Troubleshooting

### Common Issues

**Issue: Application won't start**
```bash
# Check logs
pm2 logs karen-ai

# Check port usage
sudo netstat -tlnp | grep :3000

# Check environment variables
pm2 env 0
```

**Issue: Database connection failed**
```bash
# Test database connection
psql -h localhost -U karenai_user -d karenai

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

**Issue: High memory usage**
```bash
# Monitor memory usage
pm2 monit

# Check for memory leaks
node --inspect app.js
```

**Issue: Slow response times**
```bash
# Check performance metrics
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:3000/api/health

# Monitor database queries
EXPLAIN ANALYZE SELECT * FROM users WHERE id = 1;
```

### Performance Debugging

```javascript
// lib/profiler.js
const profiler = require('v8-profiler-next');

const startProfiling = (name) => {
  profiler.startProfiling(name, true);
};

const stopProfiling = (name) => {
  const profile = profiler.stopProfiling(name);
  profile.export((error, result) => {
    if (!error) {
      fs.writeFileSync(`./profiles/${name}.cpuprofile`, result);
    }
  });
};

// Usage
startProfiling('slow-operation');
// ... your code here
stopProfiling('slow-operation');
```

### Log Analysis

```bash
# Analyze error patterns
grep -i error /var/log/karen-ai/app.log | awk '{print $1}' | sort | uniq -c | sort -nr

# Monitor response times
grep "response_time" /var/log/karen-ai/access.log | awk '{print $NF}' | sort -n | tail -10

# Check failed requests
grep "status_code:5" /var/log/karen-ai/access.log | wc -l
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying and maintaining the KAREN AI system in production. Following these guidelines will ensure a secure, performant, and reliable deployment.

For additional support or questions, please refer to:
- [API Documentation](./API_DOCUMENTATION.md)
- [Architecture Documentation](./ARCHITECTURE.md)
- [GitHub Issues](https://github.com/karen-ai/issues)