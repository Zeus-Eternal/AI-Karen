# Chat Interface

The Control Room exposes a single chat panel where every feature can be accessed.

## Slash Commands

| Command | Description | Required Roles |
| ------- | ----------- | -------------- |
| `/help` | List available commands | user |
| `/memory` | Show recent memory snippets | user |
| `/purge` | Clear short‑term memory | dev |

## Usage Examples

```bash
# Send a normal message
curl -X POST /chat -d 'Hello'

# Inspect recent memory
curl -X POST /chat -d '/memory'
```

## Metrics

The chat backend exposes Prometheus metrics:

- `chat_hub_latency_seconds` – time to generate each reply
- `slash_command_error_total` – validation or authorization failures

Admin users can scrape `/metrics` to view these values in Grafana.
