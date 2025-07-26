# Gmail Plugin
This plugin provides Gmail functionality for Karen AI.
It supports two actions via parameters:

- `check_unread` – return a summary of unread emails.
- `compose_email` – send an email via Gmail.

For production use the plugin expects Gmail credentials to be supplied via the
``GMAIL_USERNAME`` and ``GMAIL_APP_PASSWORD`` environment variables. When these
variables are not set, the plugin falls back to a mocked behaviour so automated
tests can still run without external dependencies.