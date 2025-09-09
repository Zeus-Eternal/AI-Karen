"""
IPython/Jupyter Interpreter for AI-Karen
Integrated from neuro_recall with async support and security controls
"""

import asyncio
import queue
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging
from .base_interpreter import BaseInterpreter, InterpreterError

if TYPE_CHECKING:
    from jupyter_client import BlockingKernelClient, KernelManager

logger = logging.getLogger(__name__)

class IPythonInterpreter(BaseInterpreter):
    """
    IPython/Jupyter kernel-based interpreter with async support.
    
    Features:
    - Jupyter kernel execution
    - ANSI escape sequence cleaning
    - Image output support
    - Timeout control
    - Async execution wrapper
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = self.config.get('timeout', 30)
        self.print_stdout = self.config.get('print_stdout', False)
        self.print_stderr = self.config.get('print_stderr', True)
        
        self.kernel_manager: Optional['KernelManager'] = None
        self.client: Optional['BlockingKernelClient'] = None
    
    def __del__(self):
        """Clean up kernel resources"""
        if self.kernel_manager:
            try:
                self.kernel_manager.shutdown_kernel()
            except Exception:
                pass
        if self.client:
            try:
                self.client.stop_channels()
            except Exception:
                pass
    
    async def run(self, code: str, code_type: str) -> str:
        """Execute code via IPython kernel (async wrapper)"""
        if not self.validate_code_type(code_type):
            raise InterpreterError(f"Unsupported code type: {code_type}")
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._run_sync, code, code_type)
            return result
        except Exception as e:
            logger.error(f"IPython interpreter error: {e}")
            raise InterpreterError(f"Execution failed: {str(e)}")
    
    def _run_sync(self, code: str, code_type: str) -> str:
        """Synchronous execution wrapper"""
        self._initialize_if_needed()
        
        # Handle bash code type
        if code_type == "bash":
            code = f"%%bash\n({code})"
        
        try:
            result = self._execute(code, timeout=self.timeout)
            return result
        except Exception as e:
            raise InterpreterError(f"Execution failed: {str(e)}")
    
    def _initialize_if_needed(self) -> None:
        """Initialize kernel manager and client if needed"""
        if self.kernel_manager is not None:
            return
        
        try:
            from jupyter_client.manager import start_new_kernel
            self.kernel_manager, self.client = start_new_kernel()
        except ImportError:
            raise InterpreterError(
                "Jupyter client not available. Install with: pip install jupyter-client ipykernel"
            )
        except Exception as e:
            raise InterpreterError(f"Failed to start Jupyter kernel: {str(e)}")
    
    @staticmethod
    def _clean_ipython_output(output: str) -> str:
        """Remove ANSI escape sequences from output"""
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', output)
    
    def _execute(self, code: str, timeout: float) -> str:
        """Execute code in Jupyter kernel and return result"""
        if not self.kernel_manager or not self.client:
            raise InterpreterError("Jupyter client is not initialized")
        
        self.client.execute(code)
        outputs = []
        
        while True:
            try:
                msg = self.client.get_iopub_msg(timeout=timeout)
                msg_content = msg["content"]
                msg_type = msg.get("msg_type", None)
                
                # Check if execution is complete
                if msg_content.get("execution_state", None) == "idle":
                    break
                
                # Handle different message types
                if msg_type == "error":
                    traceback = "\n".join(msg_content["traceback"])
                    outputs.append(f"Error:\n{traceback}")
                elif msg_type == "stream":
                    text = msg_content["text"]
                    if msg_content.get("name") == "stdout" and self.print_stdout:
                        outputs.append(text)
                    elif msg_content.get("name") == "stderr" and self.print_stderr:
                        outputs.append(f"stderr: {text}")
                    else:
                        outputs.append(text)
                elif msg_type in ["execute_result", "display_data"]:
                    data = msg_content["data"]
                    if "text/plain" in data:
                        outputs.append(data["text/plain"])
                    if "image/png" in data:
                        outputs.append(
                            f"\n![image](data:image/png;base64,{data['image/png']})\n"
                        )
                    if "text/html" in data:
                        outputs.append(f"HTML output:\n{data['text/html']}")
                        
            except queue.Empty:
                outputs.append(f"Execution timed out after {timeout} seconds")
                break
            except Exception as e:
                outputs.append(f"Exception occurred: {str(e)}")
                break
        
        exec_result = "\n".join(outputs)
        return self._clean_ipython_output(exec_result)
    
    def supported_code_types(self) -> List[str]:
        """Return supported code types"""
        return ["python", "py", "bash", "shell", "sh"]
    
    def update_action_space(self, action_space: Dict[str, Any]) -> None:
        """Update action space (not applicable for IPython interpreter)"""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup IPython resources"""
        if self.kernel_manager:
            try:
                self.kernel_manager.shutdown_kernel()
            except Exception:
                pass
            self.kernel_manager = None
        
        if self.client:
            try:
                self.client.stop_channels()
            except Exception:
                pass
            self.client = None
