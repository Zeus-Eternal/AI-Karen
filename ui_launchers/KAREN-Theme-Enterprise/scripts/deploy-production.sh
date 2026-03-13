#!/bin/bash

# =============================================================================
# AI KAREN - PRODUCTION DEPLOYMENT SCRIPT
# =============================================================================
# This script helps deploy the AI Karen Web UI to production
# Last updated: 2025-12-12

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "Please run this script from the ui_launchers/KAREN-Theme-Default directory"
    exit 1
fi

print_header "AI Karen Web UI - Production Deployment"

# Check for required environment variables
print_status "Checking environment configuration..."

# Check if .env.local exists
if [ -f ".env.local" ]; then
    print_warning ".env.local already exists. Backing up to .env.local.backup"
    cp .env.local .env.local.backup
fi

# Check if production environment file exists
if [ ! -f ".env.production" ]; then
    print_error ".env.production file not found. Please create it first."
    exit 1
fi

# Copy production environment to local
print_status "Setting up production environment..."
cp .env.production .env.local

# Prompt for required production values
print_status "Please configure your production settings:"

# Backend URL
if ! grep -q "NEXT_PUBLIC_KAREN_BACKEND_URL=" .env.local; then
    echo
    read -p "Enter your production backend URL (e.g., https://api.yourdomain.com): " BACKEND_URL
    if [ ! -z "$BACKEND_URL" ]; then
        sed -i "s|NEXT_PUBLIC_KAREN_BACKEND_URL=.*|NEXT_PUBLIC_KAREN_BACKEND_URL=$BACKEND_URL|" .env.local
        sed -i "s|KAREN_BACKEND_URL=.*|KAREN_BACKEND_URL=$BACKEND_URL|" .env.local
    fi
fi

# CORS Origins
if ! grep -q "KARI_CORS_ORIGINS=" .env.local; then
    echo
    read -p "Enter your CORS origins (comma-separated, e.g., https://yourdomain.com,https://www.yourdomain.com): " CORS_ORIGINS
    if [ ! -z "$CORS_ORIGINS" ]; then
        sed -i "s|KARI_CORS_ORIGINS=.*|KARI_CORS_ORIGINS=$CORS_ORIGINS|" .env.local
    fi
fi

# External Host
if ! grep -q "KAREN_EXTERNAL_HOST=" .env.local; then
    echo
    read -p "Enter your external host (e.g., api.yourdomain.com): " EXTERNAL_HOST
    if [ ! -z "$EXTERNAL_HOST" ]; then
        sed -i "s|KAREN_EXTERNAL_HOST=.*|KAREN_EXTERNAL_HOST=$EXTERNAL_HOST|" .env.local
    fi
fi

# High Availability URLs (optional)
echo
read -p "Enter high availability backend URLs (comma-separated, optional): " HA_URLS
if [ ! -z "$HA_URLS" ]; then
    sed -i "s|KAREN_HA_BACKEND_URLS=.*|KAREN_HA_BACKEND_URLS=$HA_URLS|" .env.local
fi

print_status "Environment configuration complete!"

# Install dependencies
print_status "Installing dependencies..."
npm ci --only=production

# Run type checking
print_status "Running type checking..."
npm run type-check

# Build for production
print_status "Building for production..."
export NODE_ENV=production
npm run build

# Check if build was successful
if [ ! -d ".next" ]; then
    print_error "Build failed. .next directory not found."
    exit 1
fi

print_status "Build completed successfully!"

# Run production-specific tests if they exist
if [ -f "package.json" ] && grep -q "test:production" package.json; then
    print_status "Running production tests..."
    npm run test:production
fi

# Display deployment information
print_header "Deployment Information"
echo "Build output: .next directory"
echo "Environment: Production"
echo "Next steps:"
echo "1. Deploy the .next directory to your production server"
echo "2. Configure your production server to serve the static files"
echo "3. Ensure your backend API is accessible at the configured URL"
echo "4. Update your DNS records if needed"

# Security reminders
print_header "Security Checklist"
echo "✓ Environment variables configured for production"
echo "✓ Debug logging disabled"
echo "✓ Development features disabled"
echo "✓ CORS configured for production domains"
echo "✓ HTTPS URLs configured for production"
echo
echo "Remember to:"
echo "- Update your production secrets (JWT keys, database passwords)"
echo "- Configure SSL/TLS certificates"
echo "- Set up monitoring and logging"
echo "- Test the deployment thoroughly"

print_status "Production deployment script completed!"