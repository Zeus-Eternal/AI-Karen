#!/bin/bash

# Update .env.local
echo "Updating environment configuration..."

cat > .env.local << EOL
# AI Karen - Environment Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
KAREN_BACKEND_URL=http://localhost:8000
KAREN_API_BASE=http://localhost:8000

# Database Configuration
POSTGRES_DB=ai_karen
POSTGRES_USER=karen_user
POSTGRES_PASSWORD=karen_secure_pass_change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis Configuration
REDIS_PASSWORD=karen-redis-pass-change-me
REDIS_URL=redis://:karen-redis-pass-change-me@localhost:6380/0

# Authentication Configuration
AUTH_MODE=modern
AUTH_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_SECRET=kari-jwt-secret-key-change-in-production-2024
CSRF_SECRET=kari-csrf-secret-key-change-in-production-2024
EOL

echo "Configuration updated. Please restart both the backend and frontend services."
