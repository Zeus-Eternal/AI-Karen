"""
Agent Manager for AI-Karen
Integrated agent management from neuro_recall with async support
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from ..recalls import RecallManager, RecallQuery
from ...tools.interpreters import BaseInterpreter, PythonInterpreter, DockerInterpreter, SubprocessInterpreter, IPythonInterpreter
from ...tools.search import SearchTool
from ...tools.documents import DocumentsTool

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Manager for AI agent instances with integrated tools and memory
    
    Features:
    - Multi-agent coordination
    - Tool management
    - Memory integration
    - Async execution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agents: Dict[str, Any] = {}
        
        # Initialize components
        self.recall_manager = None
        self.interpreters: Dict[str, BaseInterpreter] = {}
        self.search_tool = None
        self.documents_tool = None
        
    async def initialize(self) -> None:
        """Initialize the agent manager"""
        try:
            # Initialize recall manager
            recall_config = self.config.get('recalls', {})
            self.recall_manager = RecallManager(recall_config)
            await self.recall_manager.initialize()
            
            # Initialize interpreters
            await self._initialize_interpreters()
            
            # Initialize tools
            await self._initialize_tools()
            
            logger.info("Agent manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent manager: {e}")
            raise
    
    async def _initialize_interpreters(self) -> None:
        """Initialize code interpreters"""
        interpreter_configs = self.config.get('interpreters', {})
        
        # Python interpreter
        if interpreter_configs.get('python', {}).get('enabled', True):
            python_config = interpreter_configs.get('python', {})
            self.interpreters['python'] = PythonInterpreter(python_config)
        
        # Docker interpreter
        if interpreter_configs.get('docker', {}).get('enabled', False):
            docker_config = interpreter_configs.get('docker', {})
            self.interpreters['docker'] = DockerInterpreter(docker_config)
        
        # Subprocess interpreter
        if interpreter_configs.get('subprocess', {}).get('enabled', False):
            subprocess_config = interpreter_configs.get('subprocess', {})
            self.interpreters['subprocess'] = SubprocessInterpreter(subprocess_config)
        
        # IPython interpreter
        if interpreter_configs.get('ipython', {}).get('enabled', False):
            ipython_config = interpreter_configs.get('ipython', {})
            self.interpreters['ipython'] = IPythonInterpreter(ipython_config)
    
    async def _initialize_tools(self) -> None:
        """Initialize agent tools"""
        # Search tool
        search_config = self.config.get('search', {})
        self.search_tool = SearchTool(search_config)
        
        # Documents tool
        documents_config = self.config.get('documents', {})
        self.documents_tool = DocumentsTool(documents_config)
    
    async def execute_code(
        self, 
        code: str, 
        code_type: str, 
        interpreter: str = "python"
    ) -> str:
        """Execute code using specified interpreter"""
        if interpreter not in self.interpreters:
            raise ValueError(f"Interpreter not available: {interpreter}")
        
        return await self.interpreters[interpreter].run(code, code_type)
    
    async def search_web(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform web search"""
        if not self.search_tool:
            raise RuntimeError("Search tool not initialized")
        
        return await self.search_tool.search(query, **kwargs)
    
    async def process_document(self, source: str, **kwargs) -> str:
        """Process document and extract text"""
        if not self.documents_tool:
            raise RuntimeError("Documents tool not initialized")
        
        return await self.documents_tool.process_document(source, **kwargs)
    
    async def recall_similar_cases(
        self, 
        task: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve similar cases from memory"""
        if not self.recall_manager:
            raise RuntimeError("Recall manager not initialized")
        
        query = RecallQuery(task=task, top_k=top_k)
        results = await self.recall_manager.retrieve_recalls(query)
        
        return [result.to_dict() for result in results]
    
    async def load_recalls_from_file(self, file_path: str) -> int:
        """Load recalls from file"""
        if not self.recall_manager:
            raise RuntimeError("Recall manager not initialized")
        
        recalls = await self.recall_manager.load_recalls_from_file(file_path)
        return len(recalls)
    
    def get_available_interpreters(self) -> List[str]:
        """Get list of available interpreters"""
        return list(self.interpreters.keys())
    
    def get_interpreter_info(self, interpreter: str) -> Dict[str, Any]:
        """Get information about specific interpreter"""
        if interpreter not in self.interpreters:
            return {}
        
        interp = self.interpreters[interpreter]
        return {
            'name': interpreter,
            'supported_types': interp.supported_code_types(),
            'available': True
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent manager status"""
        status = {
            'initialized': True,
            'interpreters': {
                name: self.get_interpreter_info(name) 
                for name in self.interpreters.keys()
            },
            'tools': {
                'search': self.search_tool is not None,
                'documents': self.documents_tool is not None
            },
            'recalls': {}
        }
        
        if self.recall_manager:
            status['recalls'] = await self.recall_manager.get_stats()
        
        return status
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        # Cleanup interpreters
        for interpreter in self.interpreters.values():
            try:
                await interpreter.cleanup()
            except Exception as e:
                logger.warning(f"Failed to cleanup interpreter: {e}")
        
        logger.info("Agent manager cleanup completed")
