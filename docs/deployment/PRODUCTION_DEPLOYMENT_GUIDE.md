# AI-Karen Production Deployment Guide

## Overview

This guide covers production deployment of AI-Karen across different environments including Docker, Kubernetes, and cloud platforms. It includes security hardening, performance optimization, and monitoring setup.

## Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended for AI workloads)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 50GB+ SSD storage
- **Network**: Stable internet connection for model downloads

### Software Requirements
- Docker 24.0+ and Docker Compose 2.20+
- Python 3.11+ (for local development)
- Node.js 18+ (for UI builds)
- Git 2.30+

## Production Environment Setup

### 1. Environment Configuration

Create production environment file:
```bash
cp .env.example .env.production
```

**Critical Production Variables:**
```bash
# Security
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
POSTGRES_PASSWORD=your-secure-database-password
REDIS_PASSWORD=your-secure-redis-password

# Performance
KARI_LAZY_LOADING=true
KARI_MINIMAL_STARTUP=true
KARI_RESOURCE_MONITORING=true
KARI_AUTO_CLEANUP=true

# Networking
KARI_CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com
KAREN_BACKEND_URL=https://api.your-domain.com
POSTGRES_HOST=postgres
REDIS_URL=redis://redis:6379/0

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
PROMETHEUS_ENABLED=true

# AI Models
WARMUP_LLM=true
LLAMA_THREADS=4
LLAMA_MLOCK=true
```

### 2. SSL/TLS Configuration

**Generate SSL Certificates:**
```bash
# Using Let's Encrypt
certbot certonly --standalone -d api.your-domain.com
certbot certonly --standalone -d app.your-domain.com

# Or use your existing certificates
mkdir -p ssl/
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem
```

**nginx Configuration:**
```nginx
# /etc/nginx/sites-available/ai-karen
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_private_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

server {
    listen 443 ssl http2;
    server_name app.your-domain.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_private_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8020;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker Production Deployment

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PROFILE: runtime-perf
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - KARI_LAZY_LOADING=true
      - KARI_MINIMAL_STARTUP=true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    volumes:
      - ./models:/app/models:ro
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - karen-network

  web-ui:
    build:
      context: ./ui_launchers/web_ui
      dockerfile: Dockerfile.prod
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.your-domain.com
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    networks:
      - karen-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=ai_karen_prod
      - POSTGRES_USER=karen_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U karen_user -d ai_karen_prod"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    networks:
      - karen-network

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    volumes:
      - redis_data:/data
    networks:
      - karen-network

  milvus:
    image: milvusdb/milvus:v2.3.0
    command: ["milvus", "run", "standalone"]
    environment:
      - ETCD_ENDPOINTS=etcd:2379
      - MINIO_ADDRESS=minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    networks:
      - karen-network

  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    networks:
      - karen-network

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped
    networks:
      - karen-network

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt

volumes:
  postgres_data:
  redis_data:
  milvus_data:
  prometheus_data:
  grafana_data:

networks:
  karen-network:
    driver: bridge
```

### 2. Deploy Production Stack

```bash
# Create secrets directory
mkdir -p secrets/
echo "your-secure-postgres-password" > secrets/postgres_password.txt
chmod 600 secrets/postgres_password.txt

# Deploy production stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Initialize database
docker compose exec api python create_tables.py
docker compose exec api python create_admin_user.py

# Verify deployment
docker compose ps
docker compose logs api
```

## Kubernetes Deployment

### 1. Kubernetes Manifests

**Namespace:**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-karen
```

**ConfigMap:**
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: karen-config
  namespace: ai-karen
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  KARI_LAZY_LOADING: "true"
  KARI_MINIMAL_STARTUP: "true"
  POSTGRES_HOST: "postgres-service"
  REDIS_URL: "redis://redis-service:6379/0"
```

**Secrets:**
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: karen-secrets
  namespace: ai-karen
type: Opaque
data:
  jwt-secret: <base64-encoded-jwt-secret>
  postgres-password: <base64-encoded-postgres-password>
  redis-password: <base64-encoded-redis-password>
```

**API Deployment:**
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: karen-api
  namespace: ai-karen
spec:
  replicas: 3
  selector:
    matchLabels:
      app: karen-api
  template:
    metadata:
      labels:
        app: karen-api
    spec:
      containers:
      - name: api
        image: ai-karen:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: karen-config
        - secretRef:
            name: karen-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: models
          mountPath: /app/models
          readOnly: true
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: karen-models-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: karen-logs-pvc
```

**Service:**
```yaml
# k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: karen-api-service
  namespace: ai-karen
spec:
  selector:
    app: karen-api
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

**Ingress:**
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: karen-ingress
  namespace: ai-karen
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.your-domain.com
    - app.your-domain.com
    secretName: karen-tls
  rules:
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: karen-api-service
            port:
              number: 8000
  - host: app.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: karen-web-service
            port:
              number: 3000
```

### 2. Deploy to Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n ai-karen
kubectl get services -n ai-karen
kubectl get ingress -n ai-karen

# View logs
kubectl logs -f deployment/karen-api -n ai-karen
```

## Cloud Platform Deployment

### AWS ECS Deployment

**Task Definition:**
```json
{
  "family": "ai-karen-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "karen-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/ai-karen:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:karen/jwt-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-karen",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### Google Cloud Run Deployment

```bash
# Build and push image
gcloud builds submit --tag gcr.io/your-project/ai-karen

# Deploy to Cloud Run
gcloud run deploy ai-karen-api \
  --image gcr.io/your-project/ai-karen \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO \
  --set-secrets JWT_SECRET_KEY=karen-jwt-secret:latest
```

## Security Hardening

### 1. Network Security

**Firewall Rules:**
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 8000/tcp   # Block direct API access
ufw enable
```

**Docker Network Isolation:**
```yaml
# Isolate services in separate networks
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### 2. Authentication Security

**JWT Configuration:**
```bash
# Use strong JWT secrets (256-bit minimum)
JWT_SECRET_KEY=$(openssl rand -base64 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600  # 1 hour
JWT_REFRESH_EXPIRATION=604800  # 1 week
```

**Password Policies:**
```python
# In auth configuration
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SYMBOLS = True
PASSWORD_MAX_AGE_DAYS = 90
```

### 3. Database Security

**PostgreSQL Hardening:**
```sql
-- Create restricted user
CREATE USER karen_app WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE ai_karen_prod TO karen_app;
GRANT USAGE ON SCHEMA public TO karen_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO karen_app;

-- Enable SSL
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';
```

## Performance Optimization

### 1. Application Performance

**Startup Optimization:**
```bash
# Use optimized startup mode
KARI_LAZY_LOADING=true
KARI_MINIMAL_STARTUP=true
KARI_ULTRA_MINIMAL=true
KARI_RESOURCE_MONITORING=true
```

**Model Performance:**
```bash
# Optimize AI model performance
LLAMA_THREADS=8
LLAMA_MLOCK=true
PROFILE=runtime-perf  # Enable OpenBLAS
```

### 2. Database Performance

**PostgreSQL Tuning:**
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

**Connection Pooling:**
```python
# Database connection pool settings
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 30
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_POOL_RECYCLE = 3600
```

### 3. Caching Strategy

**Redis Configuration:**
```bash
# Redis performance settings
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

**Application Caching:**
```python
# Cache configuration
CACHE_TYPE = "redis"
CACHE_REDIS_URL = "redis://redis:6379/1"
CACHE_DEFAULT_TIMEOUT = 300
CACHE_KEY_PREFIX = "karen:"
```

## Monitoring and Observability

### 1. Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'karen-api'
    static_configs:
      - targets: ['karen-api:8000']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. Grafana Dashboards

**API Performance Dashboard:**
```json
{
  "dashboard": {
    "title": "AI-Karen API Performance",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 3. Log Aggregation

**Fluentd Configuration:**
```yaml
# fluentd/fluent.conf
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match karen.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name karen-logs
  type_name _doc
  logstash_format true
  logstash_prefix karen
  flush_interval 10s
</match>
```

## Backup and Disaster Recovery

### 1. Database Backups

**Automated PostgreSQL Backups:**
```bash
#!/bin/bash
# backup-postgres.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
DB_NAME="ai_karen_prod"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h postgres -U karen_user -d $DB_NAME | gzip > $BACKUP_DIR/backup_${DATE}.sql.gz

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_${DATE}.sql.gz s3://your-backup-bucket/postgres/
```

### 2. Model and Data Backups

```bash
#!/bin/bash
# backup-models.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/models"

# Backup models directory
tar -czf $BACKUP_DIR/models_${DATE}.tar.gz /app/models/

# Backup configuration
tar -czf $BACKUP_DIR/config_${DATE}.tar.gz /app/config/

# Upload to cloud storage
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/models/
```

### 3. Disaster Recovery Plan

**Recovery Procedures:**
1. **Database Recovery:**
   ```bash
   # Restore from backup
   gunzip -c backup_20250101_120000.sql.gz | psql -h postgres -U karen_user -d ai_karen_prod
   ```

2. **Application Recovery:**
   ```bash
   # Redeploy application
   docker compose -f docker-compose.prod.yml up -d
   
   # Restore models
   tar -xzf models_20250101_120000.tar.gz -C /
   ```

3. **Verification:**
   ```bash
   # Health checks
   curl http://localhost:8000/health
   curl http://localhost:8000/api/health/summary
   ```

## Maintenance Procedures

### 1. Regular Maintenance Tasks

**Weekly Tasks:**
```bash
# Update system packages
apt update && apt upgrade -y

# Clean Docker images
docker system prune -f

# Rotate logs
logrotate /etc/logrotate.d/ai-karen

# Check disk space
df -h
```

**Monthly Tasks:**
```bash
# Update Docker images
docker compose pull
docker compose up -d

# Vacuum PostgreSQL
docker compose exec postgres psql -U karen_user -d ai_karen_prod -c "VACUUM ANALYZE;"

# Check SSL certificate expiration
openssl x509 -in /etc/ssl/certs/cert.pem -noout -dates
```

### 2. Scaling Procedures

**Horizontal Scaling:**
```bash
# Scale API instances
docker compose up -d --scale api=3

# Kubernetes scaling
kubectl scale deployment karen-api --replicas=5 -n ai-karen
```

**Vertical Scaling:**
```yaml
# Update resource limits
deploy:
  resources:
    limits:
      memory: 8G
      cpus: '4.0'
```

This production deployment guide provides comprehensive coverage of deploying AI-Karen in production environments with proper security, monitoring, and maintenance procedures.