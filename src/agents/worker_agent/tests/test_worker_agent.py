"""
Tests for the Worker Agent
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the agent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ..handler import WorkerAgentHandler, initialize, execute, finalize


class TestWorkerAgent(unittest.TestCase):
    """Test cases for the Worker Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.handler = WorkerAgentHandler()
        self.context = {
            "config": {"test": True},
            "state": {"initialized": False}
        }
        self.task = {
            "type": "data_processing",
            "data": {
                "input": "test data",
                "parameters": {
                    "format": "json"
                }
            }
        }
    
    def test_initialize(self):
        """Test agent initialization"""
        self.handler.initialize(self.context)
        self.assertTrue(self.handler.initialized)
        self.assertEqual(self.handler.context, self.context)
    
    def test_execute_without_initialization(self):
        """Test task execution without initialization"""
        with self.assertRaises(RuntimeError):
            self.handler.execute(self.task)
    
    def test_execute_data_processing_task(self):
        """Test execution of a data processing task"""
        self.handler.initialize(self.context)
        result = self.handler.execute(self.task)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["input_data"], self.task["data"])
        self.assertIn("processed_at", result)
    
    def test_execute_analysis_task(self):
        """Test execution of an analysis task"""
        analysis_task = {
            "type": "analysis",
            "data": {
                "input": "test data for analysis"
            }
        }
        
        self.handler.initialize(self.context)
        result = self.handler.execute(analysis_task)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["input_data"], analysis_task["data"])
        self.assertIn("analysis_result", result)
        self.assertIn("analyzed_at", result)
    
    def test_execute_unknown_task_type(self):
        """Test execution of an unknown task type"""
        unknown_task = {
            "type": "unknown",
            "data": {
                "input": "test data"
            }
        }
        
        self.handler.initialize(self.context)
        result = self.handler.execute(unknown_task)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Unknown task type", result["message"])
    
    def test_finalize_without_initialization(self):
        """Test agent finalization without initialization"""
        with self.assertRaises(RuntimeError):
            self.handler.finalize({"result": "test"})
    
    def test_finalize(self):
        """Test agent finalization"""
        self.handler.initialize(self.context)
        self.handler.finalize({"result": "test"})
        
        self.assertFalse(self.handler.initialized)
        self.assertEqual(self.handler.context, {})
    
    def test_global_functions(self):
        """Test global functions for agent interface"""
        # Test initialize
        initialize(self.context)
        
        # Test execute
        result = execute(self.task)
        self.assertEqual(result["status"], "success")
        
        # Test finalize
        finalize(result)
        
        # Test execute after finalize (should fail)
        with self.assertRaises(RuntimeError):
            execute(self.task)


class TestWorkerAgentSchema(unittest.TestCase):
    """Test cases for the Worker Agent schema"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_path = os.path.join(os.path.dirname(__file__), 'schema', 'task.json')
        
        # Load the schema
        with open(self.schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def test_task_schema_validity(self):
        """Test that the task schema is valid"""
        self.assertIn("$schema", self.schema)
        self.assertIn("title", self.schema)
        self.assertIn("type", self.schema)
        self.assertEqual(self.schema["type"], "object")
        self.assertIn("properties", self.schema)
        self.assertIn("required", self.schema)
    
    def test_task_schema_required_fields(self):
        """Test that the required fields are correctly defined"""
        required_fields = self.schema["required"]
        self.assertIn("type", required_fields)
        self.assertIn("data", required_fields)
    
    def test_task_schema_type_enum(self):
        """Test that the type field has the correct enum values"""
        type_property = self.schema["properties"]["type"]
        self.assertIn("enum", type_property)
        enum_values = type_property["enum"]
        self.assertIn("data_processing", enum_values)
        self.assertIn("analysis", enum_values)


if __name__ == '__main__':
    unittest.main()