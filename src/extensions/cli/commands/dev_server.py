"""
Development server command for hot-reload extension development.
"""

import argparse
import asyncio
import json
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .base import BaseCommand
from ...manager import ExtensionManager


class ExtensionFileHandler(FileSystemEventHandler):
    """File system event handler for extension files."""
    
    def __init__(self, extension_path: Path, callback):
        super().__init__()
        self.extension_path = extension_path
        self.callback = callback
        self.last_reload = 0
        self.reload_delay = 1.0  # Minimum delay between reloads
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Check if it's a relevant file
        file_path = Path(event.src_path)
        if self._should_trigger_reload(file_path):
            current_time = time.time()
            if current_time - self.last_reload > self.reload_delay:
                self.last_reload = current_time
                self.callback(file_path)
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self._should_trigger_reload(file_path):
                self.callback(file_path)
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self._should_trigger_reload(file_path):
                self.callback(file_path)
    
    def _should_trigger_reload(self, file_path: Path) -> bool:
        """Check if file change should trigger a reload."""
        # Only watch relevant file types
        relevant_extensions = {'.py', '.json', '.yaml', '.yml', '.md', '.txt'}
        
        if file_path.suffix not in relevant_extensions:
            return False
        
        # Ignore temporary files and caches
        ignore_patterns = {
            '__pycache__',
            '.pyc',
            '.pyo',
            '.tmp',
            '.temp',
            '.swp',
            '.DS_Store',
            'Thumbs.db'
        }
        
        for pattern in ignore_patterns:
            if pattern in str(file_path):
                return False
        
        return True


class DevServerCommand(BaseCommand):
    """Command to start development server with hot reload."""
    
    def __init__(self):
        self.extension_path: Optional[Path] = None
        self.observer: Optional[Observer] = None
        self.running = False
        self.extension_instance = None
        self.reload_count = 0
        self.extension_manager: Optional[ExtensionManager] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add dev server command arguments."""
        parser.add_argument(
            "path",
            type=Path,
            help="Path to extension directory"
        )
        parser.add_argument(
            "--watch", "-w",
            action="store_true",
            default=True,
            help="Enable file watching for hot reload"
        )
        parser.add_argument(
            "--port", "-p",
            type=int,
            default=8001,
            help="Development server port (default: 8001)"
        )
        parser.add_argument(
            "--host",
            default="localhost",
            help="Development server host (default: localhost)"
        )
        parser.add_argument(
            "--reload-delay",
            type=float,
            default=1.0,
            help="Minimum delay between reloads in seconds"
        )
        parser.add_argument(
            "--validate-on-reload",
            action="store_true",
            default=True,
            help="Validate extension on each reload"
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode"
        )
    
    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        """Execute the dev server command."""
        server = DevServerCommand()
        return server._run_server(args)
    
    def _run_server(self, args: argparse.Namespace) -> int:
        """Run the development server."""
        self.extension_path = args.path
        
        if not self.extension_path.exists():
            self.print_error(f"Extension path '{self.extension_path}' does not exist")
            return 1
        
        if not self.extension_path.is_dir():
            self.print_error(f"Extension path '{self.extension_path}' is not a directory")
            return 1
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initial load
            if not self._load_extension(validate=args.validate_on_reload):
                return 1
            
            # Set up file watching
            if args.watch:
                self._setup_file_watcher(args)
            
            # Start server
            self._start_development_server(args)
            
            return 0
            
        except KeyboardInterrupt:
            self.print_info("Development server stopped by user")
            return 0
        except Exception as e:
            self.print_error(f"Development server failed: {e}")
            return 1
        finally:
            self._cleanup()
    
    def _load_extension(self, validate: bool = True) -> bool:
        """Load or reload the extension."""
        try:
            self.print_info(f"Loading extension from {self.extension_path}")

            # Validate extension if requested
            if validate:
                if not self._validate_extension():
                    return False

            # Load manifest
            manifest = self._load_manifest()
            if not manifest:
                return False

            manager = self._get_extension_manager()
            if not manager:
                self.print_error("Extension manager not available")
                return False

            extension_name = manifest.get("name")
            if not extension_name:
                self.print_error("Extension manifest is missing a name")
                return False

            if self.reload_count > 0:
                record = self._run_async(manager.reload_extension(extension_name))
            else:
                record = self._run_async(manager.load_extension(extension_name))

            if not record or not record.instance:
                self.print_error(
                    f"Failed to load extension runtime for '{extension_name}'"
                )
                return False

            self.extension_instance = record.instance
            self.print_success(
                f"Extension '{extension_name}' loaded successfully"
            )
            manifest_data: Dict[str, Any] = record.manifest.model_dump()
            self._print_development_info(manifest_data)

            if self.reload_count > 0:
                self.print_info(f"Reload #{self.reload_count} completed")

            return True

        except Exception as e:
            self.print_error(f"Failed to load extension: {e}")
            return False
    
    def _validate_extension(self) -> bool:
        """Validate the extension."""
        from .validate import ValidateCommand
        
        results = ValidateCommand._validate_extension(self.extension_path, strict=False)
        
        if results["errors"]:
            self.print_error("Extension validation failed:")
            for error in results["errors"]:
                print(f"  • {error}")
            return False
        
        if results["warnings"]:
            self.print_warning("Extension has warnings:")
            for warning in results["warnings"]:
                print(f"  • {warning}")
        
        return True
    
    def _load_manifest(self) -> Optional[Dict[str, Any]]:
        """Load extension manifest."""
        manifest_path = self.extension_path / "extension.json"
        
        if not manifest_path.exists():
            self.print_error("Missing extension.json manifest file")
            return None
        
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.print_error(f"Invalid JSON in manifest: {e}")
            return None
        except Exception as e:
            self.print_error(f"Error reading manifest: {e}")
            return None
    
    def _setup_file_watcher(self, args: argparse.Namespace) -> None:
        """Set up file system watcher for hot reload."""
        self.print_info("Setting up file watcher for hot reload...")

        def on_file_change(file_path: Path):
            self.print_info(f"File changed: {file_path.relative_to(self.extension_path)}")
            self.reload_count += 1
            self._load_extension(validate=args.validate_on_reload)
        
        event_handler = ExtensionFileHandler(self.extension_path, on_file_change)
        event_handler.reload_delay = args.reload_delay
        
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.extension_path), recursive=True)
        self.observer.start()
        
        self.print_success("File watcher started")
    
    def _start_development_server(self, args: argparse.Namespace) -> None:
        """Start the development server."""
        self.running = True
        
        self.print_success(f"🚀 Development server started!")
        self.print_info(f"Extension: {self.extension_path.name}")
        self.print_info(f"Path: {self.extension_path}")
        self.print_info(f"Host: {args.host}:{args.port}")
        
        if args.watch:
            self.print_info("📁 Watching for file changes...")
        
        self.print_info("Press Ctrl+C to stop the server")
        
        # Keep the server running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def _get_extension_manager(self) -> Optional[ExtensionManager]:
        """Create (or retrieve) the extension manager for the dev session."""
        if not self.extension_path:
            return None

        if not self.extension_manager:
            extension_root = self.extension_path.parent
            manager = ExtensionManager(extension_root=extension_root)

            try:
                self._run_async(manager.initialize())
            except Exception as exc:
                self.print_error(f"Failed to initialize extension manager: {exc}")
                return None

            self.extension_manager = manager

        return self.extension_manager

    def _ensure_event_loop(self) -> asyncio.AbstractEventLoop:
        """Ensure there is a background event loop for async extension ops."""
        if not self._event_loop:
            self._event_loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(
                target=self._event_loop_runner,
                name="kari-extension-dev-loop",
                daemon=True,
            )
            self._loop_thread.start()

        return self._event_loop

    def _event_loop_runner(self) -> None:
        """Run the event loop in a dedicated background thread."""
        assert self._event_loop is not None
        asyncio.set_event_loop(self._event_loop)
        try:
            self._event_loop.run_forever()
        finally:
            self._event_loop.close()

    def _run_async(self, coroutine):
        """Synchronously execute an async coroutine on the background loop."""
        loop = self._ensure_event_loop()
        future = asyncio.run_coroutine_threadsafe(coroutine, loop)
        return future.result()

    def _stop_event_loop(self) -> None:
        """Stop and clean up the background event loop."""
        if not self._event_loop:
            return

        self._event_loop.call_soon_threadsafe(self._event_loop.stop)

        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join()

        self._event_loop = None
        self._loop_thread = None

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.print_info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _cleanup(self):
        """Clean up resources."""
        if self.observer:
            self.observer.stop()
            self.observer.join()

        if self.extension_manager:
            try:
                self._run_async(self.extension_manager.shutdown())
            except Exception as exc:
                self.print_warning(f"Error shutting down extension manager: {exc}")
            finally:
                self.extension_manager = None
                self.extension_instance = None

        if self._event_loop:
            self._stop_event_loop()

        self.print_info("Development server stopped")
    
    def _print_development_info(self, manifest: Dict[str, Any]) -> None:
        """Print development information."""
        print("\n" + "="*50)
        print("🔧 DEVELOPMENT MODE")
        print("="*50)
        
        print(f"Extension: {manifest.get('display_name', manifest.get('name'))}")
        print(f"Version: {manifest.get('version')}")
        print(f"Author: {manifest.get('author')}")
        
        capabilities = manifest.get('capabilities', {})
        enabled_caps = [k.replace('provides_', '') for k, v in capabilities.items() if v]
        if enabled_caps:
            print(f"Capabilities: {', '.join(enabled_caps)}")
        
        # Show API endpoints if available
        api_config = manifest.get('api', {})
        if api_config.get('endpoints'):
            print(f"\n🌐 API Endpoints:")
            prefix = api_config.get('prefix', '')
            for endpoint in api_config['endpoints']:
                methods = ', '.join(endpoint.get('methods', ['GET']))
                path = prefix + endpoint.get('path', '')
                print(f"  {methods} {path}")
        
        # Show UI pages if available
        ui_config = manifest.get('ui', {})
        if ui_config.get('control_room_pages'):
            print(f"\n🖥️  UI Pages:")
            for page in ui_config['control_room_pages']:
                print(f"  {page.get('name')} - {page.get('path')}")
        
        # Show background tasks if available
        bg_tasks = manifest.get('background_tasks', [])
        if bg_tasks:
            print(f"\n⏰ Background Tasks:")
            for task in bg_tasks:
                print(f"  {task.get('name')} - {task.get('schedule')}")
        
        print("="*50)
        print("Ready for development! 🎉")
        print("="*50 + "\n")