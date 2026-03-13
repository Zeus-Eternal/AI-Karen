"""
Agent Reasoning service for providing sophisticated reasoning capabilities to agents.

This service provides various reasoning mechanisms including logical reasoning, causal reasoning,
probabilistic reasoning, and strategic thinking to enhance agent decision-making capabilities.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union, Tuple, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import numpy as np
try:
    from pydantic import BaseModel, Field, ConfigDict
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field, ConfigDict

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

# Try to import AI Orchestrator
try:
    from src.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
    HAS_AI_ORCHESTRATOR = True
except ImportError:
    HAS_AI_ORCHESTRATOR = False
    AIOrchestrator = None

logger = logging.getLogger(__name__)


class ReasoningType(str, Enum):
    """Reasoning type enumeration."""
    LOGICAL = "logical"
    CAUSAL = "causal"
    PROBABILISTIC = "probabilistic"
    STRATEGIC = "strategic"
    ANALOGICAL = "analogical"
    DIALECTICAL = "dialectical"
    PRACTICAL = "practical"


class ReasoningStrategy(str, Enum):
    """Reasoning strategy enumeration."""
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    BAYESIAN = "bayesian"
    FUZZY = "fuzzy"
    HEURISTIC = "heuristic"
    SYSTEMATIC = "systematic"


class ReasoningConfidence(str, Enum):
    """Reasoning confidence level enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@dataclass
class ReasoningContext:
    """Context for reasoning operations."""
    context_id: str
    agent_id: str
    reasoning_type: ReasoningType
    strategy: ReasoningStrategy
    data: Dict[str, Any] = field(default_factory=dict)
    premises: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningStep:
    """Single step in a reasoning process."""
    step_id: str
    reasoning_type: ReasoningType
    strategy: ReasoningStrategy
    premise: str
    conclusion: str
    confidence: ReasoningConfidence
    justification: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningResult:
    """Result of a reasoning operation."""
    reasoning_id: str
    context_id: str
    conclusion: str
    confidence: ReasoningConfidence
    steps: List[ReasoningStep]
    alternatives: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    certainties: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReasoningEngine(ABC):
    """Abstract base class for reasoning engines."""
    
    @abstractmethod
    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """Perform reasoning based on the given context."""
        pass
    
    @abstractmethod
    def supports_reasoning_type(self, reasoning_type: ReasoningType) -> bool:
        """Check if this engine supports the given reasoning type."""
        pass


class LogicalReasoningEngine(ReasoningEngine):
    """Engine for logical reasoning operations."""
    
    def __init__(self):
        self._logical_operators = {
            "AND": lambda x, y: x and y,
            "OR": lambda x, y: x or y,
            "NOT": lambda x: not x,
            "IMPLIES": lambda x, y: (not x) or y,
            "EQUIVALENT": lambda x, y: x == y
        }
    
    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """Perform logical reasoning."""
        reasoning_id = str(uuid.uuid4())
        steps = []
        
        # Extract premises from context
        premises = context.premises
        if not premises:
            premises = context.data.get("premises", [])
        
        # Apply logical reasoning based on strategy
        if context.strategy == ReasoningStrategy.DEDUCTIVE:
            result, step = await self._deductive_reasoning(premises, context.data)
        elif context.strategy == ReasoningStrategy.INDUCTIVE:
            result, step = await self._inductive_reasoning(premises, context.data)
        elif context.strategy == ReasoningStrategy.ABDUCTIVE:
            result, step = await self._abductive_reasoning(premises, context.data)
        else:
            # Default to deductive reasoning
            result, step = await self._deductive_reasoning(premises, context.data)
        
        steps.append(step)
        
        # Create reasoning result
        return ReasoningResult(
            reasoning_id=reasoning_id,
            context_id=context.context_id,
            conclusion=result,
            confidence=step.confidence,
            steps=steps
        )
    
    def supports_reasoning_type(self, reasoning_type: ReasoningType) -> bool:
        """Check if this engine supports the given reasoning type."""
        return reasoning_type == ReasoningType.LOGICAL
    
    async def _deductive_reasoning(self, premises: List[str], data: Dict[str, Any]) -> Tuple[str, ReasoningStep]:
        """Perform deductive reasoning."""
        if len(premises) < 2:
            return "Insufficient premises for deductive reasoning", ReasoningStep(
                step_id=str(uuid.uuid4()),
                reasoning_type=ReasoningType.LOGICAL,
                strategy=ReasoningStrategy.DEDUCTIVE,
                premise="; ".join(premises),
                conclusion="Insufficient premises",
                confidence=ReasoningConfidence.LOW,
                justification="Deductive reasoning requires at least two premises"
            )
        
        # Simple deductive reasoning: If P and P->Q, then Q
        premise1 = premises[0]
        premise2 = premises[1]
        
        # Check if premise2 is an implication
        if "->" in premise2:
            parts = premise2.split("->")
            if len(parts) == 2 and parts[0].strip() == premise1:
                conclusion = parts[1].strip()
                return conclusion, ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    reasoning_type=ReasoningType.LOGICAL,
                    strategy=ReasoningStrategy.DEDUCTIVE,
                    premise=f"{premise1} and {premise2}",
                    conclusion=conclusion,
                    confidence=ReasoningConfidence.HIGH,
                    justification=f"From {premise1} and {premise2}, we deduce {conclusion}"
                )
        
        # Default case
        conclusion = f"Cannot deduce conclusion from premises: {premise1}, {premise2}"
        return conclusion, ReasoningStep(
            step_id=str(uuid.uuid4()),
            reasoning_type=ReasoningType.LOGICAL,
            strategy=ReasoningStrategy.DEDUCTIVE,
            premise=f"{premise1} and {premise2}",
            conclusion=conclusion,
            confidence=ReasoningConfidence.LOW,
            justification="No clear logical implication found"
        )
    
    async def _inductive_reasoning(self, premises: List[str], data: Dict[str, Any]) -> Tuple[str, ReasoningStep]:
        """Perform inductive reasoning."""
        if not premises:
            return "No premises for inductive reasoning", ReasoningStep(
                step_id=str(uuid.uuid4()),
                reasoning_type=ReasoningType.LOGICAL,
                strategy=ReasoningStrategy.INDUCTIVE,
                premise="No premises",
                conclusion="No conclusion",
                confidence=ReasoningConfidence.LOW,
                justification="Inductive reasoning requires at least one premise"
            )
        
        # Simple inductive reasoning: Generalize from specific instances
        if len(premises) >= 3:
            # Look for patterns in premises
            first_premise = premises[0]
            if "is" in first_premise:
                parts = first_premise.split(" is ")
                if len(parts) == 2:
                    subject = parts[0]
                    property1 = parts[1]
                    
                    # Check if other premises have the same property
                    all_have_property = True
                    for premise in premises[1:]:
                        if f"{subject} is {property1}" not in premise:
                            all_have_property = False
                            break
                    
                    if all_have_property:
                        conclusion = f"All {subject} are {property1}"
                        return conclusion, ReasoningStep(
                            step_id=str(uuid.uuid4()),
                            reasoning_type=ReasoningType.LOGICAL,
                            strategy=ReasoningStrategy.INDUCTIVE,
                            premise="; ".join(premises),
                            conclusion=conclusion,
                            confidence=ReasoningConfidence.MEDIUM,
                            justification=f"All observed instances of {subject} have property {property1}"
                        )
        
        # Default case
        conclusion = f"Cannot generalize from premises: {'; '.join(premises)}"
        return conclusion, ReasoningStep(
            step_id=str(uuid.uuid4()),
            reasoning_type=ReasoningType.LOGICAL,
            strategy=ReasoningStrategy.INDUCTIVE,
            premise="; ".join(premises),
            conclusion=conclusion,
            confidence=ReasoningConfidence.LOW,
            justification="No clear pattern found for generalization"
        )
    
    async def _abductive_reasoning(self, premises: List[str], data: Dict[str, Any]) -> Tuple[str, ReasoningStep]:
        """Perform abductive reasoning."""
        if not premises:
            return "No premises for abductive reasoning", ReasoningStep(
                step_id=str(uuid.uuid4()),
                reasoning_type=ReasoningType.LOGICAL,
                strategy=ReasoningStrategy.ABDUCTIVE,
                premise="No premises",
                conclusion="No conclusion",
                confidence=ReasoningConfidence.LOW,
                justification="Abductive reasoning requires at least one premise"
            )
        
        # Simple abductive reasoning: Infer the best explanation
        observation = premises[0]
        
        # Generate possible explanations
        explanations = [
            f"{observation} because of natural causes",
            f"{observation} because of human intervention",
            f"{observation} because of external factors"
        ]
        
        # For now, just return the first explanation
        conclusion = explanations[0]
        return conclusion, ReasoningStep(
            step_id=str(uuid.uuid4()),
            reasoning_type=ReasoningType.LOGICAL,
            strategy=ReasoningStrategy.ABDUCTIVE,
            premise=observation,
            conclusion=conclusion,
            confidence=ReasoningConfidence.MEDIUM,
            justification=f"Abduced explanation for {observation}"
        )


class CausalReasoningEngine(ReasoningEngine):
    """Engine for causal reasoning operations."""
    
    def __init__(self):
        self._causal_models = {}
    
    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """Perform causal reasoning."""
        reasoning_id = str(uuid.uuid4())
        steps = []
        
        # Extract causal information from context
        causal_data = context.data.get("causal_data", {})
        cause = causal_data.get("cause")
        effect = causal_data.get("effect")
        
        if not cause or not effect:
            result = "Insufficient causal information"
            step = ReasoningStep(
                step_id=str(uuid.uuid4()),
                reasoning_type=ReasoningType.CAUSAL,
                strategy=ReasoningStrategy.SYSTEMATIC,
                premise="No causal information provided",
                conclusion=result,
                confidence=ReasoningConfidence.LOW,
                justification="Causal reasoning requires cause and effect information"
            )
        else:
            # Simple causal reasoning
            result = f"{cause} causes {effect}"
            step = ReasoningStep(
                step_id=str(uuid.uuid4()),
                reasoning_type=ReasoningType.CAUSAL,
                strategy=ReasoningStrategy.SYSTEMATIC,
                premise=f"Observed: {cause} is associated with {effect}",
                conclusion=result,
                confidence=ReasoningConfidence.MEDIUM,
                justification=f"Based on observed association, {cause} appears to cause {effect}"
            )
        
        steps.append(step)
        
        # Create reasoning result
        return ReasoningResult(
            reasoning_id=reasoning_id,
            context_id=context.context_id,
            conclusion=result,
            confidence=step.confidence,
            steps=steps
        )
    
    def supports_reasoning_type(self, reasoning_type: ReasoningType) -> bool:
        """Check if this engine supports the given reasoning type."""
        return reasoning_type == ReasoningType.CAUSAL


class ProbabilisticReasoningEngine(ReasoningEngine):
    """Engine for probabilistic reasoning operations."""
    
    def __init__(self):
        self._probabilistic_models = {}
    
    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """Perform probabilistic reasoning."""
        reasoning_id = str(uuid.uuid4())
        steps = []
        
        # Extract probabilistic information from context
        prob_data = context.data.get("probabilistic_data", {})
        events = prob_data.get("events", [])
        probabilities = prob_data.get("probabilities", {})
        
        if not events or not probabilities:
            result = "Insufficient probabilistic information"
            step = ReasoningStep(
                step_id=str(uuid.uuid4()),
                reasoning_type=ReasoningType.PROBABILISTIC,
                strategy=ReasoningStrategy.BAYESIAN,
                premise="No probabilistic information provided",
                conclusion=result,
                confidence=ReasoningConfidence.LOW,
                justification="Probabilistic reasoning requires events and probabilities"
            )
        else:
            # Simple probabilistic reasoning
            if len(events) >= 2:
                event1, event2 = events[0], events[1]
                prob1 = probabilities.get(event1, 0.5)
                prob2 = probabilities.get(event2, 0.5)
                
                # Calculate joint probability (assuming independence)
                joint_prob = prob1 * prob2
                
                result = f"Probability of both {event1} and {event2} occurring: {joint_prob:.2f}"
                confidence_level = ReasoningConfidence.HIGH if joint_prob > 0.7 else ReasoningConfidence.MEDIUM if joint_prob > 0.3 else ReasoningConfidence.LOW
                
                step = ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    reasoning_type=ReasoningType.PROBABILISTIC,
                    strategy=ReasoningStrategy.BAYESIAN,
                    premise=f"P({event1}) = {prob1:.2f}, P({event2}) = {prob2:.2f}",
                    conclusion=result,
                    confidence=confidence_level,
                    justification=f"Calculated assuming independence: P({event1} and {event2}) = P({event1}) × P({event2})"
                )
            else:
                result = "Need at least two events for probabilistic reasoning"
                step = ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    reasoning_type=ReasoningType.PROBABILISTIC,
                    strategy=ReasoningStrategy.BAYESIAN,
                    premise=f"Only {len(events)} event(s) provided",
                    conclusion=result,
                    confidence=ReasoningConfidence.LOW,
                    justification="Probabilistic reasoning with multiple events requires at least two events"
                )
        
        steps.append(step)
        
        # Create reasoning result
        return ReasoningResult(
            reasoning_id=reasoning_id,
            context_id=context.context_id,
            conclusion=result,
            confidence=step.confidence,
            steps=steps
        )
    
    def supports_reasoning_type(self, reasoning_type: ReasoningType) -> bool:
        """Check if this engine supports the given reasoning type."""
        return reasoning_type == ReasoningType.PROBABILISTIC


class StrategicReasoningEngine(ReasoningEngine):
    """Engine for strategic reasoning operations."""
    
    def __init__(self):
        self._strategic_models = {}
    
    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """Perform strategic reasoning."""
        reasoning_id = str(uuid.uuid4())
        steps = []
        
        # Extract strategic information from context
        goals = context.goals
        constraints = context.constraints
        strategic_data = context.data.get("strategic_data", {})
        
        if not goals:
            result = "No goals provided for strategic reasoning"
            step = ReasoningStep(
                step_id=str(uuid.uuid4()),
                reasoning_type=ReasoningType.STRATEGIC,
                strategy=ReasoningStrategy.HEURISTIC,
                premise="No goals provided",
                conclusion=result,
                confidence=ReasoningConfidence.LOW,
                justification="Strategic reasoning requires goals"
            )
        else:
            # Simple strategic reasoning
            primary_goal = goals[0]
            
            # Consider constraints
            constraint_text = ""
            if constraints:
                constraint_text = f" considering constraints: {', '.join(constraints)}"
            
            result = f"Strategic approach to achieve {primary_goal}{constraint_text}"
            step = ReasoningStep(
                step_id=str(uuid.uuid4()),
                reasoning_type=ReasoningType.STRATEGIC,
                strategy=ReasoningStrategy.HEURISTIC,
                premise=f"Goal: {primary_goal}",
                conclusion=result,
                confidence=ReasoningConfidence.MEDIUM,
                justification=f"Developed strategic approach for {primary_goal}"
            )
        
        steps.append(step)
        
        # Create reasoning result
        return ReasoningResult(
            reasoning_id=reasoning_id,
            context_id=context.context_id,
            conclusion=result,
            confidence=step.confidence,
            steps=steps
        )
    
    def supports_reasoning_type(self, reasoning_type: ReasoningType) -> bool:
        """Check if this engine supports the given reasoning type."""
        return reasoning_type == ReasoningType.STRATEGIC


class AgentReasoning(BaseService):
    """
    Agent Reasoning service for providing sophisticated reasoning capabilities to agents.
    
    This service provides various reasoning mechanisms including logical reasoning, causal reasoning,
    probabilistic reasoning, and strategic thinking to enhance agent decision-making capabilities.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="agent_reasoning"))
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Core services
        self._ai_orchestrator = None
        
        # Reasoning engines
        self._reasoning_engines = {
            ReasoningType.LOGICAL: LogicalReasoningEngine(),
            ReasoningType.CAUSAL: CausalReasoningEngine(),
            ReasoningType.PROBABILISTIC: ProbabilisticReasoningEngine(),
            ReasoningType.STRATEGIC: StrategicReasoningEngine()
        }
        
        # Reasoning contexts and results
        self._reasoning_contexts: Dict[str, ReasoningContext] = {}
        self._reasoning_results: Dict[str, ReasoningResult] = {}
        
        # Configuration
        self._config = {
            "default_reasoning_type": ReasoningType.LOGICAL,
            "default_strategy": ReasoningStrategy.DEDUCTIVE,
            "max_reasoning_steps": 100,
            "enable_validation": True,
            "enable_alternatives": True,
            "enable_contradiction_detection": True
        }
        
        # Performance metrics
        self._metrics = {
            "reasoning_operations": 0,
            "successful_reasoning": 0,
            "failed_reasoning": 0,
            "avg_reasoning_time_ms": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the agent reasoning service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Agent Reasoning service")
            
            # Initialize with AI Orchestrator if available
            if HAS_AI_ORCHESTRATOR and AIOrchestrator:
                self._ai_orchestrator = AIOrchestrator(config=ServiceConfig(name="ai_orchestrator"))
                await self._ai_orchestrator.initialize()
            else:
                self._ai_orchestrator = None
                self.logger.info("AI Orchestrator not available, running in standalone mode")
            
            self._initialized = True
            self.logger.info("Agent Reasoning service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Agent Reasoning service: {e}")
            raise
    
    async def start(self) -> None:
        """Start the agent reasoning service."""
        self.logger.info("Agent Reasoning service started")
    
    async def stop(self) -> None:
        """Stop the agent reasoning service."""
        self.logger.info("Agent Reasoning service stopped")
    
    async def health_check(self) -> bool:
        """Check health of the agent reasoning service."""
        return self._initialized
    
    async def create_reasoning_context(
        self,
        agent_id: str,
        reasoning_type: ReasoningType,
        strategy: ReasoningStrategy,
        data: Dict[str, Any],
        premises: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        goals: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a reasoning context.
        
        Args:
            agent_id: ID of the agent
            reasoning_type: Type of reasoning
            strategy: Reasoning strategy
            data: Data for reasoning
            premises: Optional list of premises
            assumptions: Optional list of assumptions
            constraints: Optional list of constraints
            goals: Optional list of goals
            metadata: Optional metadata
            
        Returns:
            Context ID
        """
        if not self._initialized:
            await self.initialize()
        
        context_id = str(uuid.uuid4())
        
        context = ReasoningContext(
            context_id=context_id,
            agent_id=agent_id,
            reasoning_type=reasoning_type,
            strategy=strategy,
            data=data,
            premises=premises or [],
            assumptions=assumptions or [],
            constraints=constraints or [],
            goals=goals or [],
            metadata=metadata or {}
        )
        
        async with self._lock:
            self._reasoning_contexts[context_id] = context
        
        self.logger.info(f"Created reasoning context {context_id} for agent {agent_id}")
        return context_id
    
    async def perform_reasoning(
        self,
        context_id: str,
        validate: bool = True,
        generate_alternatives: bool = True,
        detect_contradictions: bool = True
    ) -> Dict[str, Any]:
        """
        Perform reasoning based on a context.
        
        Args:
            context_id: ID of the reasoning context
            validate: Whether to validate the reasoning
            generate_alternatives: Whether to generate alternative conclusions
            detect_contradictions: Whether to detect contradictions
            
        Returns:
            Reasoning result
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        self._metrics["reasoning_operations"] += 1
        
        try:
            # Get reasoning context
            async with self._lock:
                if context_id not in self._reasoning_contexts:
                    return {"success": False, "error": f"Reasoning context {context_id} not found"}
                
                context = self._reasoning_contexts[context_id]
            
            # Get appropriate reasoning engine
            reasoning_engine = self._reasoning_engines.get(context.reasoning_type)
            if not reasoning_engine:
                return {"success": False, "error": f"Reasoning engine for {context.reasoning_type} not found"}
            
            # Perform reasoning
            result = await reasoning_engine.reason(context)
            
            # Validate reasoning if requested
            if validate and self._config.get("enable_validation", True):
                validation_result = await self._validate_reasoning(result)
                if not validation_result.get("valid", True):
                    result.contradictions.append(f"Validation failed: {validation_result.get('reason', 'Unknown error')}")
            
            # Generate alternatives if requested
            if generate_alternatives and self._config.get("enable_alternatives", True):
                alternatives = await self._generate_alternatives(context)
                result.alternatives.extend(alternatives)
            
            # Detect contradictions if requested
            if detect_contradictions and self._config.get("enable_contradiction_detection", True):
                contradictions = await self._detect_contradictions(result)
                result.contradictions.extend(contradictions)
            
            # Store reasoning result
            async with self._lock:
                self._reasoning_results[result.reasoning_id] = result
            
            # Record metrics
            operation_time_ms = (time.time() - start_time) * 1000
            self._metrics["avg_reasoning_time_ms"] = (
                self._metrics["avg_reasoning_time_ms"] * 0.9 + operation_time_ms * 0.1
            )
            self._metrics["successful_reasoning"] += 1
            
            self.logger.info(f"Completed reasoning {result.reasoning_id} for agent {context.agent_id}")
            
            return {
                "success": True,
                "reasoning_id": result.reasoning_id,
                "context_id": context_id,
                "conclusion": result.conclusion,
                "confidence": result.confidence,
                "steps": [self._reasoning_step_to_dict(step) for step in result.steps],
                "alternatives": result.alternatives,
                "contradictions": result.contradictions,
                "certainties": result.certainties,
                "timestamp": result.timestamp.isoformat()
            }
            
        except Exception as e:
            self._metrics["failed_reasoning"] += 1
            self.logger.error(f"Error performing reasoning for context {context_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _reasoning_step_to_dict(self, step: ReasoningStep) -> Dict[str, Any]:
        """Convert a reasoning step to a dictionary."""
        return {
            "step_id": step.step_id,
            "reasoning_type": step.reasoning_type,
            "strategy": step.strategy,
            "premise": step.premise,
            "conclusion": step.conclusion,
            "confidence": step.confidence,
            "justification": step.justification,
            "timestamp": step.timestamp.isoformat(),
            "metadata": step.metadata
        }
    
    async def _validate_reasoning(self, result: ReasoningResult) -> Dict[str, Any]:
        """Validate a reasoning result."""
        # Simple validation: check if steps are logically consistent
        for step in result.steps:
            if step.strategy == ReasoningStrategy.DEDUCTIVE:
                # For deductive reasoning, check if conclusion follows from premises
                if "cannot" in step.conclusion.lower():
                    return {"valid": False, "reason": "Deductive reasoning resulted in negative conclusion"}
        
        return {"valid": True}
    
    async def _generate_alternatives(self, context: ReasoningContext) -> List[str]:
        """Generate alternative conclusions."""
        alternatives = []
        
        if context.reasoning_type == ReasoningType.LOGICAL:
            if context.strategy == ReasoningStrategy.DEDUCTIVE:
                alternatives.append("Conclusion may not follow if premises are false")
                alternatives.append("Alternative logical interpretations may exist")
            elif context.strategy == ReasoningStrategy.INDUCTIVE:
                alternatives.append("Different generalizations may be possible")
                alternatives.append("Sample may not be representative")
            elif context.strategy == ReasoningStrategy.ABDUCTIVE:
                alternatives.append("Alternative explanations may exist")
                alternatives.append("Explanation may not be the most likely")
        
        elif context.reasoning_type == ReasoningType.CAUSAL:
            alternatives.append("Correlation does not imply causation")
            alternatives.append("Reverse causation may be possible")
            alternatives.append("Confounding factors may exist")
        
        elif context.reasoning_type == ReasoningType.PROBABILISTIC:
            alternatives.append("Different probability distributions may fit the data")
            alternatives.append("Events may not be independent")
            alternatives.append("Prior probabilities may affect the result")
        
        elif context.reasoning_type == ReasoningType.STRATEGIC:
            alternatives.append("Alternative strategies may achieve the same goals")
            alternatives.append("Goals may need to be re-prioritized")
            alternatives.append("Constraints may be relaxed for better outcomes")
        
        return alternatives[:3]  # Return at most 3 alternatives
    
    async def _detect_contradictions(self, result: ReasoningResult) -> List[str]:
        """Detect contradictions in reasoning."""
        contradictions = []
        
        # Check for direct contradictions in steps
        for i, step1 in enumerate(result.steps):
            for step2 in result.steps[i+1:]:
                if (step1.strategy == step2.strategy and 
                    step1.premise == step2.premise and 
                    step1.conclusion != step2.conclusion):
                    contradictions.append(f"Contradictory conclusions from same premises: {step1.conclusion} vs {step2.conclusion}")
        
        return contradictions
    
    async def get_reasoning_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a reasoning context.
        
        Args:
            context_id: ID of the reasoning context
            
        Returns:
            Reasoning context if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._lock:
            if context_id in self._reasoning_contexts:
                context = self._reasoning_contexts[context_id]
                return {
                    "context_id": context.context_id,
                    "agent_id": context.agent_id,
                    "reasoning_type": context.reasoning_type,
                    "strategy": context.strategy,
                    "data": context.data,
                    "premises": context.premises,
                    "assumptions": context.assumptions,
                    "constraints": context.constraints,
                    "goals": context.goals,
                    "created_at": context.created_at.isoformat(),
                    "metadata": context.metadata
                }
            return None
    
    async def get_reasoning_result(self, reasoning_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a reasoning result.
        
        Args:
            reasoning_id: ID of the reasoning result
            
        Returns:
            Reasoning result if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._lock:
            if reasoning_id in self._reasoning_results:
                result = self._reasoning_results[reasoning_id]
                return {
                    "reasoning_id": result.reasoning_id,
                    "context_id": result.context_id,
                    "conclusion": result.conclusion,
                    "confidence": result.confidence,
                    "steps": [self._reasoning_step_to_dict(step) for step in result.steps],
                    "alternatives": result.alternatives,
                    "contradictions": result.contradictions,
                    "certainties": result.certainties,
                    "timestamp": result.timestamp.isoformat(),
                    "metadata": result.metadata
                }
            return None
    
    async def logical_reasoning(
        self,
        agent_id: str,
        premises: List[str],
        strategy: ReasoningStrategy = ReasoningStrategy.DEDUCTIVE,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform logical reasoning.
        
        Args:
            agent_id: ID of the agent
            premises: List of premises
            strategy: Reasoning strategy
            data: Additional data
            
        Returns:
            Reasoning result
        """
        if not self._initialized:
            await self.initialize()
        
        # Create reasoning context
        context_id = await self.create_reasoning_context(
            agent_id=agent_id,
            reasoning_type=ReasoningType.LOGICAL,
            strategy=strategy,
            data=data or {},
            premises=premises
        )
        
        # Perform reasoning
        return await self.perform_reasoning(context_id)
    
    async def causal_reasoning(
        self,
        agent_id: str,
        cause: str,
        effect: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform causal reasoning.
        
        Args:
            agent_id: ID of the agent
            cause: Cause in the causal relationship
            effect: Effect in the causal relationship
            data: Additional data
            
        Returns:
            Reasoning result
        """
        if not self._initialized:
            await self.initialize()
        
        # Create reasoning context
        context_id = await self.create_reasoning_context(
            agent_id=agent_id,
            reasoning_type=ReasoningType.CAUSAL,
            strategy=ReasoningStrategy.SYSTEMATIC,
            data={
                "causal_data": {
                    "cause": cause,
                    "effect": effect
                },
                **(data or {})
            }
        )
        
        # Perform reasoning
        return await self.perform_reasoning(context_id)
    
    async def probabilistic_reasoning(
        self,
        agent_id: str,
        events: List[str],
        probabilities: Dict[str, float],
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform probabilistic reasoning.
        
        Args:
            agent_id: ID of the agent
            events: List of events
            probabilities: Probabilities of events
            data: Additional data
            
        Returns:
            Reasoning result
        """
        if not self._initialized:
            await self.initialize()
        
        # Create reasoning context
        context_id = await self.create_reasoning_context(
            agent_id=agent_id,
            reasoning_type=ReasoningType.PROBABILISTIC,
            strategy=ReasoningStrategy.BAYESIAN,
            data={
                "probabilistic_data": {
                    "events": events,
                    "probabilities": probabilities
                },
                **(data or {})
            }
        )
        
        # Perform reasoning
        return await self.perform_reasoning(context_id)
    
    async def strategic_reasoning(
        self,
        agent_id: str,
        goals: List[str],
        constraints: List[str],
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform strategic reasoning.
        
        Args:
            agent_id: ID of the agent
            goals: List of goals
            constraints: List of constraints
            data: Additional data
            
        Returns:
            Reasoning result
        """
        if not self._initialized:
            await self.initialize()
        
        # Create reasoning context
        context_id = await self.create_reasoning_context(
            agent_id=agent_id,
            reasoning_type=ReasoningType.STRATEGIC,
            strategy=ReasoningStrategy.HEURISTIC,
            data=data or {},
            goals=goals,
            constraints=constraints
        )
        
        # Perform reasoning
        return await self.perform_reasoning(context_id)
    
    async def get_reasoning_metrics(self) -> Dict[str, Any]:
        """
        Get reasoning metrics.
        
        Returns:
            Reasoning metrics
        """
        return {
            "reasoning_operations": self._metrics["reasoning_operations"],
            "successful_reasoning": self._metrics["successful_reasoning"],
            "failed_reasoning": self._metrics["failed_reasoning"],
            "avg_reasoning_time_ms": self._metrics["avg_reasoning_time_ms"],
            "success_rate": (
                self._metrics["successful_reasoning"] / 
                max(1, self._metrics["reasoning_operations"])
            ) if self._metrics["reasoning_operations"] > 0 else 0.0
        }