"""
Code execution and tool integration service for chat system.

This module provides secure sandboxed code execution capabilities with
multi-language support and tool integration.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import json
import shutil

try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

logger = logging.getLogger(__name__)


class CodeLanguage(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"
    SQL = "sql"
    R = "r"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"


class ExecutionStatus(str, Enum):
    """Code execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class SecurityLevel(str, Enum):
    """Security levels for code execution."""
    STRICT = "strict"      # Maximum security, minimal permissions
    MODERATE = "moderate"  # Balanced security and functionality
    PERMISSIVE = "permissive"  # More permissions for advanced use cases


@dataclass
class ExecutionLimits:
    """Resource limits for code execution."""
    max_execution_time: float = 30.0  # seconds
    max_memory_mb: int = 512
    max_output_size: int = 10 * 1024 * 1024  # 10MB
    max_file_operations: int = 100
    allow_network: bool = False
    allow_file_system: bool = False


@dataclass
class ExecutionResult:
    """Result of code execution."""
    execution_id: str
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    return_code: Optional[int] = None
    execution_time: float = 0.0
    memory_used: Optional[int] = None
    files_created: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    visualization_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeExecutionRequest(BaseModel):
    """Request for code execution."""
    code: str = Field(..., description="Code to execute")
    language: CodeLanguage = Field(..., description="Programming language")
    user_id: str = Field(..., description="User ID")
    conversation_id: str = Field(..., description="Conversation ID")
    security_level: SecurityLevel = Field(SecurityLevel.STRICT, description="Security level")
    execution_limits: Optional[Dict[str, Any]] = Field(None, description="Custom execution limits")
    environment_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    input_data: Optional[str] = Field(None, description="Input data for the code")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CodeExecutionResponse(BaseModel):
    """Response for code execution."""
    execution_id: str = Field(..., description="Unique execution identifier")
    status: ExecutionStatus = Field(..., description="Execution status")
    result: Optional[ExecutionResult] = Field(None, description="Execution result")
    message: str = Field(..., description="Status message")
    success: bool = Field(..., description="Whether execution was successful")


class ToolDefinition(BaseModel):
    """Definition of a custom tool."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    language: CodeLanguage = Field(..., description="Implementation language")
    code_template: str = Field(..., description="Code template with placeholders")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters schema")
    security_level: SecurityLevel = Field(SecurityLevel.STRICT, description="Required security level")
    category: str = Field("general", description="Tool category")
    version: str = Field("1.0.0", description="Tool version")


class ToolExecutionRequest(BaseModel):
    """Request for tool execution."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    user_id: str = Field(..., description="User ID")
    conversation_id: str = Field(..., description="Conversation ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CodeExecutionService:
    """
    Service for secure code execution and tool integration.
    
    Features:
    - Multi-language code execution with sandboxing
    - Resource limits and security controls
    - Custom tool integration and management
    - Result visualization and sharing
    - Execution history and analytics
    """
    
    def __init__(
        self,
        sandbox_path: str = "data/sandbox",
        enable_docker: bool = True,
        default_limits: Optional[ExecutionLimits] = None,
        supported_languages: Optional[List[CodeLanguage]] = None,
        enable_visualization: bool = True
    ):
        self.sandbox_path = Path(sandbox_path)
        self.enable_docker = enable_docker
        self.default_limits = default_limits or ExecutionLimits()
        self.supported_languages = supported_languages or [
            CodeLanguage.PYTHON,
            CodeLanguage.JAVASCRIPT,
            CodeLanguage.BASH,
            CodeLanguage.SQL
        ]
        self.enable_visualization = enable_visualization
        
        # Create sandbox directory
        self.sandbox_path.mkdir(parents=True, exist_ok=True)
        
        # Execution tracking
        self._active_executions: Dict[str, subprocess.Popen] = {}
        self._execution_history: Dict[str, ExecutionResult] = {}
        
        # Tool registry
        self._registered_tools: Dict[str, ToolDefinition] = {}
        
        # Initialize language environments
        self._initialize_environments()
        
        logger.info(f"CodeExecutionService initialized with sandbox: {self.sandbox_path}")
    
    def _initialize_environments(self):
        """Initialize execution environments for supported languages."""
        self._language_configs = {}
        
        # Python configuration
        if CodeLanguage.PYTHON in self.supported_languages:
            self._language_configs[CodeLanguage.PYTHON] = {
                "executable": "python3",
                "file_extension": ".py",
                "docker_image": "python:3.9-slim",
                "security_wrapper": self._get_python_security_wrapper()
            }
        
        # JavaScript configuration
        if CodeLanguage.JAVASCRIPT in self.supported_languages:
            self._language_configs[CodeLanguage.JAVASCRIPT] = {
                "executable": "node",
                "file_extension": ".js",
                "docker_image": "node:16-slim",
                "security_wrapper": self._get_javascript_security_wrapper()
            }
        
        # Bash configuration
        if CodeLanguage.BASH in self.supported_languages:
            self._language_configs[CodeLanguage.BASH] = {
                "executable": "bash",
                "file_extension": ".sh",
                "docker_image": "ubuntu:20.04",
                "security_wrapper": self._get_bash_security_wrapper()
            }
        
        # SQL configuration
        if CodeLanguage.SQL in self.supported_languages:
            self._language_configs[CodeLanguage.SQL] = {
                "executable": "sqlite3",
                "file_extension": ".sql",
                "docker_image": "alpine:latest",
                "security_wrapper": self._get_sql_security_wrapper()
            }
        
        logger.info(f"Initialized environments for: {list(self._language_configs.keys())}")

    def get_language_configs(self) -> Dict[CodeLanguage, Dict[str, Any]]:
        """Return configuration details for supported languages."""
        return dict(self._language_configs)

    def _get_python_security_wrapper(self) -> str:
        """Get Python security wrapper code."""
        return '''
import sys
import os
import signal
import resource
import tempfile
from io import StringIO
import contextlib

# Set resource limits
def set_limits(max_memory_mb=512, max_time=30):
    # Memory limit
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_mb * 1024 * 1024, max_memory_mb * 1024 * 1024))
    
    # Time limit
    def timeout_handler(signum, frame):
        raise TimeoutError("Execution timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(max_time)

# Capture output
@contextlib.contextmanager
def capture_output():
    old_stdout, old_stderr = sys.stdout, sys.stderr
    stdout_capture, stderr_capture = StringIO(), StringIO()
    try:
        sys.stdout, sys.stderr = stdout_capture, stderr_capture
        yield stdout_capture, stderr_capture
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

# Restricted imports
ALLOWED_MODULES = {
    'math', 'random', 'datetime', 'json', 'csv', 'statistics',
    'collections', 'itertools', 'functools', 're', 'string',
    'numpy', 'pandas', 'matplotlib', 'seaborn', 'plotly'
}

def secure_import(name, *args, **kwargs):
    if name not in ALLOWED_MODULES:
        raise ImportError(f"Module '{name}' is not allowed")
    return original_import(name, *args, **kwargs)

original_import = __builtins__['__import__']
__builtins__['__import__'] = secure_import

# Execute user code
def execute_user_code():
    set_limits()
    with capture_output() as (stdout, stderr):
        try:
            # USER_CODE_PLACEHOLDER
            pass
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
    
    return stdout.getvalue(), stderr.getvalue()

if __name__ == "__main__":
    stdout, stderr = execute_user_code()
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
'''
    
    def _get_javascript_security_wrapper(self) -> str:
        """Get JavaScript security wrapper code."""
        return '''
const vm = require('vm');
const { performance } = require('perf_hooks');

// Security context
const context = vm.createContext({
    console: {
        log: (...args) => process.stdout.write(args.join(' ') + '\\n'),
        error: (...args) => process.stderr.write(args.join(' ') + '\\n')
    },
    Math: Math,
    Date: Date,
    JSON: JSON,
    setTimeout: undefined,
    setInterval: undefined,
    require: undefined,
    process: undefined,
    global: undefined
});

// Execute user code
function executeUserCode() {
    const startTime = performance.now();
    
    try {
        const code = `
        // USER_CODE_PLACEHOLDER
        `;
        
        vm.runInContext(code, context, {
            timeout: 30000, // 30 seconds
            displayErrors: true
        });
        
    } catch (error) {
        console.error('Error:', error.message);
    }
    
    const endTime = performance.now();
    console.log(`Execution time: ${endTime - startTime}ms`);
}

executeUserCode();
'''
    
    def _get_bash_security_wrapper(self) -> str:
        """Get Bash security wrapper."""
        return '''#!/bin/bash
set -e
set -u
set -o pipefail

# Set resource limits
ulimit -t 30    # CPU time limit: 30 seconds
ulimit -v 524288 # Virtual memory limit: 512MB
ulimit -f 10240  # File size limit: 10MB

# Restricted environment
export PATH="/usr/bin:/bin"
unset IFS

# Execute user code in restricted environment
(
    # USER_CODE_PLACEHOLDER
    echo "User code executed"
) 2>&1
'''
    
    def _get_sql_security_wrapper(self) -> str:
        """Get SQL security wrapper."""
        return '''
-- SQL Security Wrapper
-- Create temporary database
.timeout 30000
.limit length 1000000
.limit sql_length 100000

-- USER_CODE_PLACEHOLDER

-- End of user code
'''
    
    async def execute_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
        """Execute code with security controls and resource limits."""
        execution_id = str(uuid.uuid4())
        
        try:
            # Validate language support
            if request.language not in self.supported_languages:
                return CodeExecutionResponse(
                    execution_id=execution_id,
                    status=ExecutionStatus.FAILED,
                    message=f"Language {request.language} is not supported",
                    success=False
                )
            
            # Create execution environment
            execution_dir = self.sandbox_path / f"exec_{execution_id}"
            execution_dir.mkdir(exist_ok=True)
            
            try:
                # Prepare execution limits
                limits = self._prepare_execution_limits(request)
                
                # Execute code based on environment
                if self.enable_docker:
                    result = await self._execute_in_docker(
                        request, execution_id, execution_dir, limits
                    )
                else:
                    result = await self._execute_locally(
                        request, execution_id, execution_dir, limits
                    )
                
                # Store execution history
                self._execution_history[execution_id] = result
                
                # Generate visualization if enabled
                if self.enable_visualization and result.status == ExecutionStatus.COMPLETED:
                    result.visualization_data = await self._generate_visualization(
                        result, request.language
                    )
                
                return CodeExecutionResponse(
                    execution_id=execution_id,
                    status=result.status,
                    result=result,
                    message="Code execution completed" if result.status == ExecutionStatus.COMPLETED else result.error_message or "Execution failed",
                    success=result.status == ExecutionStatus.COMPLETED
                )
                
            finally:
                # Cleanup execution directory
                try:
                    shutil.rmtree(execution_dir)
                except Exception as e:
                    logger.warning(f"Failed to cleanup execution directory: {e}")
                
        except Exception as e:
            logger.error(f"Code execution failed: {e}", exc_info=True)
            return CodeExecutionResponse(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                message=f"Execution failed: {str(e)}",
                success=False
            )
    
    def _prepare_execution_limits(self, request: CodeExecutionRequest) -> ExecutionLimits:
        """Prepare execution limits based on request and security level."""
        limits = ExecutionLimits()
        
        # Apply security level defaults
        if request.security_level == SecurityLevel.STRICT:
            limits.max_execution_time = 15.0
            limits.max_memory_mb = 256
            limits.allow_network = False
            limits.allow_file_system = False
        elif request.security_level == SecurityLevel.MODERATE:
            limits.max_execution_time = 30.0
            limits.max_memory_mb = 512
            limits.allow_network = False
            limits.allow_file_system = True
        elif request.security_level == SecurityLevel.PERMISSIVE:
            limits.max_execution_time = 60.0
            limits.max_memory_mb = 1024
            limits.allow_network = True
            limits.allow_file_system = True
        
        # Apply custom limits if provided
        if request.execution_limits:
            for key, value in request.execution_limits.items():
                if hasattr(limits, key):
                    setattr(limits, key, value)
        
        return limits
    
    async def _execute_in_docker(
        self,
        request: CodeExecutionRequest,
        execution_id: str,
        execution_dir: Path,
        limits: ExecutionLimits
    ) -> ExecutionResult:
        """Execute code in Docker container."""
        try:
            config = self._language_configs[request.language]
            
            # Prepare code file
            code_file = execution_dir / f"code{config['file_extension']}"
            wrapped_code = self._wrap_user_code(request.code, request.language)
            
            with open(code_file, 'w') as f:
                f.write(wrapped_code)
            
            # Prepare Docker command
            docker_cmd = [
                "docker", "run",
                "--rm",
                "--network=none" if not limits.allow_network else "--network=bridge",
                f"--memory={limits.max_memory_mb}m",
                f"--cpus=1",
                "--read-only" if not limits.allow_file_system else "",
                "-v", f"{execution_dir}:/workspace",
                "-w", "/workspace",
                config["docker_image"],
                config["executable"], f"code{config['file_extension']}"
            ]
            
            # Remove empty strings from command
            docker_cmd = [cmd for cmd in docker_cmd if cmd]
            
            # Execute with timeout
            start_time = datetime.utcnow()
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *docker_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, **request.environment_vars}
                )
                
                self._active_executions[execution_id] = process
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=limits.max_execution_time
                    )
                    
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    return ExecutionResult(
                        execution_id=execution_id,
                        status=ExecutionStatus.COMPLETED if process.returncode == 0 else ExecutionStatus.FAILED,
                        stdout=stdout.decode('utf-8', errors='ignore')[:limits.max_output_size],
                        stderr=stderr.decode('utf-8', errors='ignore')[:limits.max_output_size],
                        return_code=process.returncode,
                        execution_time=execution_time
                    )
                    
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    
                    return ExecutionResult(
                        execution_id=execution_id,
                        status=ExecutionStatus.TIMEOUT,
                        error_message=f"Execution timeout after {limits.max_execution_time}s",
                        execution_time=limits.max_execution_time
                    )
                    
            finally:
                if execution_id in self._active_executions:
                    del self._active_executions[execution_id]
                    
        except Exception as e:
            logger.error(f"Docker execution failed: {e}")
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error_message=f"Docker execution failed: {str(e)}"
            )
    
    async def _execute_locally(
        self,
        request: CodeExecutionRequest,
        execution_id: str,
        execution_dir: Path,
        limits: ExecutionLimits
    ) -> ExecutionResult:
        """Execute code locally with security restrictions."""
        try:
            config = self._language_configs[request.language]
            
            # Prepare code file
            code_file = execution_dir / f"code{config['file_extension']}"
            wrapped_code = self._wrap_user_code(request.code, request.language)
            
            with open(code_file, 'w') as f:
                f.write(wrapped_code)
            
            # Prepare execution command
            cmd = [config["executable"], str(code_file)]
            
            # Execute with timeout
            start_time = datetime.utcnow()
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=execution_dir,
                    env={**os.environ, **request.environment_vars}
                )
                
                self._active_executions[execution_id] = process
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=limits.max_execution_time
                    )
                    
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    return ExecutionResult(
                        execution_id=execution_id,
                        status=ExecutionStatus.COMPLETED if process.returncode == 0 else ExecutionStatus.FAILED,
                        stdout=stdout.decode('utf-8', errors='ignore')[:limits.max_output_size],
                        stderr=stderr.decode('utf-8', errors='ignore')[:limits.max_output_size],
                        return_code=process.returncode,
                        execution_time=execution_time
                    )
                    
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    
                    return ExecutionResult(
                        execution_id=execution_id,
                        status=ExecutionStatus.TIMEOUT,
                        error_message=f"Execution timeout after {limits.max_execution_time}s",
                        execution_time=limits.max_execution_time
                    )
                    
            finally:
                if execution_id in self._active_executions:
                    del self._active_executions[execution_id]
                    
        except Exception as e:
            logger.error(f"Local execution failed: {e}")
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                error_message=f"Local execution failed: {str(e)}"
            )
    
    def _wrap_user_code(self, user_code: str, language: CodeLanguage) -> str:
        """Wrap user code with security and monitoring wrapper."""
        config = self._language_configs[language]
        wrapper = config["security_wrapper"]
        
        # Replace placeholder with user code
        if language == CodeLanguage.PYTHON:
            # Indent user code for Python
            indented_code = '\n'.join('            ' + line for line in user_code.split('\n'))
            return wrapper.replace('            # USER_CODE_PLACEHOLDER', indented_code)
        else:
            return wrapper.replace('// USER_CODE_PLACEHOLDER', user_code).replace('# USER_CODE_PLACEHOLDER', user_code)
    
    async def _generate_visualization(
        self,
        result: ExecutionResult,
        language: CodeLanguage
    ) -> Optional[Dict[str, Any]]:
        """Generate visualization data from execution result."""
        try:
            visualization = {
                "type": "execution_result",
                "language": language.value,
                "execution_time": result.execution_time,
                "memory_used": result.memory_used,
                "output_length": len(result.stdout),
                "has_errors": bool(result.stderr),
                "charts": []
            }
            
            # Try to detect and extract visualization data from output
            if language == CodeLanguage.PYTHON:
                # Look for matplotlib/plotly output patterns
                if "matplotlib" in result.stdout.lower() or "plt." in result.stdout.lower():
                    visualization["charts"].append({
                        "type": "matplotlib",
                        "description": "Python matplotlib chart detected"
                    })
            
            return visualization
            
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}")
            return None
    
    def register_tool(self, tool: ToolDefinition) -> bool:
        """Register a custom tool."""
        try:
            self._registered_tools[tool.name] = tool
            logger.info(f"Tool '{tool.name}' registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register tool '{tool.name}': {e}")
            return False
    
    async def execute_tool(self, request: ToolExecutionRequest) -> CodeExecutionResponse:
        """Execute a registered tool."""
        try:
            if request.tool_name not in self._registered_tools:
                return CodeExecutionResponse(
                    execution_id="",
                    status=ExecutionStatus.FAILED,
                    message=f"Tool '{request.tool_name}' not found",
                    success=False
                )
            
            tool = self._registered_tools[request.tool_name]
            
            # Generate code from template
            code = self._generate_tool_code(tool, request.parameters)
            
            # Create execution request
            exec_request = CodeExecutionRequest(
                code=code,
                language=tool.language,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                security_level=tool.security_level,
                metadata={**request.metadata, "tool_name": tool.name, "tool_version": tool.version}
            )
            
            # Execute tool code
            return await self.execute_code(exec_request)
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return CodeExecutionResponse(
                execution_id="",
                status=ExecutionStatus.FAILED,
                message=f"Tool execution failed: {str(e)}",
                success=False
            )
    
    def _generate_tool_code(self, tool: ToolDefinition, parameters: Dict[str, Any]) -> str:
        """Generate executable code from tool template and parameters."""
        code = tool.code_template
        
        # Replace parameter placeholders
        for param_name, param_value in parameters.items():
            placeholder = f"{{{param_name}}}"
            if isinstance(param_value, str):
                code = code.replace(placeholder, f'"{param_value}"')
            else:
                code = code.replace(placeholder, str(param_value))
        
        return code
    
    def get_registered_tools(self) -> List[Dict[str, Any]]:
        """Get list of registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "language": tool.language.value,
                "category": tool.category,
                "version": tool.version,
                "parameters": tool.parameters
            }
            for tool in self._registered_tools.values()
        ]
    
    def get_execution_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history for a user."""
        history = []
        
        for execution_id, result in list(self._execution_history.items())[-limit:]:
            history.append({
                "execution_id": execution_id,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "return_code": result.return_code,
                "has_output": bool(result.stdout),
                "has_errors": bool(result.stderr),
                "metadata": result.metadata
            })
        
        return history
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        total_executions = len(self._execution_history)
        successful_executions = sum(
            1 for result in self._execution_history.values()
            if result.status == ExecutionStatus.COMPLETED
        )
        
        return {
            "supported_languages": [lang.value for lang in self.supported_languages],
            "registered_tools": len(self._registered_tools),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0.0,
            "active_executions": len(self._active_executions),
            "docker_enabled": self.enable_docker,
            "visualization_enabled": self.enable_visualization,
            "sandbox_path": str(self.sandbox_path)
        }
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution."""
        if execution_id in self._active_executions:
            try:
                process = self._active_executions[execution_id]
                process.kill()
                await process.wait()
                
                # Update execution result
                if execution_id in self._execution_history:
                    self._execution_history[execution_id].status = ExecutionStatus.CANCELLED
                
                logger.info(f"Execution {execution_id} cancelled")
                return True
                
            except Exception as e:
                logger.error(f"Failed to cancel execution {execution_id}: {e}")
                return False
        
        return False