"""
File Connector - File system knowledge ingestion

This connector handles file system sources with glob patterns,
file watchers, and incremental updates for local file ingestion.
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, AsyncGenerator
import glob
import mimetypes

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

from .base_connector import BaseConnector, ConnectorType, ChangeDetection, ChangeType

try:
    from llama_index.core import Document
except ImportError:
    Document = None


class FileWatchHandler(FileSystemEventHandler):
    """File system event handler for real-time change detection."""
    
    def __init__(self, connector: 'FileConnector'):
        self.connector = connector
        self.logger = logging.getLogger(__name__)
    
    def on_created(self, event):
        if not event.is_directory:
            asyncio.create_task(self.connector._handle_file_event(event.src_path, ChangeType.CREATED))
    
    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(self.connector._handle_file_event(event.src_path, ChangeType.MODIFIED))
    
    def on_deleted(self, event):
        if not event.is_directory:
            asyncio.create_task(self.connector._handle_file_event(event.src_path, ChangeType.DELETED))
    
    def on_moved(self, event):
        if not event.is_directory:
            asyncio.create_task(self.connector._handle_file_event(event.dest_path, ChangeType.MOVED))


class FileConnector(BaseConnector):
    """
    Connector for ingesting knowledge from file system sources.
    Supports glob patterns, file watching, and incremental updates.
    """
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        super().__init__(connector_id, ConnectorType.FILE, config)
        
        # File-specific configuration
        self.root_paths = config.get("root_paths", [])
        self.glob_patterns = config.get("glob_patterns", ["**/*"])
        self.recursive = config.get("recursive", True)
        self.follow_symlinks = config.get("follow_symlinks", False)
        self.watch_enabled = config.get("watch_enabled", False) and WATCHDOG_AVAILABLE
        
        # File processing configuration
        self.encoding = config.get("encoding", "utf-8")
        self.encoding_errors = config.get("encoding_errors", "ignore")
        self.extract_metadata = config.get("extract_metadata", True)
        
        # File watching
        self.observer: Optional[Observer] = None
        self.watch_handler: Optional[FileWatchHandler] = None
        self.pending_changes: List[ChangeDetection] = []
        
        # Supported file types
        self.text_extensions = {
            '.txt', '.md', '.rst', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h',
            '.css', '.html', '.xml', '.json', '.yaml', '.yml', '.toml', '.ini',
            '.sql', '.sh', '.bat', '.ps1', '.dockerfile', '.gitignore', '.env'
        }
        
        # Initialize file watching if enabled
        if self.watch_enabled:
            asyncio.create_task(self._setup_file_watching())
    
    async def _setup_file_watching(self):
        """Set up file system watching for real-time updates."""
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("Watchdog not available - file watching disabled")
            return
        
        try:
            self.watch_handler = FileWatchHandler(self)
            self.observer = Observer()
            
            for root_path in self.root_paths:
                if os.path.exists(root_path):
                    self.observer.schedule(
                        self.watch_handler,
                        root_path,
                        recursive=self.recursive
                    )
                    self.logger.info(f"Watching directory: {root_path}")
            
            self.observer.start()
            self.logger.info("File watching started")
        
        except Exception as e:
            self.logger.error(f"Failed to setup file watching: {e}")
    
    async def _handle_file_event(self, file_path: str, change_type: ChangeType):
        """Handle file system events from watcher."""
        try:
            if self._should_process_file(file_path):
                change = ChangeDetection(
                    source_path=file_path,
                    change_type=change_type,
                    timestamp=datetime.utcnow(),
                    metadata={"watched": True}
                )
                self.pending_changes.append(change)
                self.logger.debug(f"Detected file {change_type.value}: {file_path}")
        
        except Exception as e:
            self.logger.error(f"Error handling file event for {file_path}: {e}")
    
    async def scan_sources(self) -> AsyncGenerator[Document, None]:
        """Scan file system sources and yield documents."""
        try:
            processed_files = set()
            
            for root_path in self.root_paths:
                if not os.path.exists(root_path):
                    self.logger.warning(f"Root path does not exist: {root_path}")
                    continue
                
                async for document in self._scan_directory(root_path, processed_files):
                    yield document
        
        except Exception as e:
            self.logger.error(f"Error scanning file sources: {e}")
    
    async def _scan_directory(self, root_path: str, processed_files: Set[str]) -> AsyncGenerator[Document, None]:
        """Scan a directory for files matching patterns."""
        try:
            for pattern in self.glob_patterns:
                full_pattern = os.path.join(root_path, pattern)
                
                for file_path in glob.glob(full_pattern, recursive=self.recursive):
                    # Avoid processing the same file multiple times
                    if file_path in processed_files:
                        continue
                    
                    processed_files.add(file_path)
                    
                    # Check if file should be processed
                    if not os.path.isfile(file_path):
                        continue
                    
                    file_size = os.path.getsize(file_path)
                    if not self._should_process_file(file_path, file_size):
                        continue
                    
                    # Process file
                    document = await self._process_file(file_path)
                    if document:
                        yield document
                        
                        # Yield control periodically
                        await asyncio.sleep(0.001)
        
        except Exception as e:
            self.logger.error(f"Error scanning directory {root_path}: {e}")
    
    async def _process_file(self, file_path: str) -> Optional[Document]:
        """Process a single file and create a document."""
        try:
            # Check if file is text-based
            if not self._is_text_file(file_path):
                return None
            
            # Read file content
            content = await self._read_file_content(file_path)
            if not content:
                return None
            
            # Extract metadata
            metadata = await self.get_source_metadata(file_path)
            
            # Create document
            document = self._create_document(content, file_path, metadata)
            
            return document
        
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def _is_text_file(self, file_path: str) -> bool:
        """Determine if file is text-based and should be processed."""
        # Check extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() in self.text_extensions:
            return True
        
        # Use mimetype detection
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('text/'):
            return True
        
        # Try to detect by reading first few bytes
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(1024)
                # Check if sample contains mostly printable characters
                try:
                    sample.decode('utf-8')
                    return True
                except UnicodeDecodeError:
                    return False
        except Exception:
            return False
    
    async def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content with proper encoding handling."""
        try:
            with open(file_path, 'r', encoding=self.encoding, errors=self.encoding_errors) as f:
                content = f.read()
            
            # Basic content validation
            if len(content.strip()) == 0:
                return None
            
            return content
        
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    async def detect_changes(self) -> List[ChangeDetection]:
        """Detect changes in file system sources."""
        changes = []
        
        try:
            # Include pending changes from file watcher
            if self.pending_changes:
                changes.extend(self.pending_changes)
                self.pending_changes.clear()
            
            # Scan for changes if not using file watcher or for initial scan
            if not self.watch_enabled or self.last_scan_time is None:
                changes.extend(await self._scan_for_changes())
            
        except Exception as e:
            self.logger.error(f"Error detecting changes: {e}")
        
        return changes
    
    async def _scan_for_changes(self) -> List[ChangeDetection]:
        """Scan file system for changes since last scan."""
        changes = []
        current_files = set()
        
        try:
            for root_path in self.root_paths:
                if not os.path.exists(root_path):
                    continue
                
                for pattern in self.glob_patterns:
                    full_pattern = os.path.join(root_path, pattern)
                    
                    for file_path in glob.glob(full_pattern, recursive=self.recursive):
                        if not os.path.isfile(file_path):
                            continue
                        
                        current_files.add(file_path)
                        
                        # Check if file should be processed
                        file_size = os.path.getsize(file_path)
                        if not self._should_process_file(file_path, file_size):
                            continue
                        
                        # Check for changes
                        change = await self._check_file_change(file_path)
                        if change:
                            changes.append(change)
            
            # Check for deleted files
            if self.source_checksums:
                tracked_files = set(self.source_checksums.keys())
                deleted_files = tracked_files - current_files
                
                for deleted_file in deleted_files:
                    changes.append(ChangeDetection(
                        source_path=deleted_file,
                        change_type=ChangeType.DELETED,
                        timestamp=datetime.utcnow(),
                        old_checksum=self.source_checksums.get(deleted_file)
                    ))
        
        except Exception as e:
            self.logger.error(f"Error scanning for changes: {e}")
        
        return changes
    
    async def _check_file_change(self, file_path: str) -> Optional[ChangeDetection]:
        """Check if a specific file has changed."""
        try:
            # Get file stats
            stat = os.stat(file_path)
            file_mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # Check if file is new
            if file_path not in self.source_checksums:
                return ChangeDetection(
                    source_path=file_path,
                    change_type=ChangeType.CREATED,
                    timestamp=file_mtime
                )
            
            # Check if file was modified since last scan
            if self.last_scan_time and file_mtime > self.last_scan_time:
                # Calculate new checksum to confirm change
                content = await self._read_file_content(file_path)
                if content:
                    new_checksum = self._calculate_checksum(content)
                    old_checksum = self.source_checksums.get(file_path)
                    
                    if new_checksum != old_checksum:
                        return ChangeDetection(
                            source_path=file_path,
                            change_type=ChangeType.MODIFIED,
                            timestamp=file_mtime,
                            old_checksum=old_checksum,
                            new_checksum=new_checksum
                        )
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error checking file change for {file_path}: {e}")
            return None
    
    async def get_source_metadata(self, source_path: str) -> Dict[str, Any]:
        """Get metadata for a file source."""
        metadata = {
            "source_type": "file",
            "file_path": source_path,
            "connector_id": self.connector_id
        }
        
        try:
            if os.path.exists(source_path):
                stat = os.stat(source_path)
                
                metadata.update({
                    "file_size": stat.st_size,
                    "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "file_extension": os.path.splitext(source_path)[1],
                    "file_name": os.path.basename(source_path),
                    "directory": os.path.dirname(source_path)
                })
                
                # Add MIME type
                mime_type, encoding = mimetypes.guess_type(source_path)
                if mime_type:
                    metadata["mime_type"] = mime_type
                if encoding:
                    metadata["encoding"] = encoding
                
                # Extract additional metadata if enabled
                if self.extract_metadata:
                    additional_metadata = await self._extract_file_metadata(source_path)
                    metadata.update(additional_metadata)
        
        except Exception as e:
            self.logger.error(f"Error getting metadata for {source_path}: {e}")
        
        return metadata
    
    async def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract additional metadata from file content."""
        metadata = {}
        
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Extract language-specific metadata
            if ext in ['.py']:
                metadata.update(await self._extract_python_metadata(file_path))
            elif ext in ['.js', '.ts']:
                metadata.update(await self._extract_javascript_metadata(file_path))
            elif ext in ['.md', '.rst']:
                metadata.update(await self._extract_markdown_metadata(file_path))
            elif ext in ['.json']:
                metadata.update(await self._extract_json_metadata(file_path))
            elif ext in ['.yaml', '.yml']:
                metadata.update(await self._extract_yaml_metadata(file_path))
        
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {file_path}: {e}")
        
        return metadata
    
    async def _extract_python_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract Python-specific metadata."""
        metadata = {"language": "python"}
        
        try:
            content = await self._read_file_content(file_path)
            if content:
                # Count lines of code
                lines = content.split('\n')
                metadata["line_count"] = len(lines)
                metadata["non_empty_lines"] = len([l for l in lines if l.strip()])
                
                # Detect imports
                imports = []
                for line in lines[:50]:  # Check first 50 lines
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line)
                
                if imports:
                    metadata["imports"] = imports[:10]  # Limit to first 10
                
                # Detect docstring
                if '"""' in content or "'''" in content:
                    metadata["has_docstring"] = True
        
        except Exception as e:
            self.logger.error(f"Error extracting Python metadata: {e}")
        
        return metadata
    
    async def _extract_javascript_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract JavaScript/TypeScript-specific metadata."""
        metadata = {"language": "javascript"}
        
        if file_path.endswith('.ts'):
            metadata["language"] = "typescript"
        
        try:
            content = await self._read_file_content(file_path)
            if content:
                # Count lines
                lines = content.split('\n')
                metadata["line_count"] = len(lines)
                
                # Detect imports/requires
                imports = []
                for line in lines[:50]:
                    line = line.strip()
                    if (line.startswith('import ') or 
                        line.startswith('const ') and 'require(' in line or
                        line.startswith('require(')):
                        imports.append(line)
                
                if imports:
                    metadata["imports"] = imports[:10]
        
        except Exception as e:
            self.logger.error(f"Error extracting JavaScript metadata: {e}")
        
        return metadata
    
    async def _extract_markdown_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract Markdown-specific metadata."""
        metadata = {"language": "markdown"}
        
        try:
            content = await self._read_file_content(file_path)
            if content:
                lines = content.split('\n')
                metadata["line_count"] = len(lines)
                
                # Extract headers
                headers = []
                for line in lines:
                    line = line.strip()
                    if line.startswith('#'):
                        headers.append(line)
                
                if headers:
                    metadata["headers"] = headers[:10]
                
                # Check for front matter
                if content.startswith('---'):
                    metadata["has_frontmatter"] = True
        
        except Exception as e:
            self.logger.error(f"Error extracting Markdown metadata: {e}")
        
        return metadata
    
    async def _extract_json_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract JSON-specific metadata."""
        metadata = {"language": "json"}
        
        try:
            content = await self._read_file_content(file_path)
            if content:
                import json as json_module
                data = json_module.loads(content)
                
                metadata["json_keys"] = list(data.keys()) if isinstance(data, dict) else []
                metadata["json_type"] = type(data).__name__
        
        except Exception as e:
            self.logger.error(f"Error extracting JSON metadata: {e}")
        
        return metadata
    
    async def _extract_yaml_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract YAML-specific metadata."""
        metadata = {"language": "yaml"}
        
        try:
            content = await self._read_file_content(file_path)
            if content:
                # Simple YAML key extraction (without full YAML parsing)
                lines = content.split('\n')
                keys = []
                for line in lines:
                    line = line.strip()
                    if ':' in line and not line.startswith('#'):
                        key = line.split(':')[0].strip()
                        if key:
                            keys.append(key)
                
                if keys:
                    metadata["yaml_keys"] = keys[:20]
        
        except Exception as e:
            self.logger.error(f"Error extracting YAML metadata: {e}")
        
        return metadata
    
    async def validate_configuration(self) -> List[str]:
        """Validate file connector configuration."""
        errors = await super().validate_configuration()
        
        # Check root paths
        if not self.root_paths:
            errors.append("At least one root path is required")
        else:
            for root_path in self.root_paths:
                if not os.path.exists(root_path):
                    errors.append(f"Root path does not exist: {root_path}")
        
        # Check glob patterns
        if not self.glob_patterns:
            errors.append("At least one glob pattern is required")
        
        # Check file watching requirements
        if self.watch_enabled and not WATCHDOG_AVAILABLE:
            errors.append("File watching enabled but watchdog library not available")
        
        return errors
    
    async def cleanup(self):
        """Clean up resources used by the connector."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("File watching stopped")
    
    def __del__(self):
        """Cleanup when connector is destroyed."""
        if hasattr(self, 'observer') and self.observer:
            try:
                self.observer.stop()
            except Exception:
                pass