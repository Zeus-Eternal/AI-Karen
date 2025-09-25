#!/bin/bash
echo "🔧 Fixing frontend configuration to connect to host backend..."

# Update the web container environment to use host backend
docker compose stop web
docker compose rm -f web

# Update docker-compose.yml web service environment
cat > temp_web_config.yml << 'EOF'
  web:
    container_name: ai-karen-web
    image: node:20-alpine
    working_dir: /app
    env_file:
      - .env
    environment:
      NODE_ENV: development
      # Use host backend instead of Docker api service
      KAREN_BACKEND_URL: http://host.docker.internal:8000
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000
      NEXT_PUBLIC_KAREN_BACKEND_URL: http://localhost:8000
    ports:
      - "8010:8010"
    volumes:
      - ./ui_launchers/web_ui:/app
      - ./.env.local:/app/.env.local:ro
    command: sh -c "npm install && npm run dev -- --port 8010"
    networks:
      - ai-karen-net
    extra_hosts:
      - "host.docker.internal:host-gateway"
EOF

echo "✅ Configuration updated. Now restart the web container:"
echo "   docker compose up web -d"
echo ""
echo "🌐 Your frontend will be available at: http://localhost:8010"
echo "🔗 It will connect to your backend at: http://localhost:8000"