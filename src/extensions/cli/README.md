# Extension Development CLI Tools

A comprehensive command-line interface for developing, testing, and packaging Kari AI extensions.

## Installation

The CLI tools are automatically available when you install the Kari AI platform:

```bash
pip install -e .
```

This makes the `kari-ext` command available globally.

## Commands

### `create` - Extension Scaffolding

Generate new extensions from templates:

```bash
# Create a basic extension
kari-ext create my-extension --template basic

# Create with custom details
kari-ext create my-extension \
  --template full \
  --author "Your Name" \
  --description "My awesome extension" \
  --output-dir ./extensions
```

**Available Templates:**
- `basic` - Extension with API and UI (default)
- `api-only` - API-only extension without UI
- `ui-only` - UI-only extension without API
- `background-task` - Extension with scheduled tasks
- `full` - Full-featured extension with all capabilities

**Options:**
- `--template, -t` - Template to use
- `--output-dir, -o` - Output directory (default: ./extensions)
- `--author` - Extension author name
- `--description` - Extension description
- `--force, -f` - Overwrite existing directory

### `validate` - Extension Validation

Validate extension structure and manifest:

```bash
# Basic validation
kari-ext validate ./my-extension

# Strict validation with auto-fix
kari-ext validate ./my-extension --strict --fix

# JSON output
kari-ext validate ./my-extension --output-format json
```

**Options:**
- `--strict` - Enable strict validation mode
- `--fix` - Attempt to fix common issues automatically
- `--output-format` - Output format: text, json

**Validation Checks:**
- Manifest file structure and required fields
- Directory structure and required files
- Python syntax validation
- Security checks for dangerous imports
- Dependency validation

### `test` - Extension Testing

Run extension test suites:

```bash
# Run all tests
kari-ext test ./my-extension

# Run with coverage
kari-ext test ./my-extension --coverage

# Run specific tests
kari-ext test ./my-extension --filter "test_api"

# Parallel execution
kari-ext test ./my-extension --parallel 4
```

**Options:**
- `--pattern, -p` - Test file pattern (default: test_*.py)
- `--verbose, -v` - Verbose output
- `--coverage` - Generate coverage report
- `--parallel, -j` - Number of parallel workers
- `--filter, -k` - Filter tests by keyword
- `--markers, -m` - Run tests with specific markers
- `--output-format` - Output format: text, junit, json
- `--fail-fast, -x` - Stop on first failure

### `package` - Extension Packaging

Package extensions for distribution:

```bash
# Create ZIP package
kari-ext package ./my-extension

# Create tar.gz package
kari-ext package ./my-extension --format tar.gz

# Custom output location
kari-ext package ./my-extension --output ./dist/my-extension-1.0.0.zip

# Include development files
kari-ext package ./my-extension --include-dev
```

**Options:**
- `--output, -o` - Output file path
- `--format, -f` - Package format: zip, tar.gz, tar.bz2
- `--exclude` - Exclude patterns (can be used multiple times)
- `--include-dev` - Include development files
- `--validate` - Validate before packaging (default: true)
- `--sign` - Sign the package
- `--metadata-only` - Generate only metadata files

### `dev-server` - Development Server

Start development server with hot reload:

```bash
# Start development server
kari-ext dev-server ./my-extension

# Custom port and host
kari-ext dev-server ./my-extension --port 8002 --host 0.0.0.0

# Disable file watching
kari-ext dev-server ./my-extension --no-watch
```

**Options:**
- `--watch, -w` - Enable file watching (default: true)
- `--port, -p` - Server port (default: 8001)
- `--host` - Server host (default: localhost)
- `--reload-delay` - Minimum delay between reloads (default: 1.0s)
- `--validate-on-reload` - Validate on each reload (default: true)
- `--debug` - Enable debug mode

## Extension Templates

### Basic Template

Creates an extension with:
- API endpoints (`/status`, `/health`)
- UI dashboard component
- Test structure
- README and documentation

### API-Only Template

Creates an extension with:
- API endpoints only
- No UI components
- Focused on backend functionality

### UI-Only Template

Creates an extension with:
- UI components only
- No API endpoints
- Focused on frontend functionality

### Background Task Template

Creates an extension with:
- Scheduled background tasks
- Task management and monitoring
- No UI or API components

### Full Template

Creates a comprehensive extension with:
- Complete API with CRUD operations
- Rich UI with dashboard and settings
- Background tasks for automation
- Plugin orchestration capabilities
- Data management and configuration
- Comprehensive test suite

## Development Workflow

1. **Create Extension**
   ```bash
   kari-ext create my-extension --template basic
   cd extensions/my-extension
   ```

2. **Validate Structure**
   ```bash
   kari-ext validate . --fix
   ```

3. **Start Development Server**
   ```bash
   kari-ext dev-server . --watch
   ```

4. **Run Tests**
   ```bash
   kari-ext test . --coverage
   ```

5. **Package for Distribution**
   ```bash
   kari-ext package .
   ```

## Configuration

### Extension Manifest

The `extension.json` file defines your extension:

```json
{
  "name": "my-extension",
  "version": "1.0.0",
  "display_name": "My Extension",
  "description": "A custom extension",
  "author": "Your Name",
  "capabilities": {
    "provides_ui": true,
    "provides_api": true,
    "provides_background_tasks": false,
    "provides_webhooks": false
  },
  "permissions": {
    "data_access": ["read", "write"],
    "plugin_access": [],
    "system_access": [],
    "network_access": []
  },
  "resources": {
    "max_memory_mb": 128,
    "max_cpu_percent": 10,
    "max_disk_mb": 256
  }
}
```

### Directory Structure

```
my-extension/
├── extension.json          # Extension manifest
├── __init__.py            # Main extension class
├── README.md              # Documentation
├── api/                   # API endpoints
│   ├── __init__.py
│   ├── routes.py
│   └── models.py
├── ui/                    # UI components
│   ├── __init__.py
│   └── components.py
├── tasks/                 # Background tasks
│   ├── __init__.py
│   └── scheduler.py
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_extension.py
│   └── test_api.py
└── config/                # Configuration
    ├── __init__.py
    └── settings.py
```

## Testing

The CLI tools include comprehensive testing capabilities:

```bash
# Run CLI tests
python -m pytest src/extensions/cli/tests/

# Run demo
python -m src.extensions.cli.demo
```

## Examples

### Create and Test Extension

```bash
# Create extension
kari-ext create demo-extension --template full --author "Demo User"

# Validate
kari-ext validate ./extensions/demo-extension

# Run tests
kari-ext test ./extensions/demo-extension --coverage

# Start dev server
kari-ext dev-server ./extensions/demo-extension --watch

# Package
kari-ext package ./extensions/demo-extension
```

### Batch Operations

```bash
# Validate all extensions
find ./extensions -name "extension.json" -execdir kari-ext validate . \;

# Test all extensions
find ./extensions -name "extension.json" -execdir kari-ext test . \;

# Package all extensions
find ./extensions -name "extension.json" -execdir kari-ext package . \;
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the Kari platform is properly installed
2. **Permission Errors**: Check file permissions in extension directory
3. **Validation Failures**: Use `--fix` flag to auto-correct common issues
4. **Test Failures**: Ensure pytest and pytest-asyncio are installed

### Debug Mode

Enable debug output:

```bash
export KARI_DEBUG=1
kari-ext dev-server ./my-extension --debug
```

### Getting Help

```bash
# General help
kari-ext --help

# Command-specific help
kari-ext create --help
kari-ext validate --help
kari-ext test --help
kari-ext package --help
kari-ext dev-server --help
```

## Contributing

The CLI tools are part of the Kari AI extension system. To contribute:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see the main project LICENSE file for details.