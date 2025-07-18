# Example Extensions

This directory contains example extensions that demonstrate various capabilities of the Kari AI extension system.

## Available Examples

### hello-extension
A simple example extension that demonstrates:
- Basic extension structure and lifecycle
- API endpoint creation
- Plugin orchestration
- MCP tool registration and consumption
- UI component integration

## Learning Path

1. **Start with hello-extension** - Learn the basic extension structure
2. **Study the manifest** - Understand extension configuration
3. **Explore MCP integration** - See how extensions expose and consume tools
4. **Review API creation** - Learn how to add custom endpoints
5. **Examine plugin orchestration** - Understand how to compose plugins

## Creating Your Own Extension

Use these examples as templates for creating your own extensions:

```bash
# Copy the hello-extension as a starting point
cp -r extensions/examples/hello-extension extensions/examples/my-extension

# Update the extension.json manifest
# Modify the __init__.py implementation
# Test your extension
```

## Best Practices Demonstrated

- Proper error handling and logging
- Resource management and limits
- Security considerations
- Testing strategies
- Documentation standards