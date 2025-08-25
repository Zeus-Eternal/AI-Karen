#!/bin/bash
# Simple loop to wait for Kari API health endpoint
until curl -sf http://127.0.0.1:8000/health >/dev/null; do
  echo "waiting for kari api..."
  sleep 1
done
echo "kari api is up"
