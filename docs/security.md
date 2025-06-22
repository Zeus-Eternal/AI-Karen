# Security Practices

Kari enforces role-based access control and signs releases with ed25519 keys. Sensitive environment variables should be loaded from a secrets manager such as Vault.

## RBAC Roles

| Role  | Permissions |
| ----- | ----------- |
| `user` | Chat and memory search |
| `dev`  | Plugin management, log viewer, LLM manager |
| `admin` | Full access including guardrail editing and capsule hot-swap |

Roles are checked by `PluginRouter.dispatch()` before invoking a plugin.

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

See [docs/ui_handbook.md](ui_handbook.md) for secure UI practices and [docs/plugin_spec.md](plugin_spec.md) for plugin-level permissions.
