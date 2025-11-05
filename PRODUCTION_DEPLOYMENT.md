# 🚀 KARI AI - PRODUCTION DEPLOYMENT GUIDE

**Version:** 1.0.0
**Last Updated:** 2025-11-05
**Status:** ✅ Production Ready

---

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### ✅ **Code Quality**
- [x] All Streamlit UI code removed
- [x] Deprecated authentication system backups removed
- [x] Example and demo files cleaned up
- [x] TODO/FIXME comments audited (only 1 non-blocking TODO remains)
- [x] Stub implementations verified (test-only usage)
- [x] Production-grade error handling implemented
- [x] Structured logging in place

### ✅ **System Architecture**
- [x] KIRE (Kari Intelligent Routing Engine) - Production ready
- [x] KRO (Kari Reasoning Orchestrator) - Production ready
- [x] NeuroVault memory system - Tri-partite memory (episodic, semantic, procedural)
- [x] Multi-database support (PostgreSQL, Redis, Milvus, ElasticSearch, DuckDB)
- [x] LLM provider abstraction (OpenAI, Gemini, Deepseek, Ollama, etc.)
- [x] Graceful degradation and fallback mechanisms
- [x] RBAC and JWT authentication

---

## 🔧 **ENVIRONMENT CONFIGURATION**

### 1. **Critical Environment Variables**

Create a `.env.production` file with the following variables:

```bash
# === SECURITY (CRITICAL - MUST CHANGE) ===
AUTH_SECRET_KEY=<generate-secure-512-bit-key>
AUTH_SESSION_SECRET=<generate-secure-512-bit-key>
JWT_SECRET_KEY=<generate-secure-512-bit-key>

# === DATABASE CONFIGURATION ===
AUTH_DATABASE_URL=postgresql+asyncpg://user:password@host:5432/kari_production
REDIS_HOST=redis-production.example.com
REDIS_PORT=6379
REDIS_PASSWORD=<secure-redis-password>
MILVUS_HOST=milvus-production.example.com
MILVUS_PORT=19530
ELASTICSEARCH_URL=https://elasticsearch-production.example.com:9200

# === LLM PROVIDER API KEYS ===
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
# Add other provider keys as needed

# === APPLICATION SETTINGS ===
ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_DEBUG=false
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com

# === SECURITY FEATURES ===
AUTH_ENABLE_SECURITY_FEATURES=true
AUTH_ENABLE_RATE_LIMITING=true
AUTH_ENABLE_SESSION_VALIDATION=true
AUTH_SESSION_COOKIE_SECURE=true
AUTH_SESSION_COOKIE_SAMESITE=strict

# === PERFORMANCE ===
KARI_SERVER_WORKERS=4
DB_POOL_SIZE=20
DB_POOL_MAX_OVERFLOW=40
PERFORMANCE_METRICS_ENABLE=true
ENABLE_GRACEFUL_SHUTDOWN=true

# === MONITORING ===
PROMETHEUS_ENABLED=true
PERFORMANCE_MONITORING_ENABLE=true
PERFORMANCE_AUTO_OPTIMIZE=true
```

### 2. **Generate Secure Keys**

```bash
# Generate AUTH_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate REDIS_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🗄️ **DATABASE SETUP**

### **PostgreSQL** (Primary relational database)

```bash
# 1. Create production database
createdb kari_production

# 2. Run migrations
cd /path/to/AI-Karen
alembic upgrade head

# 3. Verify connection
python -c "from ai_karen_engine.database.client import get_database_client; import asyncio; asyncio.run(get_database_client().health_check())"
```

**Production Settings:**
- Pool size: 20 connections
- Max overflow: 40
- Connection timeout: 45s
- Pool recycle: 3600s (1 hour)

### **Redis** (Session cache, rate limiting)

```bash
# Redis configuration (redis.conf)
maxmemory 2gb
maxmemory-policy allkeys-lru
requirepass <REDIS_PASSWORD>
bind 0.0.0.0
protected-mode yes
```

### **Milvus** (Vector embeddings)

```bash
# Deploy Milvus with Helm
helm install milvus milvus/milvus \
  --set cluster.enabled=true \
  --set etcd.replicaCount=3 \
  --set minio.mode=distributed

# Create collections
python scripts/setup_milvus_collections.py --environment production
```

**Collections:**
- `ai_karen_memories` - Episodic memory (dim=1536, metric=COSINE)
- `semantic_knowledge` - Semantic memory (dim=1536, metric=COSINE)
- `procedural_skills` - Procedural memory (dim=768, metric=IP)

### **ElasticSearch** (Full-text search, logging)

```bash
# Deploy ElasticSearch cluster (minimum 3 nodes for production)
docker-compose -f docker/elasticsearch-cluster.yml up -d

# Create indices
curl -X PUT "https://elasticsearch:9200/kari-logs-production"
curl -X PUT "https://elasticsearch:9200/kari-conversations-production"
```

---

## 🚢 **DEPLOYMENT OPTIONS**

### **Option 1: Docker Compose (Recommended for single-server)**

```bash
# 1. Build production image
docker build -t kari-ai:production -f Dockerfile .

# 2. Deploy with docker-compose
docker-compose -f docker-compose.production.yml up -d

# 3. Check logs
docker-compose logs -f kari-api
```

### **Option 2: Kubernetes (Recommended for scaling)**

```bash
# 1. Deploy with Helm chart
helm install kari-ai ./src/charts/kari \
  --namespace kari-production \
  --values ./src/charts/kari/values.production.yaml

# 2. Verify deployment
kubectl get pods -n kari-production
kubectl logs -f deployment/kari-api -n kari-production

# 3. Expose service
kubectl expose deployment kari-api --type=LoadBalancer --port=80 --target-port=8000
```

### **Option 3: Standalone Python**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment
export $(cat .env.production | xargs)

# 3. Run server
python start.py --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🔒 **SECURITY HARDENING**

### **1. SSL/TLS Configuration**

```nginx
# Nginx reverse proxy (recommended)
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/kari-ai.crt;
    ssl_certificate_key /etc/ssl/private/kari-ai.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **2. Firewall Rules**

```bash
# Only allow HTTPS traffic
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp  # For Let's Encrypt renewal
sudo ufw deny 8000/tcp # Block direct access to application

# Allow database access only from application server
sudo ufw allow from <app-server-ip> to any port 5432
sudo ufw allow from <app-server-ip> to any port 6379
```

### **3. Rate Limiting**

Already configured in application:
- 100 requests per minute per IP (default)
- JWT-based authentication with 24h expiry
- Session validation on each request
- Automatic rate limit escalation for suspicious activity

---

## 📊 **MONITORING & OBSERVABILITY**

### **Prometheus Metrics**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'kari-ai'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Available Metrics:**
- `kari_http_requests_total` - Total HTTP requests
- `kari_http_request_duration_seconds` - Request latency
- `kari_llm_requests_total` - LLM provider requests
- `kari_llm_request_duration_seconds` - LLM response time
- `kari_memory_operations_total` - Memory operations
- `kari_database_connections` - Active DB connections

### **Grafana Dashboards**

```bash
# Import pre-built dashboard
cp monitoring/grafana-dashboard.json /var/lib/grafana/dashboards/

# Restart Grafana
sudo systemctl restart grafana-server
```

### **Health Checks**

```bash
# Application health
curl https://api.yourdomain.com/health

# Detailed status
curl https://api.yourdomain.com/health/detailed
```

---

## 🧪 **TESTING IN PRODUCTION**

### **Smoke Tests**

```bash
# Run smoke tests against production
pytest tests/e2e/smoke_tests.py --env production --base-url https://api.yourdomain.com

# Test LLM providers
pytest tests/integration/llm/test_provider_health.py --env production
```

### **Load Testing**

```bash
# Install k6
brew install k6  # or download from k6.io

# Run load test
k6 run tests/performance/load_test.js --vus 100 --duration 5m
```

---

## 🔄 **BACKUP & DISASTER RECOVERY**

### **Database Backups**

```bash
# PostgreSQL automated backups (cron job)
0 2 * * * pg_dump kari_production | gzip > /backups/kari_$(date +\%Y\%m\%d).sql.gz

# Milvus backups
0 3 * * * python scripts/backup_milvus.py --output /backups/milvus_$(date +\%Y\%m\%d)

# Rotate backups (keep last 30 days)
find /backups -name "kari_*.sql.gz" -mtime +30 -delete
```

### **Disaster Recovery Plan**

1. **Database Failure:**
   - Automatic failover to read replica
   - Restore from latest backup (< 24 hours old)

2. **LLM Provider Outage:**
   - Automatic failover via KIRE routing
   - Graceful degradation to local models

3. **Complete System Failure:**
   - Restore from last backup
   - Replay Redis cache from PostgreSQL
   - Rebuild Milvus indices from PostgreSQL vectors

---

## 📈 **SCALING RECOMMENDATIONS**

### **Horizontal Scaling**

```yaml
# Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: kari-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: kari-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### **Database Scaling**

- **PostgreSQL:** Configure read replicas (1 master + 2 replicas minimum)
- **Redis:** Redis Cluster mode (6 nodes: 3 masters + 3 replicas)
- **Milvus:** Increase query/data node replicas
- **ElasticSearch:** Scale to 5+ data nodes

---

## 🐛 **TROUBLESHOOTING**

### **Common Issues**

#### **1. Database Connection Errors**
```bash
# Check PostgreSQL connectivity
psql -h <host> -U <user> -d kari_production

# Increase connection pool
export DB_POOL_SIZE=40
export DB_POOL_MAX_OVERFLOW=80
```

#### **2. LLM Provider Timeouts**
```bash
# Check provider health
curl https://api.yourdomain.com/api/llm/providers

# Enable fallback routing
export ENABLE_LLM_FALLBACK=true
export LLM_REQUEST_TIMEOUT=30
```

#### **3. Memory/Performance Issues**
```bash
# Check memory usage
docker stats kari-api

# Increase worker count and memory limits
export KARI_SERVER_WORKERS=8
export UVICORN_LIMIT_MAX_REQUESTS=1000
```

---

## 📞 **SUPPORT & CONTACTS**

- **Technical Issues:** https://github.com/Zeus-Eternal/AI-Karen/issues
- **Security Vulnerabilities:** security@yourdomain.com
- **Production Support:** devops@yourdomain.com

---

## ✅ **FINAL PRE-LAUNCH CHECKLIST**

- [ ] All environment variables configured and tested
- [ ] SSL/TLS certificates installed and verified
- [ ] Database migrations completed successfully
- [ ] Redis cache operational
- [ ] Milvus collections created and indexed
- [ ] ElasticSearch indices created
- [ ] Monitoring dashboards configured (Prometheus + Grafana)
- [ ] Backup automation configured and tested
- [ ] Load testing completed (>1000 concurrent users)
- [ ] Security audit completed
- [ ] Disaster recovery plan tested
- [ ] Documentation updated
- [ ] Team trained on production operations

---

**🎉 Kari AI is production-ready. Deploy with confidence!**
