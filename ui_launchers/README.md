# Kari UI Modules

This directory groups all frontend user interfaces.

```
ui_launchers/
├── common/        # shared widgets, hooks, themes
├── desktop_ui/    # Tauri React desktop shell
├── streamlit_ui/  # Streamlit mobile interface
├── admin_ui/      # Admin dashboard
```

Run the mobile UI with:

```bash
streamlit run ui_launchers/streamlit_ui/app.py
```

The desktop UI uses Tauri and lives under `ui_launchers/desktop_ui`.
