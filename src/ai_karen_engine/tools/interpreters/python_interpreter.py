"""
Python Interpreter for AI-Karen
Integrated from neuro_recall internal python interpreter with security controls
"""

import ast
import difflib
import importlib
import sys
import io
import contextlib
from typing import Any, Dict, List, Optional
import logging
from .base_interpreter import BaseInterpreter, InterpreterError

logger = logging.getLogger(__name__)

class PythonInterpreter(BaseInterpreter):
    """
    Secure Python interpreter with controlled execution environment.
    
    Features:
    - Whitelist-based import control
    - Action space restriction
    - Fuzzy variable matching
    - Safe execution environment
    """
    
    # Default safe imports whitelist
    DEFAULT_IMPORT_WHITELIST = {
        'math', 'random', 'datetime', 'json', 'os', 'sys', 'typing',
        'collections', 'itertools', 'functools', 'operator', 're',
        'string', 'time', 'uuid', 'base64', 'hashlib', 'hmac',
        'urllib', 'pathlib', 'tempfile', 'shutil', 'glob',
        'numpy', 'pandas', 'matplotlib', 'seaborn', 'plotly',
        'requests', 'httpx', 'aiohttp'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.action_space = {}
        self.state = {}
        self.import_whitelist = set(
            self.config.get('import_whitelist', self.DEFAULT_IMPORT_WHITELIST)
        )
        self.enable_fuzzy_matching = self.config.get('enable_fuzzy_matching', True)
        
    async def run(self, code: str, code_type: str) -> str:
        """Execute Python code in controlled environment"""
        if not self.validate_code_type(code_type):
            raise InterpreterError(f"Unsupported code type: {code_type}")
            
        try:
            # Parse and validate AST
            tree = ast.parse(code)
            self._validate_ast(tree)
            
            # Capture output
            output_buffer = io.StringIO()
            error_buffer = io.StringIO()
            
            # Create execution environment
            exec_globals = {
                '__builtins__': self._get_safe_builtins(),
                **self.action_space,
                **self.state
            }
            
            # Execute code with output capture
            with contextlib.redirect_stdout(output_buffer), \
                 contextlib.redirect_stderr(error_buffer):
                try:
                    exec(compile(tree, '<string>', 'exec'), exec_globals)
                    
                    # Update state with new variables
                    for key, value in exec_globals.items():
                        if not key.startswith('__') and key not in self.action_space:
                            self.state[key] = value
                            
                except Exception as e:
                    error_output = error_buffer.getvalue()
                    if error_output:
                        return f"Execution Error:\n{error_output}\n{str(e)}"
                    return f"Execution Error: {str(e)}"
            
            output = output_buffer.getvalue()
            error_output = error_buffer.getvalue()
            
            if error_output:
                return f"Warning:\n{error_output}\nOutput:\n{output}"
            
            return output if output else "Code executed successfully (no output)"
            
        except SyntaxError as e:
            return f"Syntax Error: {str(e)}"
        except InterpreterError:
            raise
        except Exception as e:
            logger.error(f"Python interpreter error: {e}")
            return f"Interpreter Error: {str(e)}"
    
    def _validate_ast(self, tree: ast.AST) -> None:
        """Validate AST for security and allowed operations"""
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._validate_import(node)
            
            # Check function calls
            elif isinstance(node, ast.Call):
                self._validate_function_call(node)
            
            # Check attribute access
            elif isinstance(node, ast.Attribute):
                self._validate_attribute_access(node)
    
    def _validate_import(self, node: ast.AST) -> None:
        """Validate import statements against whitelist"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                if module_name not in self.import_whitelist:
                    raise InterpreterError(f"Import not allowed: {module_name}")
        
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                if module_name not in self.import_whitelist:
                    raise InterpreterError(f"Import not allowed: {module_name}")
    
    def _validate_function_call(self, node: ast.Call) -> None:
        """Validate function calls for security"""
        # Check for dangerous functions
        dangerous_functions = {'eval', 'exec', 'compile', '__import__'}
        
        if isinstance(node.func, ast.Name):
            if node.func.id in dangerous_functions:
                raise InterpreterError(f"Function not allowed: {node.func.id}")
    
    def _validate_attribute_access(self, node: ast.Attribute) -> None:
        """Validate attribute access for security"""
        # Check for dangerous attribute access
        dangerous_attrs = {'__globals__', '__locals__', '__dict__', '__class__'}
        
        if node.attr in dangerous_attrs:
            raise InterpreterError(f"Attribute access not allowed: {node.attr}")
    
    def _get_safe_builtins(self) -> Dict[str, Any]:
        """Get safe subset of builtins"""
        safe_builtins = {
            'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter',
            'float', 'int', 'len', 'list', 'map', 'max', 'min', 'range',
            'reversed', 'round', 'set', 'sorted', 'str', 'sum', 'tuple',
            'type', 'zip', 'print', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'chr', 'ord', 'hex', 'oct', 'bin'
        }
        
        return {name: getattr(__builtins__, name) for name in safe_builtins 
                if hasattr(__builtins__, name)}
    
    def supported_code_types(self) -> List[str]:
        """Return supported code types"""
        return ['python', 'py']
    
    def update_action_space(self, action_space: Dict[str, Any]) -> None:
        """Update available functions and objects"""
        self.action_space.update(action_space)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current interpreter state"""
        return self.state.copy()
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """Set interpreter state"""
        self.state = state.copy()
    
    def clear_state(self) -> None:
        """Clear interpreter state"""
        self.state.clear()
    
    async def cleanup(self) -> None:
        """Cleanup interpreter resources"""
        self.state.clear()
        self.action_space.clear()
