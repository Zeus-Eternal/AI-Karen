#!/bin/bash
set -e

# etcd Entrypoint Script for AI Karen
# This script sets up proper permissions for etcd data directory before starting etcd

echo "🔧 Setting up etcd for AI Karen..."

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

# Start etcd with the provided arguments
log "🚀 Starting etcd..."
exec etcd "$@"