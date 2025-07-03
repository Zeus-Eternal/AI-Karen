# UI Handbook

The Tauri Control Room is the main interface for interacting with Kari. Pages are displayed according to the user's role.

## Navigation

- **Chat** – send messages to Kari and view responses.
- **Memory Matrix** – search stored interactions.
- **Plugins** – enable/disable plugins and open their UIs (Dev+).
- **LLM Manager** – select local or remote models (Dev+).
- **Settings** – edit application configuration.
- **Guardrails** – edit YAML rules that validate plugin parameters (Admin only).
- **Diagnostics** – view system health checks (Admin only).
- **Dashboard** – Prometheus metrics and system health (Admin only).
- **SelfRefactor Logs** – review patch history (Admin only).

The top bar shows a role badge, theme switcher and live status indicator fed by the EventBus.

## RBAC

Pages use the `require_role()` decorator from `ui.common.components` to hide
admin-only features. Session state must include a `roles` list for access checks.

## Accessibility

- Keyboard navigation is standard across pages.
- Set `prefers-color-scheme` in your OS to enable high-contrast mode.
- ARIA labels are included in sidebar links for screen readers.

## Plugin UI Injection

Plugins may provide a `ui.py` module exporting `render()`. The Control Room loads these modules at runtime. Untrusted UIs require `ADVANCED_MODE=true`.

For additional UX guidelines see the prompt at `self_refactor/prompts/ux_update.txt`.
