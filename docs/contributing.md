# Contributing Guide

We welcome community plugins and bug fixes. Please follow the checklist below when submitting a pull request.

## Development Setup

```bash
pip install -r requirements.txt
pre-commit install  # sets up git hooks from .pre-commit-config.yaml
```

## Coding Standards

- Format with `black` and `isort`.
- Lint with `ruff`.
- Type-check with `mypy --strict`.
- Add tests under `tests/` and keep coverage above 85%.

## Plugin Development

1. Create a folder under `src/ai_karen_engine/plugins/` with `plugin_manifest.json` and `handler.py`.
2. Optionally add `ui.py` if your plugin provides a Control Room widget.
3. Reload plugins via `POST /plugins/reload` or the Plugin Manager page.

See [docs/plugin_spec.md](plugin_spec.md) for the manifest schema.

## Pull Request Checklist

- [ ] Keep commits focused and descriptive.
- [ ] Run `pytest -q` before pushing.
- [ ] Update documentation if behavior changes.
- [ ] Verify that `pre-commit` hooks pass.

Happy hacking!
