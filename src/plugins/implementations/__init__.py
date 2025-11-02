"""
Plugin Implementations Directory

This directory contains all plugin implementations organized by category.
Plugins are simple, focused functions that extend system capabilities.

Directory Structure:
- examples/: Example plugins for learning and templates
- core/: Core system plugins (time, TUI fallback, etc.)
- ai/: AI and LLM-related plugins
- integrations/: Third-party service integrations
- automation/: Automation and workflow plugins

Each plugin should have:
- plugin_manifest.json: Plugin metadata and configuration
- handler.py: Main plugin implementation
- README.md: Documentation and usage instructions
"""

# This is a namespace package for plugin implementations
# Individual plugins are loaded dynamically by the plugin framework