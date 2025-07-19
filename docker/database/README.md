# AI Karen Database Infrastructure

This directory contains the complete Docker-based database infrastructure for AI Karen, providing a streamlined setup for all required database services including PostgreSQL, DuckDB, Elasticsearch, Milvus, and Redis.

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

- Docker Engine 20.10+
- Docker Compose 2.0+ (or docker-compose 1.29+)
- At least 4GB RAM available for containers
- At least 10GB free disk space
- Linux, macOS, or Windows with WSL2

## Services Included

### Core Databases
- **PostgreSQL 15**: Primary relational database for memory, sessions, and extensions
- **DuckDB**: User profiles, profile history, and structured analytics data
- **Elasticsearch 8.9**: Document search and indexing for memory retrieval
- **Redis 7**: Caching and session storage

### Vector Database Stack
- **Milvus 2.3**: Vector database for embeddings and similarity search
- **ETCD**: Configuration management for Milvus
- **MinIO**: Object storage for Milvus data persistence

## Directory Structure

```
docker/database/
├── docker-compose.yml          # Main orchestration file
├── .env.template              # Environment configuration template
├── README.md                  # This file
├── init/                      # Initialization scripts
│   ├── init-all.sh           # Master initialization script
│   ├── postgres/             # PostgreSQL initialization
│   ├── elasticsearch/        # Elasticsearch setup
│   ├── milvus/              # Milvus configuration
│   └── duckdb/              # DuckDB setup
├── migrations/               # Database migrations
│   ├── postgres/            # PostgreSQL migrations
│   ├── elasticsearch/       # Elasticsearch mappings
│   └── milvus/             # Milvus collections
└── scripts/                 # Management scripts
    ├── start.sh            # Start all services
    ├── stop.sh             # Stop all services
    ├── restart.sh          # Restart services
    ├── reset.sh            # Reset all data
    ├── backup.sh           # Create backups
    ├── restore.sh          # Restore from backup
    └── health-check.sh     # Health monitoring
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

- **Database Credentials**: Secure passwords for all services
- **Resource Limits**: Memory and connection limits for each service
- **Feature Flags**: Enable/disable optional services
- **Environment Mode**: Development vs production settings

### Port Mappings

Default ports (configurable via `.env`):
- PostgreSQL: 5432
- Elasticsearch: 9200
- Milvus: 19530
- Redis: 6379
- MinIO: 9000 (API), 9001 (Console)

## Management Commands

### Basic Operations
```bash
# Start all services
./scripts/start.sh

# Stop all services
./scripts/stop.sh

# Restart services
./scripts/restart.sh

# Check service health
./scripts/health-check.sh
```

### Data Management
```bash
# Reset all data (DESTRUCTIVE)
./scripts/reset.sh

# Create backups
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backup-2024-01-01.tar.gz
```

## Health Monitoring

All services include comprehensive health checks:
- **PostgreSQL**: Connection and query tests
- **Elasticsearch**: Cluster health API
- **Milvus**: Service status endpoint
- **Redis**: PING command
- **DuckDB**: File accessibility check

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