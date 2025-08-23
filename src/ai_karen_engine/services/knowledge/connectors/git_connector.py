"""
Git Connector - Git repository knowledge ingestion

This connector handles Git repositories with branch filtering,
change detection, and incremental updates based on Git history.
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, AsyncGenerator, Tuple
from pathlib import Path

from .base_connector import BaseConnector, ConnectorType, ChangeDetection, ChangeType

try:
    from llama_index.core import Document
except ImportError:
    Document = None


class GitConnector(BaseConnector):
    """
    Connector for ingesting knowledge from Git repositories.
    Supports branch filtering, change detection via Git history,
    and incremental updates based on commits.
    """
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        super().__init__(connector_id, ConnectorType.GIT, config)
        
        # Git-specific configuration
        self.repo_path = config.get("repo_path", ".")
        self.branches = config.get("branches", ["main", "master"])
        self.current_branch = config.get("current_branch", "main")
        self.include_history = config.get("include_history", False)
        self.max_history_days = config.get("max_history_days", 30)
        
        # Git filtering
        self.include_paths = config.get("include_paths", [])
        self.exclude_paths = config.get("exclude_paths", [".git/", "__pycache__/", "node_modules/"])
        
        # Change detection
        self.last_commit_hash: Optional[str] = None
        self.tracked_commits: Set[str] = set()
        
        # Git command configuration
        self.git_timeout = config.get("git_timeout", 30)
    
    async def scan_sources(self) -> AsyncGenerator[Document, None]:
        """Scan Git repository and yield documents."""
        try:
            # Validate repository
            if not await self._is_git_repository():
                self.logger.error(f"Path is not a Git repository: {self.repo_path}")
                return
            
            # Switch to target branch if needed
            await self._ensure_branch(self.current_branch)
            
            # Get files to process
            files_to_process = await self._get_repository_files()
            
            for file_path in files_to_process:
                document = await self._process_git_file(file_path)
                if document:
                    yield document
                    await asyncio.sleep(0.001)  # Yield control
        
        except Exception as e:
            self.logger.error(f"Error scanning Git repository: {e}")
    
    async def detect_changes(self) -> List[ChangeDetection]:
        """Detect changes in Git repository since last scan."""
        changes = []
        
        try:
            if not await self._is_git_repository():
                return changes
            
            # Get current commit hash
            current_commit = await self._get_current_commit_hash()
            
            if self.last_commit_hash and current_commit != self.last_commit_hash:
                # Get changes between commits
                git_changes = await self._get_changes_between_commits(
                    self.last_commit_hash, current_commit
                )
                changes.extend(git_changes)
            elif self.last_commit_hash is None:
                # First scan - get recent changes
                recent_changes = await self._get_recent_changes()
                changes.extend(recent_changes)
            
            # Update last commit hash
            self.last_commit_hash = current_commit
        
        except Exception as e:
            self.logger.error(f"Error detecting Git changes: {e}")
        
        return changes
    
    async def get_source_metadata(self, source_path: str) -> Dict[str, Any]:
        """Get Git-specific metadata for a file."""
        metadata = {
            "source_type": "git",
            "file_path": source_path,
            "repository_path": self.repo_path,
            "connector_id": self.connector_id
        }
        
        try:
            # Get Git file information
            git_info = await self._get_file_git_info(source_path)
            metadata.update(git_info)
            
            # Get file system metadata
            full_path = os.path.join(self.repo_path, source_path)
            if os.path.exists(full_path):
                stat = os.stat(full_path)
                metadata.update({
                    "file_size": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "file_extension": os.path.splitext(source_path)[1],
                    "file_name": os.path.basename(source_path),
                    "directory": os.path.dirname(source_path)
                })
        
        except Exception as e:
            self.logger.error(f"Error getting Git metadata for {source_path}: {e}")
        
        return metadata
    
    async def _is_git_repository(self) -> bool:
        """Check if the path is a valid Git repository."""
        try:
            result = await self._run_git_command(["rev-parse", "--git-dir"])
            return result.returncode == 0
        except Exception:
            return False
    
    async def _ensure_branch(self, branch_name: str) -> bool:
        """Ensure we're on the specified branch."""
        try:
            # Check current branch
            result = await self._run_git_command(["branch", "--show-current"])
            if result.returncode == 0:
                current_branch = result.stdout.strip()
                if current_branch == branch_name:
                    return True
            
            # Try to switch to branch
            result = await self._run_git_command(["checkout", branch_name])
            if result.returncode == 0:
                self.logger.info(f"Switched to branch: {branch_name}")
                return True
            else:
                self.logger.warning(f"Failed to switch to branch {branch_name}: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error ensuring branch {branch_name}: {e}")
            return False
    
    async def _get_repository_files(self) -> List[str]:
        """Get list of files in the repository to process."""
        try:
            # Use git ls-files to get tracked files
            result = await self._run_git_command(["ls-files"])
            if result.returncode != 0:
                return []
            
            all_files = result.stdout.strip().split('\n')
            filtered_files = []
            
            for file_path in all_files:
                if not file_path:
                    continue
                
                # Apply include/exclude filters
                if self._should_include_git_file(file_path):
                    full_path = os.path.join(self.repo_path, file_path)
                    if os.path.exists(full_path):
                        file_size = os.path.getsize(full_path)
                        if self._should_process_file(file_path, file_size):
                            filtered_files.append(file_path)
            
            return filtered_files
        
        except Exception as e:
            self.logger.error(f"Error getting repository files: {e}")
            return []
    
    def _should_include_git_file(self, file_path: str) -> bool:
        """Check if Git file should be included based on path filters."""
        # Check exclude paths
        for exclude_path in self.exclude_paths:
            if file_path.startswith(exclude_path):
                return False
        
        # Check include paths (if specified)
        if self.include_paths:
            for include_path in self.include_paths:
                if file_path.startswith(include_path):
                    return True
            return False  # Not in include list
        
        return True
    
    async def _process_git_file(self, file_path: str) -> Optional[Document]:
        """Process a Git-tracked file and create a document."""
        try:
            full_path = os.path.join(self.repo_path, file_path)
            
            # Read file content
            content = await self._read_git_file_content(full_path)
            if not content:
                return None
            
            # Get metadata
            metadata = await self.get_source_metadata(file_path)
            
            # Create document
            document = self._create_document(content, file_path, metadata)
            
            return document
        
        except Exception as e:
            self.logger.error(f"Error processing Git file {file_path}: {e}")
            return None
    
    async def _read_git_file_content(self, file_path: str) -> Optional[str]:
        """Read content of a Git file."""
        try:
            # Check if file is text-based (similar to file connector)
            if not self._is_text_file(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if len(content.strip()) == 0:
                return None
            
            return content
        
        except Exception as e:
            self.logger.error(f"Error reading Git file {file_path}: {e}")
            return None
    
    def _is_text_file(self, file_path: str) -> bool:
        """Determine if file is text-based (reuse from file connector logic)."""
        import mimetypes
        
        # Check extension
        text_extensions = {
            '.txt', '.md', '.rst', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h',
            '.css', '.html', '.xml', '.json', '.yaml', '.yml', '.toml', '.ini',
            '.sql', '.sh', '.bat', '.ps1', '.dockerfile', '.gitignore', '.env'
        }
        
        _, ext = os.path.splitext(file_path)
        if ext.lower() in text_extensions:
            return True
        
        # Use mimetype detection
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('text/'):
            return True
        
        return False
    
    async def _get_current_commit_hash(self) -> Optional[str]:
        """Get current commit hash."""
        try:
            result = await self._run_git_command(["rev-parse", "HEAD"])
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            self.logger.error(f"Error getting current commit hash: {e}")
            return None
    
    async def _get_changes_between_commits(self, old_commit: str, new_commit: str) -> List[ChangeDetection]:
        """Get changes between two commits."""
        changes = []
        
        try:
            # Get list of changed files
            result = await self._run_git_command([
                "diff", "--name-status", f"{old_commit}..{new_commit}"
            ])
            
            if result.returncode != 0:
                return changes
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                status = parts[0]
                file_path = parts[1]
                
                # Map Git status to change type
                if status == 'A':
                    change_type = ChangeType.CREATED
                elif status == 'M':
                    change_type = ChangeType.MODIFIED
                elif status == 'D':
                    change_type = ChangeType.DELETED
                elif status.startswith('R'):
                    change_type = ChangeType.MOVED
                else:
                    continue  # Skip unknown status
                
                # Get commit info for this change
                commit_info = await self._get_commit_info_for_file(file_path, new_commit)
                
                change = ChangeDetection(
                    source_path=file_path,
                    change_type=change_type,
                    timestamp=commit_info.get('timestamp', datetime.utcnow()),
                    metadata={
                        'commit_hash': new_commit,
                        'author': commit_info.get('author'),
                        'commit_message': commit_info.get('message')
                    }
                )
                
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error getting changes between commits: {e}")
        
        return changes
    
    async def _get_recent_changes(self) -> List[ChangeDetection]:
        """Get recent changes in the repository."""
        changes = []
        
        try:
            # Get commits from the last N days
            since_date = datetime.utcnow() - timedelta(days=self.max_history_days)
            since_str = since_date.strftime('%Y-%m-%d')
            
            result = await self._run_git_command([
                "log", "--name-status", "--pretty=format:%H|%an|%ad|%s", 
                "--date=iso", f"--since={since_str}"
            ])
            
            if result.returncode != 0:
                return changes
            
            current_commit = None
            current_author = None
            current_date = None
            current_message = None
            
            for line in result.stdout.split('\n'):
                if not line:
                    continue
                
                if '|' in line and not line.startswith(('A\t', 'M\t', 'D\t', 'R\t')):
                    # Commit info line
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        current_commit = parts[0]
                        current_author = parts[1]
                        current_date = datetime.fromisoformat(parts[2].replace(' ', 'T'))
                        current_message = parts[3]
                else:
                    # File change line
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        status = parts[0]
                        file_path = parts[1]
                        
                        # Map status to change type
                        if status == 'A':
                            change_type = ChangeType.CREATED
                        elif status == 'M':
                            change_type = ChangeType.MODIFIED
                        elif status == 'D':
                            change_type = ChangeType.DELETED
                        elif status.startswith('R'):
                            change_type = ChangeType.MOVED
                        else:
                            continue
                        
                        change = ChangeDetection(
                            source_path=file_path,
                            change_type=change_type,
                            timestamp=current_date or datetime.utcnow(),
                            metadata={
                                'commit_hash': current_commit,
                                'author': current_author,
                                'commit_message': current_message
                            }
                        )
                        
                        changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error getting recent changes: {e}")
        
        return changes
    
    async def _get_commit_info_for_file(self, file_path: str, commit_hash: str) -> Dict[str, Any]:
        """Get commit information for a specific file."""
        try:
            result = await self._run_git_command([
                "show", "--pretty=format:%an|%ad|%s", "--date=iso", 
                "--name-only", commit_hash, "--", file_path
            ])
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and '|' in lines[0]:
                    parts = lines[0].split('|', 2)
                    if len(parts) >= 3:
                        return {
                            'author': parts[0],
                            'timestamp': datetime.fromisoformat(parts[1].replace(' ', 'T')),
                            'message': parts[2]
                        }
        
        except Exception as e:
            self.logger.error(f"Error getting commit info for {file_path}: {e}")
        
        return {}
    
    async def _get_file_git_info(self, file_path: str) -> Dict[str, Any]:
        """Get Git-specific information for a file."""
        git_info = {}
        
        try:
            # Get last commit info for file
            result = await self._run_git_command([
                "log", "-1", "--pretty=format:%H|%an|%ad|%s", 
                "--date=iso", "--", file_path
            ])
            
            if result.returncode == 0 and result.stdout:
                parts = result.stdout.strip().split('|', 3)
                if len(parts) >= 4:
                    git_info.update({
                        'last_commit_hash': parts[0],
                        'last_author': parts[1],
                        'last_commit_date': parts[2],
                        'last_commit_message': parts[3]
                    })
            
            # Get file blame info (line count by author)
            blame_result = await self._run_git_command(["blame", "--line-porcelain", file_path])
            if blame_result.returncode == 0:
                authors = {}
                for line in blame_result.stdout.split('\n'):
                    if line.startswith('author '):
                        author = line[7:]  # Remove 'author ' prefix
                        authors[author] = authors.get(author, 0) + 1
                
                if authors:
                    git_info['contributors'] = authors
                    git_info['primary_author'] = max(authors.items(), key=lambda x: x[1])[0]
        
        except Exception as e:
            self.logger.error(f"Error getting Git info for {file_path}: {e}")
        
        return git_info
    
    async def _run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a Git command and return the result."""
        try:
            cmd = ["git"] + args
            result = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), 
                timeout=self.git_timeout
            )
            
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=result.returncode,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore')
            )
        
        except asyncio.TimeoutError:
            self.logger.error(f"Git command timed out: {args}")
            raise
        except Exception as e:
            self.logger.error(f"Error running Git command {args}: {e}")
            raise
    
    async def validate_configuration(self) -> List[str]:
        """Validate Git connector configuration."""
        errors = await super().validate_configuration()
        
        # Check repository path
        if not os.path.exists(self.repo_path):
            errors.append(f"Repository path does not exist: {self.repo_path}")
        elif not await self._is_git_repository():
            errors.append(f"Path is not a Git repository: {self.repo_path}")
        
        # Check branches
        if not self.branches:
            errors.append("At least one branch must be specified")
        
        # Check current branch
        if self.current_branch not in self.branches:
            errors.append(f"Current branch '{self.current_branch}' not in branches list")
        
        return errors