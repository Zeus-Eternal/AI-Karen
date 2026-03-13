"""Tests for the worker agent."""

import unittest
from unittest.mock import MagicMock
from src.agents.worker_agent.handler import WorkerAgentHandler


class TestWorkerAgent(unittest.TestCase):
    """Test cases for the worker agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = WorkerAgentHandler()
    
    def test_process_task(self):
        """Test task processing."""
        task = {
            "type": "test_task",
            "data": {"key": "value"}
        }
        
        result = self.handler.process_task(task)
        
        self.assertEqual(result["status"], "completed")
        self.assertIn("test_task", result["result"])
        self.assertEqual(result["data"], {"key": "value"})
    
    def test_get_capabilities(self):
        """Test getting capabilities."""
        capabilities = self.handler.get_capabilities()
        
        self.assertIn("task_execution", capabilities)
        self.assertIn("basic_reasoning", capabilities)
        self.assertIn("response_generation", capabilities)
    
    def test_get_info(self):
        """Test getting agent information."""
        info = self.handler.get_info()
        
        self.assertEqual(info["name"], "worker_agent")
        self.assertEqual(info["version"], "1.0.0")
        self.assertIn("capabilities", info)


if __name__ == "__main__":
    unittest.main()