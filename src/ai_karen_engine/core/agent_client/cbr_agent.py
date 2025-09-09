"""
Case-Based Reasoning Agent for AI-Karen
Integrated CBR agent from neuro_recall with case-memory learning
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
import json
from datetime import datetime

from ..recalls import RecallManager, RecallQuery, RecallEntry
from ...learning.case_memory import CaseRetriever, Case, StepTrace, Reward
from ...tools.interpreters import BaseInterpreter

logger = logging.getLogger(__name__)

class CBRAgent:
    """
    Case-Based Reasoning Agent with integrated memory and learning
    
    Features:
    - Case-based reasoning
    - Memory integration
    - Tool execution
    - Learning from experience
    - Async execution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agent_id = self.config.get('agent_id', 'cbr_agent')
        self.max_iterations = self.config.get('max_iterations', 10)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        
        # Components
        self.recall_manager: Optional[RecallManager] = None
        self.case_retriever: Optional[CaseRetriever] = None
        self.interpreters: Dict[str, BaseInterpreter] = {}
        
        # State
        self.current_task = None
        self.execution_history = []
        
    async def initialize(self, recall_manager: RecallManager, interpreters: Dict[str, BaseInterpreter]) -> None:
        """Initialize the CBR agent"""
        self.recall_manager = recall_manager
        self.interpreters = interpreters
        
        # Initialize case retriever if available
        # This would be integrated with the case-memory system
        logger.info(f"CBR Agent {self.agent_id} initialized")
    
    async def solve_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Solve a task using case-based reasoning
        
        Args:
            task: Task description
            context: Additional context
            
        Returns:
            Solution result with steps and outcome
        """
        self.current_task = task
        self.execution_history = []
        
        try:
            # Step 1: Retrieve similar cases
            similar_cases = await self._retrieve_similar_cases(task)
            
            # Step 2: Adapt and execute solution
            solution = await self._adapt_and_execute(task, similar_cases, context)
            
            # Step 3: Learn from execution
            await self._learn_from_execution(task, solution)
            
            return solution
            
        except Exception as e:
            logger.error(f"Task solving failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task': task,
                'execution_history': self.execution_history
            }
    
    async def _retrieve_similar_cases(self, task: str) -> List[Dict[str, Any]]:
        """Retrieve similar cases from memory"""
        if not self.recall_manager:
            logger.warning("No recall manager available")
            return []
        
        try:
            query = RecallQuery(
                task=task,
                top_k=5,
                min_score=self.similarity_threshold
            )
            
            results = await self.recall_manager.retrieve_recalls(query)
            
            similar_cases = []
            for result in results:
                case_data = {
                    'question': result.question,
                    'plan': result.plan,
                    'score': result.score,
                    'rank': result.rank
                }
                similar_cases.append(case_data)
            
            logger.info(f"Retrieved {len(similar_cases)} similar cases for task")
            return similar_cases
            
        except Exception as e:
            logger.error(f"Failed to retrieve similar cases: {e}")
            return []
    
    async def _adapt_and_execute(
        self, 
        task: str, 
        similar_cases: List[Dict[str, Any]], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Adapt similar cases and execute solution"""
        
        execution_steps = []
        current_context = context or {}
        
        try:
            # If we have similar cases, adapt their solutions
            if similar_cases:
                adapted_plan = await self._adapt_plan(task, similar_cases)
                execution_steps.extend(adapted_plan)
            else:
                # Generate new plan if no similar cases
                new_plan = await self._generate_new_plan(task)
                execution_steps.extend(new_plan)
            
            # Execute the plan
            results = []
            for i, step in enumerate(execution_steps):
                step_result = await self._execute_step(step, current_context)
                results.append(step_result)
                
                # Update context with step results
                if step_result.get('success'):
                    current_context.update(step_result.get('context_updates', {}))
                
                # Record execution history
                self.execution_history.append({
                    'step_id': i + 1,
                    'step': step,
                    'result': step_result,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Stop if step failed and no recovery strategy
                if not step_result.get('success') and not step.get('optional', False):
                    break
            
            # Determine overall success
            success = all(r.get('success', False) for r in results if not r.get('optional', False))
            
            return {
                'success': success,
                'task': task,
                'execution_steps': execution_steps,
                'results': results,
                'execution_history': self.execution_history,
                'similar_cases_used': len(similar_cases),
                'final_context': current_context
            }
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task': task,
                'execution_history': self.execution_history
            }
    
    async def _adapt_plan(self, task: str, similar_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Adapt plans from similar cases"""
        adapted_steps = []
        
        # Simple adaptation: extract common patterns from similar cases
        for case in similar_cases[:3]:  # Use top 3 cases
            try:
                plan_data = json.loads(case['plan'])
                if 'plan' in plan_data:
                    for step in plan_data['plan']:
                        adapted_step = {
                            'id': step.get('id', len(adapted_steps) + 1),
                            'description': step.get('description', ''),
                            'type': 'adapted',
                            'source_case_score': case['score'],
                            'optional': False
                        }
                        adapted_steps.append(adapted_step)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse case plan: {e}")
                continue
        
        # Remove duplicates and limit steps
        unique_steps = []
        seen_descriptions = set()
        
        for step in adapted_steps:
            desc = step['description'].lower()
            if desc not in seen_descriptions:
                seen_descriptions.add(desc)
                unique_steps.append(step)
        
        return unique_steps[:self.max_iterations]
    
    async def _generate_new_plan(self, task: str) -> List[Dict[str, Any]]:
        """Generate new plan when no similar cases available"""
        # Simple plan generation - in practice this would use LLM
        return [
            {
                'id': 1,
                'description': f'Analyze the task: {task}',
                'type': 'analysis',
                'optional': False
            },
            {
                'id': 2,
                'description': 'Execute the required actions',
                'type': 'execution',
                'optional': False
            },
            {
                'id': 3,
                'description': 'Verify the results',
                'type': 'verification',
                'optional': True
            }
        ]
    
    async def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step"""
        try:
            step_type = step.get('type', 'general')
            description = step.get('description', '')
            
            # Simulate step execution based on type
            if step_type == 'analysis':
                result = await self._execute_analysis_step(description, context)
            elif step_type == 'execution':
                result = await self._execute_action_step(description, context)
            elif step_type == 'verification':
                result = await self._execute_verification_step(description, context)
            else:
                result = await self._execute_general_step(description, context)
            
            return {
                'success': True,
                'step_id': step.get('id'),
                'result': result,
                'context_updates': result.get('context_updates', {})
            }
            
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return {
                'success': False,
                'step_id': step.get('id'),
                'error': str(e)
            }
    
    async def _execute_analysis_step(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis step"""
        return {
            'type': 'analysis',
            'description': description,
            'analysis_result': f"Analyzed: {description}",
            'context_updates': {'last_analysis': description}
        }
    
    async def _execute_action_step(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action step"""
        return {
            'type': 'action',
            'description': description,
            'action_result': f"Executed: {description}",
            'context_updates': {'last_action': description}
        }
    
    async def _execute_verification_step(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute verification step"""
        return {
            'type': 'verification',
            'description': description,
            'verification_result': f"Verified: {description}",
            'context_updates': {'last_verification': description}
        }
    
    async def _execute_general_step(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general step"""
        return {
            'type': 'general',
            'description': description,
            'result': f"Completed: {description}",
            'context_updates': {}
        }
    
    async def _learn_from_execution(self, task: str, solution: Dict[str, Any]) -> None:
        """Learn from execution results"""
        if not self.recall_manager:
            return
        
        try:
            # Create recall entry from execution
            success = solution.get('success', False)
            reward = 1.0 if success else 0.0
            
            # Create plan text from execution steps
            steps = solution.get('execution_steps', [])
            plan_data = {'plan': steps}
            plan_text = json.dumps(plan_data)
            
            # Create recall entry
            recall_entry = RecallEntry(
                question=task,
                plan=plan_text,
                reward=reward,
                timestamp=datetime.now(),
                metadata={
                    'agent_id': self.agent_id,
                    'execution_time': datetime.now().isoformat(),
                    'success': success,
                    'steps_count': len(steps)
                }
            )
            
            # Add to recall manager
            await self.recall_manager.add_recall(recall_entry)
            
            logger.info(f"Learned from execution: task='{task[:50]}...', reward={reward}")
            
        except Exception as e:
            logger.error(f"Failed to learn from execution: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'current_task': self.current_task,
            'execution_history_length': len(self.execution_history),
            'interpreters_available': list(self.interpreters.keys()),
            'recall_manager_available': self.recall_manager is not None,
            'max_iterations': self.max_iterations,
            'similarity_threshold': self.similarity_threshold
        }
