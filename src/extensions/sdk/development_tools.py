"""
Development tools for extension development.
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

logger = logging.getLogger(__name__)


if WATCHDOG_AVAILABLE:
    class ExtensionWatcher(FileSystemEventHandler):
        """File system watcher for extension hot reload."""
        
        def __init__(self, extension_path: Path, callback):
            self.extension_path = extension_path
            self.callback = callback
            super().__init__()
        
        def on_modified(self, event):
            if not event.is_directory:
                # Only reload for relevant file changes
                if any(event.src_path.endswith(ext) for ext in ['.py', '.json', '.tsx', '.ts']):
                    logger.info(f"File changed: {event.src_path}")
                    self.callback()
else:
    class ExtensionWatcher:
        """Dummy watcher when watchdog is not available."""
        def __init__(self, extension_path: Path, callback):
            pass


class DevelopmentTools:
    """Tools for extension development and testing."""
    
    def __init__(self, config):
        self.config = config
        self.dev_server_process = None
        self.watcher = None
    
    def run_tests(self, extension_path: Path) -> Dict[str, Any]:
        """
        Run comprehensive tests on an extension.
        
        Args:
            extension_path: Path to extension directory
            
        Returns:
            Test results
        """
        results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "coverage": 0.0,
            "test_files": []
        }
        
        test_dir = extension_path / "tests"
        if not test_dir.exists():
            results["errors"].append("No tests directory found")
            return results
        
        try:
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest",
                str(test_dir),
                "--cov=" + str(extension_path),
                "--cov-report=json",
                "--json-report",
                "--json-report-file=" + str(extension_path / "test-results.json")
            ]
            
            result = subprocess.run(
                cmd,
                cwd=extension_path,
                capture_output=True,
                text=True
            )
            
            # Parse test results
            results_file = extension_path / "test-results.json"
            if results_file.exists():
                with open(results_file) as f:
                    test_data = json.load(f)
                
                results["passed"] = test_data.get("summary", {}).get("passed", 0)
                results["failed"] = test_data.get("summary", {}).get("failed", 0)
                results["test_files"] = [
                    test["nodeid"] for test in test_data.get("tests", [])
                ]
            
            # Parse coverage results
            coverage_file = extension_path / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                results["coverage"] = coverage_data.get("totals", {}).get("percent_covered", 0.0)
            
            if result.returncode != 0:
                results["errors"].append(f"Test execution failed: {result.stderr}")
        
        except Exception as e:
            results["errors"].append(f"Test execution error: {str(e)}")
        
        return results
    
    def start_dev_server(
        self, 
        extension_path: Path,
        watch: bool = True,
        port: int = 8000
    ) -> None:
        """
        Start development server for extension testing.
        
        Args:
            extension_path: Path to extension directory
            watch: Enable file watching for hot reload
            port: Development server port
        """
        try:
            # Start the extension in development mode
            cmd = [
                "python", "-m", "uvicorn",
                "dev_server:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--reload" if watch else "--no-reload"
            ]
            
            # Create development server script
            dev_server_script = extension_path / "dev_server.py"
            self._create_dev_server_script(extension_path, dev_server_script)
            
            self.dev_server_process = subprocess.Popen(
                cmd,
                cwd=extension_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print(f"🚀 Development server started at http://localhost:{port}")
            print(f"📁 Extension: {extension_path.name}")
            
            if watch:
                self._start_file_watcher(extension_path)
            
            # Wait for server to start
            try:
                self.dev_server_process.wait()
            except KeyboardInterrupt:
                self.stop_dev_server()
        
        except Exception as e:
            logger.error(f"Failed to start dev server: {e}")
            raise
    
    def stop_dev_server(self) -> None:
        """Stop the development server."""
        if self.dev_server_process:
            self.dev_server_process.terminate()
            self.dev_server_process = None
            print("🛑 Development server stopped")
        
        if self.watcher:
            self.watcher.stop()
            self.watcher = None
    
    def _create_dev_server_script(self, extension_path: Path, script_path: Path) -> None:
        """Create development server script for the extension."""
        script_content = f'''"""
Development server for {extension_path.name} extension.
"""

import sys
from pathlib import Path

# Add extension to Python path
extension_path = Path(__file__).parent
sys.path.insert(0, str(extension_path))

# Import Kari extension framework
from src.core.extensions.manager import ExtensionManager
from src.core.extensions.base import BaseExtension
from fastapi import FastAPI

# Create FastAPI app
app = FastAPI(title="{extension_path.name} Development Server")

# Load and initialize extension
try:
    # Import the extension
    from . import {extension_path.name.replace('-', '_')}Extension
    
    # Create extension instance
    extension = {extension_path.name.replace('-', '_')}Extension()
    
    # Mount extension routes
    if hasattr(extension, 'get_api_router'):
        router = extension.get_api_router()
        if router:
            app.include_router(router, prefix="/api")
    
    @app.get("/")
    async def root():
        return {{
            "message": "Extension development server",
            "extension": "{extension_path.name}",
            "status": "running"
        }}
    
    @app.get("/health")
    async def health():
        return {{"status": "healthy", "extension": "{extension_path.name}"}}

except Exception as e:
    print(f"Failed to load extension: {{e}}")
    
    @app.get("/")
    async def error_root():
        return {{
            "error": "Extension failed to load",
            "message": str(e)
        }}
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
    
    def _start_file_watcher(self, extension_path: Path) -> None:
        """Start file watcher for hot reload."""
        if not WATCHDOG_AVAILABLE:
            print("⚠️  File watching not available (watchdog not installed)")
            return
        
        def reload_callback():
            print("🔄 Files changed, reloading...")
            # In a real implementation, this would trigger extension reload
        
        event_handler = ExtensionWatcher(extension_path, reload_callback)
        self.watcher = Observer()
        self.watcher.schedule(event_handler, str(extension_path), recursive=True)
        self.watcher.start()
    
    def update_dependencies(self, extension_path: Path) -> None:
        """Update extension dependencies to latest versions."""
        requirements_file = extension_path / "requirements.txt"
        if requirements_file.exists():
            try:
                subprocess.run([
                    "pip", "install", "-r", str(requirements_file), "--upgrade"
                ], check=True)
                print("✅ Dependencies updated successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to update dependencies: {e}")
        else:
            print("⚠️  No requirements.txt found")
    
    def generate_documentation(self, extension_path: Path) -> Path:
        """Generate documentation for an extension."""
        docs_dir = extension_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Generate API documentation
        api_docs_path = docs_dir / "api.md"
        self._generate_api_docs(extension_path, api_docs_path)
        
        # Generate README if it doesn't exist
        readme_path = extension_path / "README.md"
        if not readme_path.exists():
            self._generate_readme(extension_path, readme_path)
        
        print(f"📚 Documentation generated at {docs_dir}")
        return docs_dir
    
    def _generate_api_docs(self, extension_path: Path, output_path: Path) -> None:
        """Generate API documentation from extension code."""
        # This would use tools like sphinx or pydoc to generate API docs
        api_content = f"""# {extension_path.name} API Documentation

## Overview

This document describes the API endpoints provided by the {extension_path.name} extension.

## Endpoints

*API documentation will be automatically generated from your extension code.*

## Models

*Data models will be documented here.*

## Examples

*Usage examples will be provided here.*
"""
        
        with open(output_path, 'w') as f:
            f.write(api_content)
    
    def _generate_readme(self, extension_path: Path, output_path: Path) -> None:
        """Generate README for extension."""
        manifest_path = extension_path / "extension.json"
        extension_name = extension_path.name
        
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            extension_name = manifest.get("display_name", extension_name)
        
        readme_content = f"""# {extension_name}

## Description

*Add a description of your extension here.*

## Installation

```bash
kari-ext install {extension_path.name}
```

## Usage

*Add usage instructions here.*

## Configuration

*Document configuration options here.*

## API Reference

See [API Documentation](docs/api.md) for detailed API reference.

## Development

```bash
# Clone the extension
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt

# Start development server
kari-ext dev --watch

# Run tests
kari-ext test
```

## License

*Add license information here.*
"""
        
        with open(output_path, 'w') as f:
            f.write(readme_content)