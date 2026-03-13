# Docker Services Debugging and Deployment

This directory contains scripts to fix common issues with the AI Karen database services and deploy them properly.

## Issues Fixed

### 1. Redis Memory Overcommit Issue

**Problem**: Redis was showing warnings about memory overcommit not being enabled, which could cause failures under low memory conditions.

**Solution**: 
- Created `fix-redis-memory-overcommit.sh` script to set `vm.overcommit_memory=1` at the system level
- Updated Redis configuration to use a valid PID file path
- Modified Docker Compose to mount the Redis configuration and PID file directory

### 2. MinIO Deprecated Environment Variables

**Problem**: MinIO was showing warnings about deprecated environment variables `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`.

**Solution**: 
- Updated Docker Compose to use the new environment variables `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`
- Ensured consistency between the `.env` file and Docker Compose configuration

### 3. Milvus RootCoord Connection Issues

**Problem**: Milvus was unable to connect to the RootCoord component, causing service failures.

**Solution**: 
- Updated etcd configuration with proper network settings
- Added additional etcd environment variables for better stability
- Modified Milvus configuration to use local storage type
- Ensured proper network connectivity between Milvus and etcd

## Scripts

### fix-redis-memory-overcommit.sh

This script fixes the Redis memory overcommit issue by:
1. Checking the current `vm.overcommit_memory` setting
2. Setting it to `1` if it's not already set
3. Making the change permanent by updating `/etc/sysctl.conf`

**Usage**:
```bash
sudo ./fix-redis-memory-overcommit.sh
```

**Note**: This script requires sudo privileges to modify system settings.

### test-docker-services.sh

This script tests the Docker services after deployment by:
1. Checking if all containers are running
2. Verifying the health status of each service
3. Testing connections to Redis, MinIO, etcd, and Milvus

**Usage**:
```bash
./test-docker-services.sh
```

### deploy-database-services.sh

This is the main deployment script that:
1. Fixes the Redis memory overcommit issue
2. Stops existing containers
3. Cleans up unused volumes and networks
4. Starts the database services
5. Waits for services to be ready
6. Tests the services
7. Displays the service status

**Usage**:
```bash
./deploy-database-services.sh
```

## Manual Steps

If you prefer to perform the fixes manually, here are the steps:

### 1. Fix Redis Memory Overcommit

```bash
# Check current setting
cat /proc/sys/vm/overcommit_memory

# Set to 1 (temporary)
sudo sysctl vm.overcommit_memory=1

# Make permanent
echo "vm.overcommit_memory = 1" | sudo tee -a /etc/sysctl.conf
```

### 2. Update Docker Compose

The Docker Compose file has already been updated with the necessary fixes. Make sure you're using the latest version.

### 3. Restart Services

```bash
cd docker/database
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Redis Still Shows Memory Overcommit Warning

If Redis still shows the memory overcommit warning after running the fix script:
1. Make sure you ran the script with sudo privileges
2. Check if the setting was applied: `cat /proc/sys/vm/overcommit_memory`
3. If it's still not 1, try running: `sudo sysctl vm.overcommit_memory=1`
4. Reboot the system if the issue persists

### Milvus RootCoord Connection Issues

If Milvus still has RootCoord connection issues:
1. Check etcd logs: `docker-compose logs milvus-etcd`
2. Check Milvus logs: `docker-compose logs milvus`
3. Make sure all services are running: `docker-compose ps`
4. Try restarting the services: `docker-compose restart`

### MinIO Still Shows Deprecated Variables Warning

If MinIO still shows warnings about deprecated variables:
1. Check your `.env` file to ensure it's using `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`
2. Make sure the Docker Compose file is using the correct environment variables
3. Restart the MinIO service: `docker-compose restart milvus-minio`

## Support

If you encounter any issues that are not covered in this documentation, please:
1. Check the logs of the specific service: `docker-compose logs [service-name]`
2. Run the test script to identify the problem: `./test-docker-services.sh`
3. Create an issue with detailed information about the problem