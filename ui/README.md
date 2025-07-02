# Kari UI Modules

This directory groups all frontend user interfaces.

```
ui/
├── common/      # shared widgets, hooks, themes
├── desktop_ui/  # Tauri React desktop shell
├── mobile_ui/   # Streamlit mobile interface
├── admin_ui/    # Admin dashboard
```

Run the mobile UI with:

```bash
streamlit run ui/mobile_ui/app.py
```

The desktop UI uses Tauri and lives under `ui/desktop_ui`.
