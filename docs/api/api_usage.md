# API Usage Guide

This guide provides quick examples for interacting with Kari's REST API.

## Basic Endpoints

List available routes:
```bash
curl http://localhost:8000/
```

Health check:
```bash
curl http://localhost:8000/ping
```

## Sending Chat Messages

Use the `/chat` endpoint to converse with the assistant:
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"text": "hello"}' http://localhost:8000/chat
```

## Plugin Operations

Plugins can be invoked directly when their manifest exposes a specific route. Refer to `plugin_manifest.json` for the plugin name and parameters.


