# Plugin UI Manifest Schema

This document describes the `ui/manifest.json` contract for plugin authors who want to add UI components to Karen-AI-Theme through the Frontend Plugin Host system.

## Overview

The `ui/manifest.json` file is a standardized contract that declares your plugin's frontend UI capabilities, component location, required permissions, and display metadata. This manifest enables the Frontend Plugin Host to automatically discover, validate, and render your plugin UI without requiring modifications to core Karen-AI-Theme files.

## File Location

Place the `ui/manifest.json` file in your plugin's `ui/` directory, alongside your UI component:

```
your-plugin/
├── plugin_manifest.json          # Backend manifest (existing)
├── ui/
│   ├── manifest.json             # UI manifest (new)
│   ├── YourPluginPage.tsx        # Your UI component
│   └── assets/                   # Optional static assets
└── ...
```

## Schema Definition

### Required Fields

| Field | Type | Description | Example |
|------|------|-------------|---------|
| `plugin_id` | string | The canonical plugin ID that matches your backend plugin name | `"weather-query"` |
| `component` | string | Relative path to your UI component file (without extension) | `"WeatherPluginPage"` |
| `slots` | string[] | Array of slot identifiers where this plugin should render | `["sidebar.plugins"]` |
| `permissions` | string[] | Array of user roles required to access this plugin UI | `["user", "admin", "developer"]` |

### Optional Fields

| Field | Type | Description | Example |
|------|------|-------------|---------|
| `display_name` | string | Human-readable plugin name for UI display | `"Weather Services"` |
| `icon` | string | Relative path to an SVG icon file | `"weather-query---sidebar_00.svg"` |
| `order` | number | Display order for sidebar entries (lower numbers first) | `0` |
| `label` | string | Short label for navigation items | `"Weather"` |

## Complete Example

### Weather Plugin Manifest

```json
{
  "plugin_id": "weather-query",
  "component": "WeatherPluginPage",
  "slots": ["sidebar.plugins"],
  "permissions": ["user", "admin", "developer"],
  "display_name": "Weather Services",
  "icon": "weather-query---sidebar_00.svg",
  "order": 0,
  "label": "Weather"
}
```

### Gmail Plugin Manifest

```json
{
  "plugin_id": "gmail-plugin",
  "component": "GmailPluginPage",
  "slots": ["sidebar.plugins"],
  "permissions": ["user", "admin"],
  "display_name": "Gmail Integration",
  "icon": "gmail-plugin---sidebar_00.svg",
  "order": 1,
  "label": "Gmail"
}
```

## Slot Identifiers

The following slot identifiers are available for plugin contributions:

| Slot ID | Description | Usage |
|---------|-------------|-------|
| `sidebar.plugins` | Main sidebar navigation for plugins | Plugin sidebar entries |
| `page.plugins.overview` | Overview section in plugin management pages | Plugin cards and summaries |
| `page.settings.sections` | Settings page sections | Plugin-specific settings |
| `page.admin.sections` | Admin page sections | Plugin administration panels |

## Permissions

The `permissions` array defines which user roles can access your plugin UI. Supported roles:

- `"user"` - Regular authenticated users
- `"admin"` - System administrators
- `"developer"` - Developers with extended privileges

### Permission Logic

- If `permissions` is empty or not provided, **all authenticated users** can access the plugin
- If `permissions` contains roles, users must have **at least one** of the specified roles
- The Frontend Plugin Host silently hides plugin entries when users don't have required permissions

## Component Path Resolution

The `component` field is resolved relative to your plugin's `ui/` directory:

- `component: "WeatherPluginPage"` → `ui/WeatherPluginPage.tsx`
- `component: "subfolder/MyComponent"` → `ui/subfolder/MyComponent.tsx`

Your component should:

1. Export a default React component function
2. Accept optional `pluginProps` if using slot rendering
3. Handle its own loading states and error boundaries internally

## Integration with Backend Manifest

For backward compatibility, the Frontend Plugin Host will automatically use the `ui` section from your existing `plugin_manifest.json` if no `ui/manifest.json` is present. However, we recommend migrating to the dedicated `ui/manifest.json` file for better separation of concerns.

### Legacy Manifest Support

```json
// plugin_manifest.json (legacy format)
{
  "name": "weather-query",
  "ui": {
    "has_component": true,
    "component_id": "weather-query",
    "menu": [
      {
        "placement": "sidebar",
        "label": "Weather",
        "order": 0,
        "icon": "weather-query---sidebar_00.svg"
      }
    ],
    "rbac": {
      "allowed_roles": ["user", "admin", "developer"]
    }
  }
}
```

## Migration Guide

### From Legacy to New Format

1. **Create `ui/` directory** in your plugin folder
2. **Move your UI component** to `ui/YourPluginPage.tsx`
3. **Create `ui/manifest.json`** with the new schema
4. **Update `plugin_manifest.json`** to remove the `ui` section (optional)

### Example Migration

**Before (legacy):**
```json
// plugin_manifest.json
{
  "name": "weather-query",
  "ui": {
    "has_component": true,
    "component_id": "weather-query",
    "menu": [...],
    "rbac": {...}
  }
}
```

**After (new format):**
```json
// plugin_manifest.json
{
  "name": "weather-query"
  // No ui section needed
}

// ui/manifest.json
{
  "plugin_id": "weather-query",
  "component": "WeatherPluginPage",
  "slots": ["sidebar.plugins"],
  "permissions": ["user", "admin", "developer"],
  "display_name": "Weather Services",
  "icon": "weather-query---sidebar_00.svg",
  "order": 0,
  "label": "Weather"
}
```

## Validation

The Frontend Plugin Host validates your manifest against the schema:

- **Valid manifests** are processed and your plugin UI becomes available
- **Invalid manifests** are logged and your plugin UI is disabled
- **Missing manifests** fall back to legacy format if available

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Missing required field `plugin_id` | Field not present | Add the plugin_id field |
| Invalid slot identifier | Unknown slot name | Use one of the predefined slot IDs |
| Invalid permission role | Unknown role name | Use one of: user, admin, developer |
| Component file not found | File doesn't exist | Create the component file at the specified path |

## Best Practices

### 1. Use Descriptive Names
```json
{
  "display_name": "Weather Forecast Services",
  "label": "Weather"
}
```

### 2. Order Plugins Logically
```json
{
  "order": 0  // First in sidebar
}
```

### 3. Provide Appropriate Permissions
```json
{
  "permissions": ["user"]  // Minimize restrictions
}
```

### 4. Use Consistent Icons
```json
{
  "icon": "your-plugin---sidebar_00.svg"
}
```

### 5. Handle Loading States
Your component should handle its own loading states since it's loaded dynamically.

## Troubleshooting

### Plugin UI Not Showing

1. **Check manifest validity** - Look for console validation errors
2. **Verify permissions** - Ensure your user has the required roles
3. **Check component path** - Confirm the component file exists
4. **Review plugin status** - Ensure backend plugin is active

### Console Errors

- `Validation failed` - Check manifest schema
- `Component not found` - Verify component file path
- `Permission denied` - Check user roles and manifest permissions

### Getting Help

1. Check browser console for validation errors
2. Verify plugin is active in backend
3. Confirm user has required permissions
4. Check that component file exists and is valid React

## Next Steps

Once your manifest is properly configured:

1. Your plugin will appear automatically in the sidebar
2. Your component will be loaded when accessed
3. Plugin health will be monitored in the overview page
4. No changes to core Karen-AI-Theme files are needed

For additional support, consult the main Karen-AI-Theme documentation or reach out to the development team.