# UI Manifest Examples

This directory contains example `ui/manifest.json` files to help plugin authors understand the schema and create their own manifests.

## Files

- `example-manifest.json` - Basic single-slot plugin example
- `analytics-manifest.json` - Multi-slot plugin example (sidebar + overview)
- `settings-manifest.json` - Settings page plugin example

## Usage

Copy these examples to your plugin's `ui/` directory and modify them according to your needs:

```
your-plugin/
├── plugin_manifest.json
├── ui/
│   ├── manifest.json          # Copy and modify an example
│   ├── YourPluginPage.tsx    # Your UI component
│   └── assets/
│       └── your-plugin---sidebar_00.svg  # Your icon
└── ...
```

## Key Differences Between Examples

### Example Plugin (`example-manifest.json`)
- **Slot**: `sidebar.plugins` only
- **Permissions**: `["user", "admin"]`
- **Use case**: Simple plugin with sidebar navigation

### Analytics Plugin (`analytics-manifest.json`)
- **Slots**: `sidebar.plugins` + `page.plugins.overview`
- **Permissions**: `["admin"]` only
- **Use case**: Admin-only plugin with multiple UI contributions

### Settings Plugin (`settings-manifest.json`)
- **Slot**: `page.settings.sections` only
- **Permissions**: `["user"]`
- **Use case**: Plugin that integrates into settings pages

## Customization Guide

1. **Change the plugin_id** to match your backend plugin name
2. **Update the component path** to match your UI component filename
3. **Modify slots** based on where your plugin should appear
4. **Adjust permissions** based on who should access your plugin
5. **Customize display_name and label** for your plugin
6. **Add your own icon** in the assets folder
7. **Set the order** to control sidebar position

## Next Steps

After creating your manifest:

1. Create your UI component in the same `ui/` directory
2. Test that your plugin appears in the UI
3. Check the plugin health page for any issues
4. Consult the main documentation for advanced features

For more detailed information, see the main `plugin-manifest-schema.md` file.