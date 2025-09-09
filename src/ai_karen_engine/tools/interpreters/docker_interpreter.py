"""
Docker Interpreter for AI-Karen
Integrated from neuro_recall docker interpreter with container isolation
"""

import asyncio
import json
import tempfile
import os
from typing import Any, Dict, List, Optional
import logging
from .base_interpreter import BaseInterpreter, InterpreterError

logger = logging.getLogger(__name__)

class DockerInterpreter(BaseInterpreter):
    """
    Docker-based code interpreter for secure isolated execution.
    
    Features:
    - Container isolation
    - Resource limits
    - Timeout control
    - Multi-language support
    """
    
    DEFAULT_IMAGES = {
        'python': 'python:3.11-slim',
        'node': 'node:18-slim',
        'bash': 'ubuntu:22.04',
        'shell': 'ubuntu:22.04'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.images = {**self.DEFAULT_IMAGES, **self.config.get('images', {})}
        self.timeout = self.config.get('timeout', 30)
        self.memory_limit = self.config.get('memory_limit', '512m')
        self.cpu_limit = self.config.get('cpu_limit', '1.0')
        self.network_disabled = self.config.get('disable_network', True)
        
    async def run(self, code: str, code_type: str) -> str:
        """Execute code in Docker container"""
        if not self.validate_code_type(code_type):
            raise InterpreterError(f"Unsupported code type: {code_type}")
            
        try:
            # Check if Docker is available
            if not await self._check_docker():
                raise InterpreterError("Docker is not available or not running")
            
            # Get appropriate image
            image = self.images.get(code_type)
            if not image:
                raise InterpreterError(f"No Docker image configured for {code_type}")
            
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix=self._get_file_extension(code_type), delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute in container
                result = await self._execute_in_container(image, temp_file, code_type)
                return result
            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"Docker interpreter error: {e}")
            raise InterpreterError(f"Docker execution failed: {str(e)}")
    
    async def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                'docker', 'version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=5)
            return process.returncode == 0
        except (asyncio.TimeoutError, FileNotFoundError):
            return False
    
    async def _execute_in_container(self, image: str, code_file: str, code_type: str) -> str:
        """Execute code in Docker container"""
        container_code_path = f"/tmp/code{self._get_file_extension(code_type)}"
        
        # Build Docker command
        docker_cmd = [
            'docker', 'run',
            '--rm',
            '--memory', self.memory_limit,
            '--cpus', str(self.cpu_limit),
            '-v', f"{code_file}:{container_code_path}:ro"
        ]
        
        # Disable network if configured
        if self.network_disabled:
            docker_cmd.extend(['--network', 'none'])
        
        # Add image and execution command
        docker_cmd.append(image)
        docker_cmd.extend(self._get_execution_command(code_type, container_code_path))
        
        try:
            # Execute container
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self.timeout
            )
            
            # Format output
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            if process.returncode != 0:
                if error_output:
                    return f"Execution Error (exit code {process.returncode}):\n{error_output}"
                return f"Execution failed with exit code {process.returncode}"
            
            if error_output and output:
                return f"Output:\n{output}\nWarnings/Errors:\n{error_output}"
            elif error_output:
                return f"Warnings/Errors:\n{error_output}"
            elif output:
                return output
            else:
                return "Code executed successfully (no output)"
                
        except asyncio.TimeoutError:
            # Kill container if it's still running
            await self._cleanup_containers(image)
            raise InterpreterError(f"Execution timed out after {self.timeout} seconds")
    
    def _get_file_extension(self, code_type: str) -> str:
        """Get file extension for code type"""
        extensions = {
            'python': '.py',
            'node': '.js',
            'javascript': '.js',
            'bash': '.sh',
            'shell': '.sh'
        }
        return extensions.get(code_type, '.txt')
    
    def _get_execution_command(self, code_type: str, code_path: str) -> List[str]:
        """Get execution command for code type"""
        commands = {
            'python': ['python', code_path],
            'node': ['node', code_path],
            'javascript': ['node', code_path],
            'bash': ['bash', code_path],
            'shell': ['bash', code_path]
        }
        return commands.get(code_type, ['cat', code_path])
    
    async def _cleanup_containers(self, image: str) -> None:
        """Cleanup any running containers"""
        try:
            # List and stop containers based on image
            process = await asyncio.create_subprocess_exec(
                'docker', 'ps', '-q', '--filter', f'ancestor={image}',
                stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            container_ids = stdout.decode().strip().split('\n')
            for container_id in container_ids:
                if container_id:
                    await asyncio.create_subprocess_exec(
                        'docker', 'kill', container_id,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
        except Exception:
            pass  # Best effort cleanup
    
    def supported_code_types(self) -> List[str]:
        """Return supported code types"""
        return list(self.images.keys())
    
    def update_action_space(self, action_space: Dict[str, Any]) -> None:
        """Update action space (not applicable for Docker interpreter)"""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup Docker resources"""
        # Cleanup any running containers for all configured images
        for image in self.images.values():
            await self._cleanup_containers(image)
