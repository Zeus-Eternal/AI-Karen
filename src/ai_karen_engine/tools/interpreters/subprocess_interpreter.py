"""
Subprocess Interpreter for AI-Karen
Integrated from neuro_recall subprocess interpreter with security controls
"""

import asyncio
import tempfile
import os
import shlex
from typing import Any, Dict, List, Optional
import logging
from .base_interpreter import BaseInterpreter, InterpreterError

logger = logging.getLogger(__name__)

class SubprocessInterpreter(BaseInterpreter):
    """
    Subprocess-based interpreter for direct system execution with security controls.
    
    Features:
    - Command whitelist
    - Timeout control
    - Working directory isolation
    - Environment variable control
    """
    
    DEFAULT_ALLOWED_COMMANDS = {
        'python', 'python3', 'node', 'npm', 'pip', 'pip3',
        'git', 'ls', 'cat', 'echo', 'pwd', 'whoami',
        'curl', 'wget', 'grep', 'find', 'sort', 'uniq',
        'head', 'tail', 'wc', 'diff', 'which'
    }
    
    DANGEROUS_COMMANDS = {
        'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs',
        'dd', 'sudo', 'su', 'chmod', 'chown', 'passwd',
        'useradd', 'userdel', 'groupadd', 'groupdel',
        'systemctl', 'service', 'kill', 'killall'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.allowed_commands = set(
            self.config.get('allowed_commands', self.DEFAULT_ALLOWED_COMMANDS)
        )
        self.timeout = self.config.get('timeout', 30)
        self.working_dir = self.config.get('working_dir')
        self.env_whitelist = set(self.config.get('env_whitelist', [
            'PATH', 'HOME', 'USER', 'LANG', 'LC_ALL', 'PYTHONPATH'
        ]))
        
    async def run(self, code: str, code_type: str) -> str:
        """Execute code via subprocess"""
        if not self.validate_code_type(code_type):
            raise InterpreterError(f"Unsupported code type: {code_type}")
            
        try:
            if code_type in ['bash', 'shell', 'sh']:
                return await self._execute_shell(code)
            elif code_type in ['python', 'py']:
                return await self._execute_python(code)
            elif code_type in ['node', 'javascript', 'js']:
                return await self._execute_node(code)
            else:
                raise InterpreterError(f"Unsupported execution type: {code_type}")
                
        except Exception as e:
            logger.error(f"Subprocess interpreter error: {e}")
            raise InterpreterError(f"Execution failed: {str(e)}")
    
    async def _execute_shell(self, code: str) -> str:
        """Execute shell commands with security validation"""
        # Validate commands
        lines = code.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                self._validate_command(line)
        
        # Create temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write('#!/bin/bash\nset -e\n')
            f.write(code)
            script_path = f.name
        
        try:
            os.chmod(script_path, 0o755)
            return await self._run_subprocess(['bash', script_path])
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass
    
    async def _execute_python(self, code: str) -> str:
        """Execute Python code via subprocess"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            script_path = f.name
        
        try:
            return await self._run_subprocess(['python3', script_path])
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass
    
    async def _execute_node(self, code: str) -> str:
        """Execute Node.js code via subprocess"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            script_path = f.name
        
        try:
            return await self._run_subprocess(['node', script_path])
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass
    
    def _validate_command(self, command: str) -> None:
        """Validate command against security policies"""
        # Parse command
        try:
            parts = shlex.split(command)
        except ValueError as e:
            raise InterpreterError(f"Invalid command syntax: {e}")
        
        if not parts:
            return
        
        cmd = parts[0]
        
        # Check for dangerous commands
        if cmd in self.DANGEROUS_COMMANDS:
            raise InterpreterError(f"Dangerous command not allowed: {cmd}")
        
        # Check against whitelist if enabled
        if self.allowed_commands and cmd not in self.allowed_commands:
            # Allow full paths if the basename is allowed
            basename = os.path.basename(cmd)
            if basename not in self.allowed_commands:
                raise InterpreterError(f"Command not in whitelist: {cmd}")
        
        # Check for command chaining and redirection
        dangerous_operators = ['&&', '||', ';', '|', '>', '>>', '<', '&']
        for part in parts:
            if any(op in part for op in dangerous_operators):
                # Allow simple pipes for common operations
                if part == '|' and len(parts) > parts.index(part) + 1:
                    next_cmd = parts[parts.index(part) + 1]
                    if next_cmd in ['grep', 'sort', 'uniq', 'head', 'tail', 'wc']:
                        continue
                raise InterpreterError(f"Command chaining/redirection not allowed: {command}")
    
    async def _run_subprocess(self, cmd: List[str]) -> str:
        """Run subprocess with security controls"""
        # Prepare environment
        env = {}
        for key, value in os.environ.items():
            if key in self.env_whitelist:
                env[key] = value
        
        # Set working directory
        cwd = self.working_dir or tempfile.gettempdir()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
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
                return "Command executed successfully (no output)"
                
        except asyncio.TimeoutError:
            raise InterpreterError(f"Execution timed out after {self.timeout} seconds")
        except FileNotFoundError:
            raise InterpreterError(f"Command not found: {cmd[0]}")
    
    def supported_code_types(self) -> List[str]:
        """Return supported code types"""
        return ['bash', 'shell', 'sh', 'python', 'py', 'node', 'javascript', 'js']
    
    def update_action_space(self, action_space: Dict[str, Any]) -> None:
        """Update action space (not applicable for subprocess interpreter)"""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup subprocess resources"""
        pass
