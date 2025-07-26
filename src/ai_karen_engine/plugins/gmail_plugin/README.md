# Gmail Plugin

This core plugin provides basic Gmail functionality. When the environment
variable `GMAIL_API_TOKEN` is set with a valid OAuth access token, the plugin
will call the Gmail REST API to list unread messages and create email drafts.
If the token is absent or an error occurs, the plugin falls back to mocked
responses so tests remain deterministic.

Supported actions via parameters:

- `check_unread` – returns unread emails (real or mocked)
- `compose_email` – creates a draft (real or mocked)
