# Complete Deployment Guide for AI Karen Database Services

## Issues Identified and Fixed

### 1. Redis Memory Overcommit Issue
**Status**: Fixed in configuration, requires manual system-level fix

**Problem**: Redis was showing warnings about memory overcommit not being enabled.

**Solution**: 
- Created Redis configuration with proper PID file path
- Updated Docker Compose to mount Redis configuration and PID file directory
- Created `fix-redis-memory-overcommit.sh` script to fix the system-level issue

**Manual Fix Required**:
```bash
# Fix the Redis memory overcommit issue
sudo sysctl vm.overcommit_memory=1

# Make the change permanent
echo 'vm.overcommit_memory = 1' | sudo tee -a /etc/sysctl.conf
```

### 2. MinIO Deprecated Environment Variables
**Status**: Fixed ✅

**Problem**: MinIO was showing warnings about deprecated environment variables.

**Solution**: 
- Updated Docker Compose to use `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` instead of the deprecated `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`
- Updated .env file to include `MINIO_PORT=9001` and `MINIO_CONSOLE_PORT=9002` to avoid port conflicts

### 3. Milvus RootCoord Connection Issues
**Status**: Fixed ✅

**Problem**: Milvus was unable to connect to the RootCoord component.

**Solution**: 
- Updated etcd configuration with proper network settings
- Added additional etcd environment variables for better stability
- Modified Milvus configuration to use local storage type
- Ensured proper network connectivity between Milvus and etcd

### 4. Docker Command Update
**Status**: Fixed ✅

**Problem**: Scripts were using the older `docker-compose` command instead of the newer `docker compose` command.

**Solution**: 
- Updated all scripts to use `docker compose` instead of `docker-compose`

### 5. Port Conflicts
**Status**: Partially Fixed

**Problem**: System services were using ports that our Docker containers needed.

**Solution**: 
- Updated Redis to use port 6380 instead of 6379
- Updated MinIO to use ports 9001 and 9002 instead of 9000 and 9001

**Manual Fix Required**:
```bash
# Stop the system Redis service (if not needed)
sudo systemctl stop redis
sudo systemctl disable redis

# OR kill the Redis process
sudo kill 1402  # Replace with the actual PID from your system
```

## Deployment Instructions

### Prerequisites
1. Docker and Docker Compose installed
2. Sudo access to fix system-level issues
3. No conflicting services running on required ports

### Step-by-Step Deployment

1. **Fix System-Level Issues** (requires sudo):
   ```bash
   # Fix Redis memory overcommit
   sudo sysctl vm.overcommit_memory=1
   echo 'vm.overcommit_memory = 1' | sudo tee -a /etc/sysctl.conf
   
   # Stop system Redis service (if needed)
   sudo systemctl stop redis
   sudo systemctl disable redis
   ```

2. **Run the Deployment Script**:
   ```bash
   cd docker/scripts
   ./deploy-database-services-no-sudo.sh
   ```

3. **Test the Services**:
   ```bash
   ./test-docker-services.sh
   ```

4. **Check Service Status**:
   ```bash
   cd ../database
   docker compose ps
   ```

## Troubleshooting

### Port Conflicts
If you encounter port conflicts:
1. Check what's using the port: `ss -tlnp | grep <port>`
2. Stop the conflicting service or change the port in the .env file
3. Restart the deployment

### Redis Memory Overcommit Warnings
If Redis still shows memory overcommit warnings:
1. Verify the fix was applied: `cat /proc/sys/vm/overcommit_memory`
2. If it's not 1, reapply the fix: `sudo sysctl vm.overcommit_memory=1`
3. Restart the Redis container: `docker compose restart redis`

### Milvus RootCoord Connection Issues
If Milvus still has RootCoord connection issues:
1. Check etcd logs: `docker compose logs milvus-etcd`
2. Check Milvus logs: `docker compose logs milvus`
3. Restart the services: `docker compose restart`

### MinIO Deprecated Variables Warning
If MinIO still shows warnings about deprecated variables:
1. Check your .env file to ensure it's using `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`
2. Make sure the Docker Compose file is using the correct environment variables
3. Restart the MinIO service: `docker compose restart milvus-minio`

## Service Ports

After successful deployment, the services will be available on these ports:

- **PostgreSQL**: 5433 (or as configured in .env)
- **Elasticsearch**: 9200 (or as configured in .env)
- **Milvus**: 19530 (or as configured in .env)
- **Redis**: 6380 (or as configured in .env)
- **MinIO**: 9001 (API) and 9002 (Console) (or as configured in .env)

## Next Steps

After successful deployment, you can:

1. **Initialize the databases**:
   ```bash
   docker compose logs -f db-init
   ```

2. **Connect your application** to the databases using the connection parameters from the .env file

3. **Monitor the services**:
   ```bash
   docker compose logs -f [service-name]
   ```

4. **Stop the services** when needed:
   ```bash
   docker compose down
   ```

## Support

If you encounter any issues not covered in this guide, please:
1. Check the logs of the specific service: `docker compose logs [service-name]`
2. Run the test script to identify the problem: `./test-docker-services.sh`
3. Create an issue with detailed information about the problem