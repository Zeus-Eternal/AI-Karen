# AI Karen Database Infrastructure

This directory contains the complete Docker-based database infrastructure for AI Karen, providing a production-ready multi-service database stack with comprehensive orchestration, monitoring, and backup capabilities.

## 🚀 Quick Start

1. **Copy environment template:**
   ```bash
   cp .env.template .env
   ```

2. **Customize configuration:**
   Edit `.env` file with your preferred settings and secure passwords.

3. **Start all database services:**
   ```bash
   ./scripts/start.sh
   ```

4. **Verify services are running:**
   ```bash
   ./scripts/health-check.sh
   ```

## 📋 Prerequisites

### Minimum Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+ (or docker-compose 1.29+)
- 4GB RAM available for containers
- 10GB free disk space
- Linux, macOS, or Windows with WSL2

### Recommended for Production
- 8GB+ RAM
- 50GB+ SSD storage
- 4+ CPU cores
- Dedicated network interface

## 🗄️ Database Services

### Core Relational & Analytics
- **PostgreSQL 15**: Primary relational database with vector extensions
  - User sessions, memory storage, and application data
  - Optimized for OLTP workloads with connection pooling
  - Automated backups and point-in-time recovery

- **DuckDB**: High-performance analytics database
  - User profiles, analytics data, and structured reporting
  - Columnar storage for fast analytical queries
  - File-based with zero-configuration deployment

### Search & Indexing
- **Elasticsearch 8.9**: Full-text search and document indexing
  - Memory retrieval and semantic search capabilities
  - Real-time indexing with configurable analyzers
  - Cluster health monitoring and automatic recovery

### Caching & Session Management
- **Redis 7**: High-performance in-memory data store
  - Session storage, caching, and real-time features
  - Pub/Sub messaging for real-time updates
  - Persistence with RDB and AOF backup strategies

### Vector Database Stack
- **Milvus 2.3**: Specialized vector database for AI workloads
  - Embedding storage and similarity search
  - Support for multiple vector index types (IVF, HNSW, etc.)
  - Horizontal scaling and load balancing

- **ETCD**: Distributed configuration management
  - Service discovery and configuration for Milvus
  - Consistent metadata storage across cluster nodes

- **MinIO**: S3-compatible object storage
  - Persistent storage backend for Milvus vector data
  - Multi-tenant object storage with versioning
  - Web console for administration and monitoring

## 🏗️ Architecture Overview

### Service Orchestration
The database stack uses Docker Compose for multi-service orchestration with:
- **Service Dependencies**: Proper startup order with health checks
- **Network Isolation**: Dedicated bridge network for inter-service communication
- **Volume Management**: Persistent storage with backup-friendly volume structure
- **Resource Limits**: Configurable memory and CPU constraints per service

### Environment Configurations
- **docker-compose.yml**: Base configuration for all environments
- **docker-compose.dev.yml**: Development overrides with debug tools
- **docker-compose.prod.yml**: Production optimizations and security hardening

## 📁 Directory Structure

```
docker/database/
├── docker-compose.yml          # Base orchestration configuration
├── docker-compose.dev.yml      # Development environment overrides
├── docker-compose.prod.yml     # Production environment configuration
├── .env.template              # Environment configuration template
├── .env.development           # Development environment defaults
├── .env.production            # Production environment template
├── README.md                  # This documentation
├── data/                      # Local data directories (created automatically)
│   ├── postgres/             # PostgreSQL data files
│   ├── elasticsearch/        # Elasticsearch indices
│   ├── milvus/              # Milvus vector data
│   ├── redis/               # Redis persistence files
│   ├── duckdb/              # DuckDB database files
│   ├── etcd/                # ETCD configuration data
│   └── minio/               # MinIO object storage
├── backups/                  # Backup storage (created automatically)
│   ├── postgres/            # PostgreSQL backups
│   ├── elasticsearch/       # Elasticsearch snapshots
│   ├── milvus/             # Milvus collection backups
│   ├── redis/              # Redis RDB backups
│   ├── duckdb/             # DuckDB file backups
│   └── full/               # Complete system backups
├── init/                     # Service initialization scripts
│   ├── init-all.sh          # Master initialization coordinator
│   ├── wait-for-services.sh # Service readiness checker
│   ├── bootstrap/           # Bootstrap data and seed files
│   ├── postgres/            # PostgreSQL schema and initial data
│   ├── elasticsearch/       # Index templates and mappings
│   ├── milvus/             # Collection schemas and indexes
│   ├── redis/              # Redis configuration and namespaces
│   └── duckdb/             # DuckDB schema and analytics setup
├── migrations/              # Database schema migrations
│   ├── postgres/           # PostgreSQL migration scripts
│   ├── elasticsearch/      # Elasticsearch mapping updates
│   ├── milvus/            # Milvus collection modifications
│   └── duckdb/            # DuckDB schema changes
├── config/                 # Service-specific configurations
│   ├── elasticsearch.yml  # Elasticsearch production config
│   ├── milvus_dev.yaml    # Milvus development settings
│   ├── milvus_prod.yaml   # Milvus production settings
│   └── redis_prod.conf    # Redis production configuration
├── scripts/               # Management and automation scripts
│   ├── start.sh          # Service startup with dependency management
│   ├── stop.sh           # Graceful service shutdown
│   ├── restart.sh        # Service restart with health checks
│   ├── reset.sh          # Complete data reset (destructive)
│   ├── backup.sh         # Comprehensive backup creation
│   ├── restore.sh        # Backup restoration with verification
│   ├── health-check.sh   # Multi-service health monitoring
│   ├── monitor.sh        # Continuous health monitoring
│   ├── migrate.sh        # Database migration runner
│   ├── configure-env.sh  # Environment setup automation
│   └── migration-manager.py # Advanced migration management
├── logs/                 # Service logs (created automatically)
└── tests/               # Integration and health tests
    └── test-suite.sh    # Comprehensive test runner
```

## ⚙️ Configuration

### Environment Variables

The `.env` file controls all aspects of the database stack configuration:

#### Database Credentials
```bash
# PostgreSQL
POSTGRES_DB=ai_karen
POSTGRES_USER=karen_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_MAX_CONNECTIONS=200

# Redis
REDIS_PASSWORD=redis_secure_password
REDIS_MEMORY_LIMIT=2g

# Elasticsearch
ELASTICSEARCH_PASSWORD=elastic_secure_password
ELASTICSEARCH_HEAP_SIZE=2g

# Milvus & MinIO
MINIO_ACCESS_KEY=minio_access_key
MINIO_SECRET_KEY=minio_secret_key
```

#### Resource Limits & Performance Tuning
```bash
# Memory allocation per service
POSTGRES_SHARED_BUFFERS=256MB
ELASTICSEARCH_HEAP_SIZE=2g
MILVUS_MEMORY_LIMIT=4g
REDIS_MEMORY_LIMIT=2g

# Connection limits
POSTGRES_MAX_CONNECTIONS=200
REDIS_MAX_CLIENTS=10000

# Performance settings
POSTGRES_WORK_MEM=4MB
POSTGRES_MAINTENANCE_WORK_MEM=64MB
```

#### Feature Flags & Environment Mode
```bash
# Service toggles
ENABLE_MILVUS=true
ENABLE_ELASTICSEARCH=true
ENABLE_MONITORING=true
ENABLE_BACKUPS=true

# Environment configuration
ENVIRONMENT=production  # development, staging, production
DATA_PATH=/opt/ai-karen/data  # Production data path
BACKUP_SCHEDULE="0 2 * * *"   # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

### Port Mappings

Default ports (all configurable via `.env`):

| Service | Default Port | Purpose | Production Binding |
|---------|--------------|---------|-------------------|
| PostgreSQL | 5432 | Database connections | 127.0.0.1:5432 |
| Elasticsearch | 9200 | HTTP API | 127.0.0.1:9200 |
| Milvus | 19530 | Vector database | 127.0.0.1:19530 |
| Redis | 6379 | Cache & sessions | 127.0.0.1:6379 |
| MinIO API | 9000 | Object storage | 127.0.0.1:9000 |
| MinIO Console | 9001 | Web interface | 127.0.0.1:9001 |

### Deployment Environments

#### Development Environment
```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Features:
# - Debug logging enabled
# - Admin tools (Adminer, Redis Commander)
# - Reduced resource requirements
# - Development-friendly defaults
```

#### Production Environment
```bash
# Start with production optimizations
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Features:
# - Security hardening
# - Resource optimization
# - Automated backups
# - Performance monitoring
# - SSL/TLS encryption
```

## 🛠️ Management Commands

### Service Lifecycle Management
```bash
# Start all services with dependency management
./scripts/start.sh

# Start with specific options
./scripts/start.sh --no-pull          # Skip image updates
./scripts/start.sh --foreground       # Run in foreground
./scripts/start.sh --skip-init        # Skip initialization

# Stop services gracefully
./scripts/stop.sh

# Restart with health verification
./scripts/restart.sh

# Check comprehensive service health
./scripts/health-check.sh
./scripts/health-check.sh --service postgres  # Check specific service
./scripts/health-check.sh --quick             # Quick health check
```

### Data Management & Backup Operations
```bash
# Complete system backup
./scripts/backup.sh

# Service-specific backups
./scripts/backup.sh --service postgres
./scripts/backup.sh --service milvus

# Compressed backup with verification
./scripts/backup.sh --compress --verify

# Restore from backup
./scripts/restore.sh backup-20240101_120000.tar.gz

# Reset all data (DESTRUCTIVE - use with caution)
./scripts/reset.sh
```

### Database Migration Management
```bash
# Run all pending migrations
./scripts/migrate.sh

# Run migrations for specific service
./scripts/migrate.sh --service postgres

# Check migration status
./scripts/migrate.sh --status

# Advanced migration management
python3 ./scripts/migration-manager.py --help
```

### Monitoring & Maintenance
```bash
# Continuous health monitoring
./scripts/monitor.sh

# Environment configuration setup
./scripts/configure-env.sh --environment production

# Run comprehensive test suite
./tests/test-suite.sh

# Performance analysis
./scripts/performance-analysis.sh
```

## 📊 Scaling Considerations

### Horizontal Scaling Options

#### PostgreSQL Scaling
- **Read Replicas**: Configure streaming replication for read-heavy workloads
- **Connection Pooling**: Use PgBouncer for connection management
- **Partitioning**: Implement table partitioning for large datasets
- **Sharding**: Consider application-level sharding for extreme scale

#### Elasticsearch Scaling
- **Multi-Node Cluster**: Add data and master nodes for high availability
- **Index Sharding**: Configure optimal shard count based on data volume
- **Replica Management**: Balance between search performance and storage cost
- **Hot-Warm Architecture**: Implement tiered storage for cost optimization

#### Milvus Scaling
- **Distributed Deployment**: Scale compute and storage independently
- **Collection Partitioning**: Partition large vector collections
- **Index Optimization**: Choose appropriate index types for query patterns
- **Load Balancing**: Distribute query load across multiple nodes

#### Redis Scaling
- **Redis Cluster**: Implement Redis Cluster for automatic sharding
- **Sentinel Setup**: High availability with automatic failover
- **Read Replicas**: Scale read operations with replica nodes
- **Memory Optimization**: Use appropriate data structures and expiration policies

### Vertical Scaling Guidelines

#### Resource Allocation by Workload
```bash
# Light workload (< 1000 users)
POSTGRES_SHARED_BUFFERS=128MB
ELASTICSEARCH_HEAP_SIZE=1g
MILVUS_MEMORY_LIMIT=2g
REDIS_MEMORY_LIMIT=512m

# Medium workload (1000-10000 users)
POSTGRES_SHARED_BUFFERS=512MB
ELASTICSEARCH_HEAP_SIZE=4g
MILVUS_MEMORY_LIMIT=8g
REDIS_MEMORY_LIMIT=2g

# Heavy workload (10000+ users)
POSTGRES_SHARED_BUFFERS=2GB
ELASTICSEARCH_HEAP_SIZE=16g
MILVUS_MEMORY_LIMIT=32g
REDIS_MEMORY_LIMIT=8g
```

## 🚀 Production Deployment Guidelines

### Pre-Deployment Checklist

#### Security Hardening
- [ ] Change all default passwords to strong, unique values
- [ ] Enable SSL/TLS encryption for all services
- [ ] Configure firewall rules to restrict access
- [ ] Set up proper network segmentation
- [ ] Enable audit logging for all databases
- [ ] Configure service-to-service authentication

#### Performance Optimization
- [ ] Tune database parameters for production workload
- [ ] Configure appropriate resource limits
- [ ] Set up monitoring and alerting
- [ ] Optimize Docker host system settings
- [ ] Configure log rotation and retention
- [ ] Set up automated backup procedures

#### High Availability Setup
- [ ] Configure service health checks and restart policies
- [ ] Set up data replication where applicable
- [ ] Implement backup and disaster recovery procedures
- [ ] Configure monitoring and alerting systems
- [ ] Document operational procedures
- [ ] Test failover and recovery scenarios

### Production Environment Setup

#### 1. System Preparation
```bash
# Create dedicated user and directories
sudo useradd -r -s /bin/false ai-karen
sudo mkdir -p /opt/ai-karen/{data,backups,logs,config}
sudo chown -R ai-karen:ai-karen /opt/ai-karen

# Configure system limits
echo "ai-karen soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "ai-karen hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize kernel parameters
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
echo "vm.swappiness=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### 2. Production Configuration
```bash
# Copy production environment template
cp .env.production .env

# Configure production settings
export DATA_PATH=/opt/ai-karen/data
export BACKUP_PATH=/opt/ai-karen/backups
export LOG_PATH=/opt/ai-karen/logs
export ENVIRONMENT=production

# Generate secure passwords
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export ELASTICSEARCH_PASSWORD=$(openssl rand -base64 32)
export MINIO_SECRET_KEY=$(openssl rand -base64 32)
```

#### 3. SSL/TLS Configuration
```bash
# Generate SSL certificates (example with Let's Encrypt)
sudo certbot certonly --standalone -d your-domain.com

# Configure SSL in production compose file
# Update docker-compose.prod.yml with certificate paths
```

#### 4. Monitoring Setup
```bash
# Start with monitoring enabled
ENABLE_MONITORING=true ./scripts/start.sh

# Configure external monitoring (Prometheus, Grafana, etc.)
# Set up log aggregation (ELK stack, Fluentd, etc.)
```

## 🔍 Health Monitoring & Observability

### Built-in Health Checks
All services include comprehensive health monitoring:

#### PostgreSQL Health Monitoring
- **Connection Tests**: Verify database connectivity and authentication
- **Query Performance**: Monitor slow queries and connection pool status
- **Replication Status**: Check streaming replication lag (if configured)
- **Disk Usage**: Monitor database size and available storage
- **Lock Monitoring**: Detect long-running locks and deadlocks

#### Elasticsearch Health Monitoring
- **Cluster Health**: Monitor cluster status (green/yellow/red)
- **Node Status**: Check individual node health and resource usage
- **Index Health**: Monitor index size, shard allocation, and search performance
- **Query Performance**: Track search latency and throughput
- **Memory Usage**: Monitor heap usage and garbage collection

#### Milvus Health Monitoring
- **Service Status**: Verify Milvus server responsiveness
- **Collection Health**: Monitor collection status and index building
- **Query Performance**: Track vector search latency and accuracy
- **Resource Usage**: Monitor memory and CPU utilization
- **Storage Health**: Check MinIO backend connectivity and performance

#### Redis Health Monitoring
- **Connection Status**: Verify Redis connectivity and authentication
- **Memory Usage**: Monitor memory consumption and eviction policies
- **Persistence Status**: Check RDB and AOF backup status
- **Replication Health**: Monitor master-slave replication (if configured)
- **Performance Metrics**: Track command latency and throughput

### Advanced Monitoring Features
```bash
# Real-time health dashboard
./scripts/monitor.sh --dashboard

# Performance profiling
./scripts/monitor.sh --profile --duration 300

# Alert configuration
./scripts/monitor.sh --configure-alerts

# Export metrics to external systems
./scripts/monitor.sh --export-prometheus
```

## Data Persistence

All data is persisted using Docker volumes:
- `postgres_data`: PostgreSQL database files
- `elasticsearch_data`: Elasticsearch indices
- `milvus_data`: Milvus vector data
- `redis_data`: Redis persistence files
- `duckdb_data`: DuckDB database files
- `etcd_data`: ETCD configuration
- `minio_data`: MinIO object storage

## Troubleshooting

### Common Issues

1. **Services won't start**: Check port conflicts and ensure Docker has sufficient resources
2. **Connection refused**: Verify services are healthy using `./scripts/health-check.sh`
3. **Data corruption**: Use `./scripts/reset.sh` to reinitialize (will lose data)
4. **Performance issues**: Adjust resource limits in `.env` file

### Logs

View service logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs postgres
docker-compose logs elasticsearch
docker-compose logs milvus
```

### Resource Requirements

**Minimum Requirements:**
- RAM: 4GB
- Disk: 10GB free space
- CPU: 2 cores

**Recommended for Production:**
- RAM: 8GB+
- Disk: 50GB+ SSD
- CPU: 4+ cores

## Security Considerations

### Development Mode
- Default passwords (change in production)
- Services exposed on localhost
- Debug logging enabled

### Production Mode
- Strong passwords required
- Network isolation
- SSL/TLS encryption
- Audit logging enabled

## Integration with AI Karen

The database services integrate seamlessly with AI Karen:
- Connection parameters match existing client configurations
- No code changes required for database connectivity
- Supports existing migration and initialization scripts

## Backup Strategy

### Automated Backups
- Daily backups of all databases
- Configurable retention policies
- Compressed and timestamped archives

### Manual Backups
```bash
# Create immediate backup
./scripts/backup.sh

# Restore specific backup
./scripts/restore.sh backup-filename.tar.gz
```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs for error messages
3. Ensure all prerequisites are met
4. Verify configuration in `.env` file