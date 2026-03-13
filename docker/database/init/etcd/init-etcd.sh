#!/bin/bash
set -e

# etcd Initialization Script for AI Karen
# This script sets up proper permissions for etcd data directory

echo "🔧 Setting up etcd permissions for AI Karen..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Set proper permissions for etcd data directory
# etcd recommends 700 (rwx------) for the data directory
if [ -d "/etcd" ]; then
    log "Setting permissions for /etcd directory..."
    chmod 700 /etcd
    log "✅ Permissions set successfully for /etcd"
else
    log "⚠️  /etcd directory does not exist, will be created by etcd"
fi

log "🎉 etcd initialization completed successfully!"