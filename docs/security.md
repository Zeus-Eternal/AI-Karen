# Security Practices

Kari enforces role-based access control and signs releases with ed25519 keys. Sensitive environment variables should be loaded from a secrets manager such as Vault.

## RBAC Roles

| Role  | Permissions |
| ----- | ----------- |
| `user` | Chat and memory search |
| `dev`  | Plugin management, log viewer, LLM manager |
| `admin` | Full access including guardrail editing and capsule hot-swap |

Roles are checked by `PluginRouter.dispatch()` before invoking a plugin.
UI pages additionally call `require_role()` from `ui.common.components.rbac` to
prevent unauthorized access.

## Secrets Management

Production deployments should store API keys and database passwords outside the repo. Use HashiCorp Vault or similar to mount them at runtime.

```bash
vault kv put secret/kari OPENAI_API_KEY=abc123
```

## Release Signing

Build artifacts are signed using ed25519 keys. Verify signatures before deploying new binaries:

```bash
gpg --verify kari-desktop.tar.gz.sig kari-desktop.tar.gz
```

See `ui_launchers/desktop_ui/README.md` for secure UI practices and [docs/plugin_spec.md](plugin_spec.md) for plugin-level permissions.

## Plugin Sandbox

Plugins are executed in isolated Python subprocesses. The sandbox runner
applies `RLIMIT_CPU` to cap CPU seconds and clears all environment variables
before loading the handler. Standard output and error from the plugin process
are captured and returned to the caller. If a plugin exceeds the configured
timeout it is terminated and a `TimeoutError` is raised.

