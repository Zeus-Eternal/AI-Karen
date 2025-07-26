# Gmail Plugin

This core plugin exposes minimal Gmail features for Karen AI.
It cleanly separates network calls (handled by `GmailClient`) from the plugin
logic so that the same handler can operate against real Gmail or mocked data.

When the environment variable `GMAIL_API_TOKEN` contains a valid OAuth access
token, all actions are executed against the Gmail REST API.  Without the token
or on failure, mocked responses are returned so tests remain deterministic.

Supported actions via parameters:

- `check_unread` – returns unread emails (real or mocked)
- `compose_email` – creates a draft (real or mocked)
