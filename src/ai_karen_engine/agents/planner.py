"""
Agent Planner Core Implementation - Soft Reasoning Engine

This module implements human-like cognitive architecture with soft reasoning,
probabilistic confidence scores, multiple solution pathways, and auditable
cognition trails. The planner composes tools based on IndexHub context
and episodic memory while maintaining emotional awareness and uncertainty
quantification.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import math
import random

from ai_karen_engine.services.knowledge.index_hub import (
    IndexHub, 
    KnowledgeQuery, 
    KnowledgeResult,
    Department,
    Team,
    Citation
)
from ai_karen_engine.services.cognitive.episodic_memory import (
    EpisodicMemoryService,
    EpisodicMemory,
    EmotionalMarker,
    EmotionalValence,
    InteractionOutcome,
    ContextImportance
)
from ai_karen_engine.services.cognitive.working_memory import WorkingMemoryService
from ai_karen_engine.services.tools.registry import CopilotToolRegistry, CopilotToolService
from ai_karen_engine.services.tools.contracts import (
    ToolContext,
    ToolResult,
    ToolScope,
    RBACLevel,
    PrivacyLevel,
    ExecutionMode
)


class ConfidenceLevel(Enum):
    """Confidence levels for reasoning and decisions."""
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


class RiskLevel(Enum):
    """Risk levels for plan steps and operations."""
    MINIMAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class ReasoningType(Enum):
    """Types of reasoning patterns."""
    DEDUCTIVE = "deductive"  # From general to specific
    INDUCTIVE = "inductive"  # From specific to general
    ABDUCTIVE = "abductive"  # Best explanation
    ANALOGICAL = "analogical"  # By analogy
    CAUSAL = "causal"  # Cause and effect
    PROBABILISTIC = "probabilistic"  # Uncertainty-based


class EmotionalContext(Enum):
    """Emotional context for decision making."""
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    CAUTIOUS = "cautious"
    OPTIMISTIC = "optimistic"
    CONCERNED = "concerned"
    FRUSTRATED = "frustrated"
    CURIOUS = "curious"
    FOCUSED = "focused"


@dataclass
class ConfidenceScore:
    """Represents confidence in a decision or reasoning step."""
    value: float  # 0.0 to 1.0
    reasoning: str
    evidence_count: int
    uncertainty_factors: List[str] = field(default_factory=list)
    confidence_level: ConfidenceLevel = field(init=False)
    
    def __post_init__(self):
        """Calculate confidence level from value."""
        if self.value >= 0.9:
            self.confidence_level = ConfidenceLevel.VERY_HIGH
        elif self.value >= 0.7:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.value >= 0.5:
            self.confidence_level = ConfidenceLevel.MEDIUM
        elif self.value >= 0.3:
            self.confidence_level = ConfidenceLevel.LOW
        else:
            self.confidence_level = ConfidenceLevel.VERY_LOW
    
    def express_doubt(self) -> Optional[str]:
        """Express doubt when confidence is low."""
        if self.value < 0.5:
            doubt_expressions = [
                f"I'm not entirely certain about this because {', '.join(self.uncertainty_factors[:2])}",
                f"There's some uncertainty here - {self.reasoning}",
                f"I have concerns about this approach due to {self.uncertainty_factors[0] if self.uncertainty_factors else 'limited evidence'}",
                f"This might not be the best solution because {self.reasoning}"
            ]
            return random.choice(doubt_expressions)
        return None


@dataclass
class RiskAssessment:
    """Risk assessment for plan steps and operations."""
    level: RiskLevel
    factors: List[str]
    mitigation_strategies: List[str] = field(default_factory=list)
    impact_description: str = ""
    probability: float = 0.5  # 0.0 to 1.0
    
    def calculate_risk_score(self) -> float:
        """Calculate overall risk score."""
        return (self.level.value / 5.0) * self.probability
    
    def requires_approval(self) -> bool:
        """Check if this risk level requires approval."""
        return self.level.value >= RiskLevel.HIGH.value


@dataclass
class ReasoningStep:
    """Individual step in a reasoning chain."""
    step_id: str
    reasoning_type: ReasoningType
    premise: str
    conclusion: str
    evidence: List[Citation]
    confidence: ConfidenceScore
    alternatives_considered: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_natural_language(self) -> str:
        """Convert reasoning step to natural language."""
        connectors = {
            ReasoningType.DEDUCTIVE: "Therefore",
            ReasoningType.INDUCTIVE: "This suggests that",
            ReasoningType.ABDUCTIVE: "The best explanation is that",
            ReasoningType.ANALOGICAL: "Similarly",
            ReasoningType.CAUSAL: "Because of this",
            ReasoningType.PROBABILISTIC: "It's likely that"
        }
        
        connector = connectors.get(self.reasoning_type, "Considering this")
        
        explanation = f"{self.premise}. {connector}, {self.conclusion}"
        
        if self.confidence.value < 0.7:
            doubt = self.confidence.express_doubt()
            if doubt:
                explanation += f" However, {doubt}"
        
        return explanation


@dataclass
class CognitionTrail:
    """Auditable trail of reasoning steps and decision points."""
    trail_id: str
    user_id: str
    session_id: str
    query: str
    
    # Reasoning chain
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    decision_points: List[Dict[str, Any]] = field(default_factory=list)
    evidence_weighting: Dict[str, float] = field(default_factory=dict)
    
    # Emotional and contextual factors
    emotional_context: EmotionalContext = EmotionalContext.FOCUSED
    user_interaction_history: List[str] = field(default_factory=list)
    
    # Outcomes and learning
    final_confidence: Optional[ConfidenceScore] = None
    alternative_pathways: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def add_reasoning_step(
        self,
        reasoning_type: ReasoningType,
        premise: str,
        conclusion: str,
        evidence: List[Citation],
        confidence: ConfidenceScore,
        alternatives: Optional[List[str]] = None
    ) -> str:
        """Add a reasoning step to the trail."""
        step_id = str(uuid.uuid4())
        step = ReasoningStep(
            step_id=step_id,
            reasoning_type=reasoning_type,
            premise=premise,
            conclusion=conclusion,
            evidence=evidence,
            confidence=confidence,
            alternatives_considered=alternatives or []
        )
        self.reasoning_steps.append(step)
        return step_id
    
    def add_decision_point(
        self,
        decision: str,
        options: List[str],
        chosen_option: str,
        reasoning: str,
        confidence: float
    ):
        """Add a decision point to the trail."""
        self.decision_points.append({
            "decision": decision,
            "options": options,
            "chosen": chosen_option,
            "reasoning": reasoning,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def generate_explanation(self) -> str:
        """Generate natural language explanation of the reasoning process."""
        if not self.reasoning_steps:
            return "No reasoning steps recorded."
        
        explanation_parts = [
            f"Here's how I approached your request: '{self.query}'"
        ]
        
        for i, step in enumerate(self.reasoning_steps, 1):
            explanation_parts.append(f"{i}. {step.to_natural_language()}")
        
        if self.final_confidence:
            confidence_text = f"Overall, I'm {self.final_confidence.confidence_level.name.lower().replace('_', ' ')} confident in this approach"
            if self.final_confidence.value < 0.7:
                doubt = self.final_confidence.express_doubt()
                if doubt:
                    confidence_text += f", though {doubt.lower()}"
            explanation_parts.append(confidence_text + ".")
        
        if self.alternative_pathways:
            explanation_parts.append(
                f"I also considered these alternatives: {', '.join(self.alternative_pathways[:3])}"
            )
        
        return "\n\n".join(explanation_parts)


@dataclass
class PlanStep:
    """Individual step in an execution plan."""
    step_id: str
    name: str
    description: str
    tool_name: str
    parameters: Dict[str, Any]
    
    # Dependencies and ordering
    depends_on: List[str] = field(default_factory=list)
    order: int = 0
    
    # Risk and validation
    risk_assessment: Optional[RiskAssessment] = None
    required_citations: List[Citation] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)
    
    # Execution context
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    requires_approval: bool = False
    can_rollback: bool = True
    
    # Progress tracking
    status: str = "pending"  # pending, running, completed, failed, skipped
    result: Optional[ToolResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Emotional markers for learning
    emotional_markers: List[str] = field(default_factory=list)
    
    def is_ready_to_execute(self, completed_steps: Set[str]) -> bool:
        """Check if step is ready to execute based on dependencies."""
        return all(dep in completed_steps for dep in self.depends_on)
    
    def calculate_execution_time_estimate(self) -> timedelta:
        """Estimate execution time based on tool and complexity."""
        # Simple heuristic - can be enhanced with historical data
        base_time = timedelta(seconds=30)
        
        if self.tool_name.startswith("fs."):
            base_time = timedelta(seconds=10)
        elif self.tool_name.startswith("git."):
            base_time = timedelta(seconds=60)
        elif self.tool_name.startswith("tests."):
            base_time = timedelta(minutes=5)
        
        # Adjust for risk level
        if self.risk_assessment:
            risk_multiplier = 1.0 + (self.risk_assessment.level.value - 1) * 0.2
            base_time = timedelta(seconds=base_time.total_seconds() * risk_multiplier)
        
        return base_time


@dataclass
class Plan:
    """Complete execution plan with steps, dependencies, and metadata."""
    plan_id: str
    name: str
    description: str
    user_id: str
    session_id: str
    
    # Plan composition
    steps: List[PlanStep] = field(default_factory=list)
    total_estimated_time: Optional[timedelta] = None
    
    # Risk and approval
    overall_risk: Optional[RiskAssessment] = None
    requires_approval: bool = False
    approval_reason: str = ""
    
    # Cognition and reasoning
    cognition_trail: Optional[CognitionTrail] = None
    confidence_score: Optional[ConfidenceScore] = None
    
    # Execution tracking
    status: str = "draft"  # draft, approved, executing, completed, failed, cancelled
    progress: float = 0.0  # 0.0 to 1.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def add_step(self, step: PlanStep):
        """Add a step to the plan."""
        step.order = len(self.steps)
        self.steps.append(step)
        self._recalculate_estimates()
    
    def _recalculate_estimates(self):
        """Recalculate time estimates and risk assessments."""
        if not self.steps:
            return
        
        # Calculate total estimated time
        total_seconds = sum(
            step.calculate_execution_time_estimate().total_seconds()
            for step in self.steps
        )
        self.total_estimated_time = timedelta(seconds=total_seconds)
        
        # Calculate overall risk
        if any(step.risk_assessment for step in self.steps):
            max_risk = max(
                (step.risk_assessment.level for step in self.steps if step.risk_assessment),
                default=RiskLevel.MINIMAL
            )
            
            risk_factors = []
            for step in self.steps:
                if step.risk_assessment:
                    risk_factors.extend(step.risk_assessment.factors)
            
            self.overall_risk = RiskAssessment(
                level=max_risk,
                factors=list(set(risk_factors)),
                impact_description=f"Plan contains {len(self.steps)} steps with maximum risk level {max_risk.name}"
            )
            
            self.requires_approval = self.overall_risk.requires_approval()
    
    def get_next_executable_steps(self) -> List[PlanStep]:
        """Get steps that are ready to execute."""
        completed_steps = {
            step.step_id for step in self.steps 
            if step.status == "completed"
        }
        
        return [
            step for step in self.steps
            if step.status == "pending" and step.is_ready_to_execute(completed_steps)
        ]
    
    def calculate_progress(self) -> float:
        """Calculate current progress (0.0 to 1.0)."""
        if not self.steps:
            return 0.0
        
        completed = sum(1 for step in self.steps if step.status == "completed")
        return completed / len(self.steps)
    
    def generate_summary(self) -> str:
        """Generate human-readable plan summary."""
        summary_parts = [
            f"Plan: {self.name}",
            f"Description: {self.description}",
            f"Steps: {len(self.steps)}",
            f"Estimated time: {self.total_estimated_time}"
        ]
        
        if self.overall_risk:
            summary_parts.append(f"Risk level: {self.overall_risk.level.name}")
        
        if self.confidence_score:
            summary_parts.append(
                f"Confidence: {self.confidence_score.confidence_level.name.lower().replace('_', ' ')} "
                f"({self.confidence_score.value:.1%})"
            )
        
        if self.requires_approval:
            summary_parts.append(f"⚠️  Requires approval: {self.approval_reason}")
        
        return "\n".join(summary_parts)


class SoftReasoningEngine:
    """
    Soft reasoning engine implementing human-like probabilistic decision-making
    with confidence scores, uncertainty expression, and multiple solution pathways.
    """
    
    def __init__(self, index_hub: IndexHub, episodic_memory: EpisodicMemoryService):
        self.index_hub = index_hub
        self.episodic_memory = episodic_memory
        self.logger = logging.getLogger(__name__)
        
        # Reasoning configuration
        self.confidence_threshold = 0.5
        self.max_alternatives = 3
        self.evidence_weight_decay = 0.1
        
        # Emotional context tracking
        self.current_emotional_context = EmotionalContext.FOCUSED
        
        # Learning from interactions
        self.interaction_patterns: Dict[str, float] = {}
        self.success_patterns: Dict[str, float] = {}
    
    async def reason_about_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CognitionTrail:
        """
        Perform soft reasoning about a user query with auditable cognition trail.
        
        Args:
            query: User query to reason about
            user_id: User identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            Cognition trail with reasoning steps and confidence scores
        """
        trail_id = str(uuid.uuid4())
        cognition_trail = CognitionTrail(
            trail_id=trail_id,
            user_id=user_id,
            session_id=session_id,
            query=query,
            emotional_context=self.current_emotional_context
        )
        
        try:
            # Step 1: Gather semantic knowledge
            semantic_evidence = await self._gather_semantic_evidence(query, cognition_trail)
            
            # Step 2: Retrieve episodic memories
            episodic_evidence = await self._gather_episodic_evidence(query, user_id, cognition_trail)
            
            # Step 3: Analyze intent and context
            intent_analysis = await self._analyze_intent(query, semantic_evidence, episodic_evidence, cognition_trail)
            
            # Step 4: Generate multiple solution pathways
            solution_pathways = await self._generate_solution_pathways(
                query, intent_analysis, semantic_evidence, episodic_evidence, cognition_trail
            )
            
            # Step 5: Evaluate and rank solutions
            best_solution = await self._evaluate_solutions(solution_pathways, cognition_trail)
            
            # Step 6: Calculate final confidence
            final_confidence = await self._calculate_final_confidence(
                best_solution, semantic_evidence, episodic_evidence, cognition_trail
            )
            
            cognition_trail.final_confidence = final_confidence
            cognition_trail.completed_at = datetime.utcnow()
            
            return cognition_trail
            
        except Exception as e:
            self.logger.error(f"Soft reasoning failed for query '{query}': {e}")
            
            # Add error reasoning step
            error_confidence = ConfidenceScore(
                value=0.1,
                reasoning=f"Reasoning failed due to error: {str(e)}",
                evidence_count=0,
                uncertainty_factors=["system_error", "incomplete_analysis"]
            )
            
            cognition_trail.add_reasoning_step(
                ReasoningType.ABDUCTIVE,
                f"Encountered error while reasoning about: {query}",
                "Unable to complete reasoning due to system limitations",
                [],
                error_confidence
            )
            
            cognition_trail.final_confidence = error_confidence
            cognition_trail.completed_at = datetime.utcnow()
            
            return cognition_trail
    
    async def _gather_semantic_evidence(
        self, 
        query: str, 
        cognition_trail: CognitionTrail
    ) -> List[KnowledgeResult]:
        """Gather semantic evidence from IndexHub."""
        try:
            # Create knowledge query
            knowledge_query = KnowledgeQuery(
                text=query,
                max_results=10,
                min_confidence=0.3,
                require_citations=True
            )
            
            # Query knowledge base
            results = await self.index_hub.query_knowledge(knowledge_query)
            
            # Add reasoning step
            confidence = ConfidenceScore(
                value=min(0.8, len(results) / 10.0 + 0.3),
                reasoning=f"Found {len(results)} relevant knowledge items",
                evidence_count=len(results),
                uncertainty_factors=["knowledge_completeness"] if len(results) < 5 else []
            )
            
            cognition_trail.add_reasoning_step(
                ReasoningType.INDUCTIVE,
                f"Searching knowledge base for information about: {query}",
                f"Retrieved {len(results)} relevant knowledge items with varying confidence levels",
                [citation for result in results for citation in result.citations],
                confidence
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to gather semantic evidence: {e}")
            return []
    
    async def _gather_episodic_evidence(
        self, 
        query: str, 
        user_id: str, 
        cognition_trail: CognitionTrail
    ) -> List[EpisodicMemory]:
        """Gather episodic evidence from conversation history."""
        try:
            # Get recent memories for this user
            # This would typically query the episodic memory service
            # For now, we'll simulate with empty list
            memories = []
            
            # Add reasoning step
            confidence = ConfidenceScore(
                value=0.6 if memories else 0.3,
                reasoning=f"Retrieved {len(memories)} relevant past interactions",
                evidence_count=len(memories),
                uncertainty_factors=["limited_history"] if len(memories) < 3 else []
            )
            
            cognition_trail.add_reasoning_step(
                ReasoningType.ANALOGICAL,
                f"Looking for similar past interactions with user",
                f"Found {len(memories)} relevant conversation memories to inform approach",
                [],  # Episodic memories don't have citations in the same format
                confidence
            )
            
            return memories
            
        except Exception as e:
            self.logger.error(f"Failed to gather episodic evidence: {e}")
            return []
    
    async def _analyze_intent(
        self,
        query: str,
        semantic_evidence: List[KnowledgeResult],
        episodic_evidence: List[EpisodicMemory],
        cognition_trail: CognitionTrail
    ) -> Dict[str, Any]:
        """Analyze user intent from query and evidence."""
        try:
            # Simple intent analysis (can be enhanced with NLP)
            query_lower = query.lower()
            
            intent_indicators = {
                "code_review": ["review", "check", "analyze", "examine"],
                "debug": ["debug", "error", "fix", "problem", "issue"],
                "refactor": ["refactor", "improve", "optimize", "restructure"],
                "generate_tests": ["test", "testing", "coverage", "unit test"],
                "explain": ["explain", "how", "what", "why", "understand"],
                "create": ["create", "make", "build", "generate", "new"]
            }
            
            detected_intents = {}
            for intent, indicators in intent_indicators.items():
                score = sum(1 for indicator in indicators if indicator in query_lower)
                if score > 0:
                    detected_intents[intent] = score / len(indicators)
            
            # Determine primary intent
            primary_intent = max(detected_intents.items(), key=lambda x: x[1]) if detected_intents else ("general_assistance", 0.5)
            
            intent_analysis = {
                "primary_intent": primary_intent[0],
                "confidence": primary_intent[1],
                "all_intents": detected_intents,
                "complexity": self._assess_query_complexity(query, semantic_evidence)
            }
            
            # Add reasoning step
            confidence = ConfidenceScore(
                value=primary_intent[1],
                reasoning=f"Identified primary intent as '{primary_intent[0]}' based on keyword analysis",
                evidence_count=len(detected_intents),
                uncertainty_factors=["simple_keyword_matching"] if primary_intent[1] < 0.7 else []
            )
            
            cognition_trail.add_reasoning_step(
                ReasoningType.DEDUCTIVE,
                f"Analyzing query for intent indicators: {query}",
                f"Primary intent appears to be '{primary_intent[0]}' with {primary_intent[1]:.1%} confidence",
                [],
                confidence
            )
            
            return intent_analysis
            
        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            return {"primary_intent": "general_assistance", "confidence": 0.3, "all_intents": {}, "complexity": "medium"}
    
    def _assess_query_complexity(self, query: str, semantic_evidence: List[KnowledgeResult]) -> str:
        """Assess complexity of the query."""
        # Simple heuristic based on query length and evidence
        word_count = len(query.split())
        evidence_count = len(semantic_evidence)
        
        if word_count > 20 or evidence_count > 8:
            return "high"
        elif word_count > 10 or evidence_count > 4:
            return "medium"
        else:
            return "low"
    
    async def _generate_solution_pathways(
        self,
        query: str,
        intent_analysis: Dict[str, Any],
        semantic_evidence: List[KnowledgeResult],
        episodic_evidence: List[EpisodicMemory],
        cognition_trail: CognitionTrail
    ) -> List[Dict[str, Any]]:
        """Generate multiple solution pathways."""
        try:
            pathways = []
            primary_intent = intent_analysis["primary_intent"]
            
            # Generate pathway based on primary intent
            if primary_intent == "code_review":
                pathways.append({
                    "name": "Comprehensive Code Review",
                    "approach": "systematic_analysis",
                    "tools": ["code.search_spans", "security.scan_secrets", "code.apply_diff"],
                    "confidence": 0.8,
                    "reasoning": "Standard code review workflow with security scanning"
                })
                
                pathways.append({
                    "name": "Quick Code Check",
                    "approach": "focused_analysis", 
                    "tools": ["code.search_spans"],
                    "confidence": 0.6,
                    "reasoning": "Faster approach focusing on specific issues"
                })
            
            elif primary_intent == "debug":
                pathways.append({
                    "name": "Systematic Debugging",
                    "approach": "root_cause_analysis",
                    "tools": ["code.search_spans", "tests.run_subset", "code.apply_diff"],
                    "confidence": 0.7,
                    "reasoning": "Thorough debugging with test validation"
                })
                
                pathways.append({
                    "name": "Quick Fix Attempt",
                    "approach": "pattern_matching",
                    "tools": ["code.search_spans", "code.apply_diff"],
                    "confidence": 0.5,
                    "reasoning": "Faster approach based on common patterns"
                })
            
            elif primary_intent == "refactor":
                pathways.append({
                    "name": "Safe Refactoring",
                    "approach": "test_driven_refactoring",
                    "tools": ["tests.run_subset", "code.search_spans", "code.apply_diff", "tests.run_subset"],
                    "confidence": 0.9,
                    "reasoning": "Test-first approach ensures safety"
                })
            
            else:
                # General assistance pathway
                pathways.append({
                    "name": "Exploratory Analysis",
                    "approach": "information_gathering",
                    "tools": ["code.search_spans", "fs.read_files"],
                    "confidence": 0.6,
                    "reasoning": "General exploration to understand the request"
                })
            
            # Add reasoning step
            confidence = ConfidenceScore(
                value=0.7,
                reasoning=f"Generated {len(pathways)} solution pathways based on intent analysis",
                evidence_count=len(pathways),
                uncertainty_factors=["pathway_generation_heuristics"]
            )
            
            cognition_trail.add_reasoning_step(
                ReasoningType.ABDUCTIVE,
                f"Considering multiple approaches for {primary_intent}",
                f"Generated {len(pathways)} potential solution pathways with different trade-offs",
                [],
                confidence
            )
            
            cognition_trail.alternative_pathways = [p["name"] for p in pathways[1:]]
            
            return pathways
            
        except Exception as e:
            self.logger.error(f"Failed to generate solution pathways: {e}")
            return []
    
    async def _evaluate_solutions(
        self, 
        pathways: List[Dict[str, Any]], 
        cognition_trail: CognitionTrail
    ) -> Optional[Dict[str, Any]]:
        """Evaluate and rank solution pathways."""
        if not pathways:
            return None
        
        try:
            # Score pathways based on multiple criteria
            for pathway in pathways:
                score = 0.0
                
                # Base confidence
                score += pathway.get("confidence", 0.5) * 0.4
                
                # Tool availability (assume all tools are available for now)
                score += 0.3
                
                # Complexity penalty (fewer tools = simpler = better for uncertain cases)
                tool_count = len(pathway.get("tools", []))
                complexity_penalty = min(tool_count / 10.0, 0.3)
                score -= complexity_penalty
                
                # Safety bonus for test-driven approaches
                if "tests.run_subset" in pathway.get("tools", []):
                    score += 0.2
                
                pathway["evaluation_score"] = max(0.0, min(1.0, score))
            
            # Sort by evaluation score
            pathways.sort(key=lambda x: x["evaluation_score"], reverse=True)
            best_pathway = pathways[0]
            
            # Add reasoning step
            confidence = ConfidenceScore(
                value=best_pathway["evaluation_score"],
                reasoning=f"Selected '{best_pathway['name']}' as best approach based on confidence and safety",
                evidence_count=len(pathways),
                uncertainty_factors=["evaluation_heuristics"] if best_pathway["evaluation_score"] < 0.7 else []
            )
            
            cognition_trail.add_reasoning_step(
                ReasoningType.PROBABILISTIC,
                f"Evaluating {len(pathways)} solution pathways",
                f"Selected '{best_pathway['name']}' with evaluation score {best_pathway['evaluation_score']:.2f}",
                [],
                confidence
            )
            
            return best_pathway
            
        except Exception as e:
            self.logger.error(f"Solution evaluation failed: {e}")
            return pathways[0] if pathways else None
    
    async def _calculate_final_confidence(
        self,
        best_solution: Optional[Dict[str, Any]],
        semantic_evidence: List[KnowledgeResult],
        episodic_evidence: List[EpisodicMemory],
        cognition_trail: CognitionTrail
    ) -> ConfidenceScore:
        """Calculate final confidence score for the reasoning process."""
        if not best_solution:
            return ConfidenceScore(
                value=0.1,
                reasoning="No viable solution found",
                evidence_count=0,
                uncertainty_factors=["no_solution_found"]
            )
        
        try:
            # Base confidence from solution
            base_confidence = best_solution.get("evaluation_score", 0.5)
            
            # Evidence quality factor
            evidence_factor = 1.0
            if semantic_evidence:
                avg_semantic_confidence = sum(r.confidence_score for r in semantic_evidence) / len(semantic_evidence)
                evidence_factor *= avg_semantic_confidence
            else:
                evidence_factor *= 0.7  # Penalty for no semantic evidence
            
            # Episodic learning factor
            episodic_factor = 1.0
            if episodic_evidence:
                # Boost confidence if we have successful past interactions
                positive_outcomes = sum(
                    1 for memory in episodic_evidence
                    if memory.interaction_outcome in [InteractionOutcome.SUCCESS, InteractionOutcome.USER_SATISFIED]
                )
                if positive_outcomes > 0:
                    episodic_factor = 1.0 + (positive_outcomes / len(episodic_evidence)) * 0.2
            
            # Calculate final confidence
            final_value = base_confidence * evidence_factor * episodic_factor
            final_value = max(0.0, min(1.0, final_value))
            
            # Determine uncertainty factors
            uncertainty_factors = []
            if len(semantic_evidence) < 3:
                uncertainty_factors.append("limited_knowledge_base")
            if len(episodic_evidence) < 2:
                uncertainty_factors.append("limited_interaction_history")
            if final_value < 0.6:
                uncertainty_factors.append("low_solution_confidence")
            
            return ConfidenceScore(
                value=final_value,
                reasoning=f"Combined solution confidence ({base_confidence:.2f}) with evidence quality ({evidence_factor:.2f}) and past experience ({episodic_factor:.2f})",
                evidence_count=len(semantic_evidence) + len(episodic_evidence),
                uncertainty_factors=uncertainty_factors
            )
            
        except Exception as e:
            self.logger.error(f"Final confidence calculation failed: {e}")
            return ConfidenceScore(
                value=0.3,
                reasoning=f"Confidence calculation failed: {str(e)}",
                evidence_count=0,
                uncertainty_factors=["calculation_error"]
            )
    
    def update_emotional_context(self, context: EmotionalContext):
        """Update current emotional context for reasoning."""
        self.current_emotional_context = context
        self.logger.info(f"Updated emotional context to: {context.value}")
    
    async def learn_from_outcome(
        self,
        cognition_trail: CognitionTrail,
        outcome: InteractionOutcome,
        user_feedback: Optional[str] = None
    ):
        """Learn from interaction outcomes to improve future reasoning."""
        try:
            # Update success patterns based on outcome
            if outcome in [InteractionOutcome.SUCCESS, InteractionOutcome.USER_SATISFIED]:
                # Reinforce successful reasoning patterns
                for step in cognition_trail.reasoning_steps:
                    pattern_key = f"{step.reasoning_type.value}_{step.confidence.confidence_level.name}"
                    self.success_patterns[pattern_key] = self.success_patterns.get(pattern_key, 0.5) + 0.1
            
            elif outcome in [InteractionOutcome.FAILURE, InteractionOutcome.USER_FRUSTRATED]:
                # Reduce confidence in failed patterns
                for step in cognition_trail.reasoning_steps:
                    pattern_key = f"{step.reasoning_type.value}_{step.confidence.confidence_level.name}"
                    self.success_patterns[pattern_key] = max(0.1, self.success_patterns.get(pattern_key, 0.5) - 0.1)
            
            # Update interaction patterns
            if user_feedback:
                feedback_lower = user_feedback.lower()
                if any(word in feedback_lower for word in ["good", "helpful", "thanks"]):
                    self.interaction_patterns["positive_feedback"] = self.interaction_patterns.get("positive_feedback", 0.5) + 0.1
                elif any(word in feedback_lower for word in ["bad", "wrong", "unhelpful"]):
                    self.interaction_patterns["negative_feedback"] = self.interaction_patterns.get("negative_feedback", 0.5) + 0.1
            
            self.logger.info(f"Updated reasoning patterns based on outcome: {outcome.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn from outcome: {e}")


class AgentPlanner:
    """
    Main agent planner that composes tools based on IndexHub context and capabilities,
    implementing human-like cognitive architecture with soft reasoning and emotional awareness.
    """
    
    def __init__(
        self,
        index_hub: IndexHub,
        episodic_memory: EpisodicMemoryService,
        working_memory: WorkingMemoryService,
        tool_registry: CopilotToolRegistry,
        tool_service: CopilotToolService
    ):
        self.index_hub = index_hub
        self.episodic_memory = episodic_memory
        self.working_memory = working_memory
        self.tool_registry = tool_registry
        self.tool_service = tool_service
        
        # Initialize soft reasoning engine
        self.reasoning_engine = SoftReasoningEngine(index_hub, episodic_memory)
        
        self.logger = logging.getLogger(__name__)
        
        # Planning configuration
        self.max_plan_steps = 20
        self.default_citation_requirement = 2
        self.enable_emotional_markers = True
        
        # Active plans tracking
        self.active_plans: Dict[str, Plan] = {}
        self.plan_history: Dict[str, List[str]] = {}  # user_id -> plan_ids
    
    async def create_plan(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    ) -> Plan:
        """
        Create an execution plan based on user query with human-like reasoning.
        
        Args:
            query: User query or request
            user_id: User identifier
            session_id: Session identifier
            context: Additional context information
            execution_mode: Default execution mode for plan steps
            
        Returns:
            Generated execution plan with reasoning trail
        """
        plan_id = str(uuid.uuid4())
        
        try:
            # Step 1: Perform soft reasoning about the query
            cognition_trail = await self.reasoning_engine.reason_about_query(
                query, user_id, session_id, context
            )
            
            # Step 2: Extract plan requirements from reasoning
            plan_requirements = await self._extract_plan_requirements(cognition_trail, context)
            
            # Step 3: Compose tool chain based on requirements
            tool_chain = await self._compose_tool_chain(plan_requirements, cognition_trail)
            
            # Step 4: Create plan steps with risk assessment
            plan_steps = await self._create_plan_steps(tool_chain, execution_mode, cognition_trail)
            
            # Step 5: Validate plan and citations
            validation_result = await self._validate_plan(plan_steps, cognition_trail)
            
            # Step 6: Create final plan
            plan = Plan(
                plan_id=plan_id,
                name=self._generate_plan_name(query, plan_requirements),
                description=self._generate_plan_description(query, cognition_trail),
                user_id=user_id,
                session_id=session_id,
                cognition_trail=cognition_trail,
                confidence_score=cognition_trail.final_confidence
            )
            
            # Add validated steps
            for step in plan_steps:
                plan.add_step(step)
            
            # Set approval requirements
            if validation_result["requires_approval"]:
                plan.requires_approval = True
                plan.approval_reason = validation_result["approval_reason"]
            
            # Track plan
            self.active_plans[plan_id] = plan
            if user_id not in self.plan_history:
                self.plan_history[user_id] = []
            self.plan_history[user_id].append(plan_id)
            
            self.logger.info(f"Created plan {plan_id} for user {user_id}: {plan.name}")
            return plan
            
        except Exception as e:
            self.logger.error(f"Plan creation failed for query '{query}': {e}")
            
            # Create minimal error plan
            error_plan = Plan(
                plan_id=plan_id,
                name="Error Plan",
                description=f"Plan creation failed: {str(e)}",
                user_id=user_id,
                session_id=session_id,
                status="failed"
            )
            
            return error_plan
    
    async def _extract_plan_requirements(
        self, 
        cognition_trail: CognitionTrail, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract plan requirements from cognition trail."""
        try:
            requirements = {
                "primary_intent": "general_assistance",
                "target_files": [],
                "required_capabilities": [],
                "privacy_level": PrivacyLevel.INTERNAL,
                "max_risk_level": RiskLevel.MEDIUM,
                "citation_requirement": self.default_citation_requirement
            }
            
            # Extract from reasoning steps
            for step in cognition_trail.reasoning_steps:
                if "code_review" in step.conclusion.lower():
                    requirements["required_capabilities"].append("copilot.review")
                elif "debug" in step.conclusion.lower():
                    requirements["required_capabilities"].append("copilot.debug")
                elif "refactor" in step.conclusion.lower():
                    requirements["required_capabilities"].append("copilot.refactor")
                    requirements["privacy_level"] = PrivacyLevel.CONFIDENTIAL  # Refactoring is sensitive
                elif "test" in step.conclusion.lower():
                    requirements["required_capabilities"].append("copilot.generate_tests")
            
            # Extract from context
            if context:
                requirements["target_files"] = context.get("selected_files", [])
                if context.get("privacy_sensitive"):
                    requirements["privacy_level"] = PrivacyLevel.CONFIDENTIAL
                if context.get("high_risk_operation"):
                    requirements["max_risk_level"] = RiskLevel.HIGH
            
            return requirements
            
        except Exception as e:
            self.logger.error(f"Failed to extract plan requirements: {e}")
            return {"primary_intent": "general_assistance", "required_capabilities": []}
    
    async def _compose_tool_chain(
        self, 
        requirements: Dict[str, Any], 
        cognition_trail: CognitionTrail
    ) -> List[Dict[str, Any]]:
        """Compose tool chain based on requirements."""
        try:
            tool_chain = []
            capabilities = requirements.get("required_capabilities", [])
            
            # Standard patterns for different capabilities
            if "copilot.review" in capabilities:
                tool_chain.extend([
                    {"tool": "code.search_spans", "purpose": "locate_code_elements"},
                    {"tool": "security.scan_secrets", "purpose": "security_check"},
                    {"tool": "code.apply_diff", "purpose": "apply_suggestions"}
                ])
            
            elif "copilot.debug" in capabilities:
                tool_chain.extend([
                    {"tool": "code.search_spans", "purpose": "find_error_location"},
                    {"tool": "tests.run_subset", "purpose": "validate_current_state"},
                    {"tool": "code.apply_diff", "purpose": "apply_fix"},
                    {"tool": "tests.run_subset", "purpose": "validate_fix"}
                ])
            
            elif "copilot.refactor" in capabilities:
                tool_chain.extend([
                    {"tool": "tests.run_subset", "purpose": "baseline_tests"},
                    {"tool": "code.search_spans", "purpose": "analyze_structure"},
                    {"tool": "code.apply_diff", "purpose": "refactor_code"},
                    {"tool": "tests.run_subset", "purpose": "verify_refactoring"}
                ])
            
            elif "copilot.generate_tests" in capabilities:
                tool_chain.extend([
                    {"tool": "code.search_spans", "purpose": "analyze_code_coverage"},
                    {"tool": "code.apply_diff", "purpose": "generate_tests"},
                    {"tool": "tests.run_subset", "purpose": "validate_tests"}
                ])
            
            else:
                # General exploration
                tool_chain.extend([
                    {"tool": "fs.read_files", "purpose": "gather_information"},
                    {"tool": "code.search_spans", "purpose": "analyze_code"}
                ])
            
            # Add git operations if needed
            if requirements.get("target_files"):
                tool_chain.append({"tool": "git.open_pr", "purpose": "create_pull_request"})
            
            return tool_chain
            
        except Exception as e:
            self.logger.error(f"Tool chain composition failed: {e}")
            return [{"tool": "fs.read_files", "purpose": "basic_exploration"}]
    
    async def _create_plan_steps(
        self, 
        tool_chain: List[Dict[str, Any]], 
        execution_mode: ExecutionMode,
        cognition_trail: CognitionTrail
    ) -> List[PlanStep]:
        """Create plan steps from tool chain."""
        try:
            steps = []
            
            for i, tool_info in enumerate(tool_chain):
                step_id = str(uuid.uuid4())
                tool_name = tool_info["tool"]
                purpose = tool_info["purpose"]
                
                # Assess risk for this step
                risk_assessment = await self._assess_step_risk(tool_name, purpose)
                
                # Determine dependencies
                depends_on = []
                if i > 0:
                    depends_on = [steps[i-1].step_id]
                
                # Create step
                step = PlanStep(
                    step_id=step_id,
                    name=f"{purpose.replace('_', ' ').title()}",
                    description=f"Execute {tool_name} to {purpose.replace('_', ' ')}",
                    tool_name=tool_name,
                    parameters={},  # Will be populated during execution
                    depends_on=depends_on,
                    order=i,
                    risk_assessment=risk_assessment,
                    execution_mode=execution_mode,
                    requires_approval=risk_assessment.requires_approval() if risk_assessment else False,
                    can_rollback=tool_name.startswith(("code.", "fs.", "git."))
                )
                
                # Add emotional markers based on reasoning
                if cognition_trail.emotional_context == EmotionalContext.CAUTIOUS:
                    step.emotional_markers.append("cautious_approach")
                elif cognition_trail.emotional_context == EmotionalContext.CONFIDENT:
                    step.emotional_markers.append("confident_execution")
                
                steps.append(step)
            
            return steps
            
        except Exception as e:
            self.logger.error(f"Plan step creation failed: {e}")
            return []
    
    async def _assess_step_risk(self, tool_name: str, purpose: str) -> RiskAssessment:
        """Assess risk for a plan step."""
        try:
            # Base risk levels by tool type
            tool_risks = {
                "fs.read_files": RiskLevel.MINIMAL,
                "code.search_spans": RiskLevel.MINIMAL,
                "code.apply_diff": RiskLevel.HIGH,
                "tests.run_subset": RiskLevel.LOW,
                "git.open_pr": RiskLevel.MEDIUM,
                "security.scan_secrets": RiskLevel.LOW,
                "fs.write_files": RiskLevel.HIGH,
                "db.query_safe": RiskLevel.MEDIUM
            }
            
            base_risk = tool_risks.get(tool_name, RiskLevel.MEDIUM)
            
            # Risk factors
            factors = []
            if "write" in tool_name or "apply" in tool_name:
                factors.append("modifies_files")
            if "git" in tool_name:
                factors.append("version_control_operation")
            if purpose in ["refactor_code", "apply_fix"]:
                factors.append("code_modification")
            
            # Mitigation strategies
            mitigations = []
            if base_risk.value >= RiskLevel.HIGH.value:
                mitigations.extend(["dry_run_first", "backup_creation", "rollback_capability"])
            if "code" in tool_name:
                mitigations.append("syntax_validation")
            if "test" in tool_name:
                mitigations.append("test_isolation")
            
            return RiskAssessment(
                level=base_risk,
                factors=factors,
                mitigation_strategies=mitigations,
                impact_description=f"Risk level {base_risk.name} for {tool_name} operation",
                probability=0.3 if base_risk.value <= RiskLevel.LOW.value else 0.6
            )
            
        except Exception as e:
            self.logger.error(f"Risk assessment failed for {tool_name}: {e}")
            return RiskAssessment(
                level=RiskLevel.MEDIUM,
                factors=["assessment_error"],
                impact_description=f"Could not assess risk for {tool_name}"
            )
    
    async def _validate_plan(
        self, 
        steps: List[PlanStep], 
        cognition_trail: CognitionTrail
    ) -> Dict[str, Any]:
        """Validate plan and determine approval requirements."""
        try:
            validation_result = {
                "valid": True,
                "requires_approval": False,
                "approval_reason": "",
                "issues": []
            }
            
            # Check for high-risk operations
            high_risk_steps = [
                step for step in steps 
                if step.risk_assessment and step.risk_assessment.level.value >= RiskLevel.HIGH.value
            ]
            
            if high_risk_steps:
                validation_result["requires_approval"] = True
                validation_result["approval_reason"] = f"Plan contains {len(high_risk_steps)} high-risk operations"
            
            # Check citation requirements for write operations
            write_steps = [
                step for step in steps
                if step.tool_name.startswith(("code.apply", "fs.write", "git."))
            ]
            
            insufficient_citations = []
            for step in write_steps:
                if len(step.required_citations) < self.default_citation_requirement:
                    insufficient_citations.append(step.name)
            
            if insufficient_citations:
                validation_result["issues"].append(
                    f"Steps with insufficient citations: {', '.join(insufficient_citations)}"
                )
            
            # Check confidence level
            if cognition_trail.final_confidence and cognition_trail.final_confidence.value < 0.5:
                validation_result["requires_approval"] = True
                if validation_result["approval_reason"]:
                    validation_result["approval_reason"] += "; Low confidence in plan"
                else:
                    validation_result["approval_reason"] = "Low confidence in plan"
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Plan validation failed: {e}")
            return {
                "valid": False,
                "requires_approval": True,
                "approval_reason": f"Validation failed: {str(e)}",
                "issues": ["validation_error"]
            }
    
    def _generate_plan_name(self, query: str, requirements: Dict[str, Any]) -> str:
        """Generate a human-readable plan name."""
        capabilities = requirements.get("required_capabilities", [])
        
        if "copilot.review" in capabilities:
            return f"Code Review: {query[:50]}..."
        elif "copilot.debug" in capabilities:
            return f"Debug Session: {query[:50]}..."
        elif "copilot.refactor" in capabilities:
            return f"Refactoring: {query[:50]}..."
        elif "copilot.generate_tests" in capabilities:
            return f"Test Generation: {query[:50]}..."
        else:
            return f"Analysis: {query[:50]}..."
    
    def _generate_plan_description(self, query: str, cognition_trail: CognitionTrail) -> str:
        """Generate a detailed plan description."""
        description_parts = [
            f"Plan generated for query: {query}",
            f"Primary reasoning approach: {cognition_trail.emotional_context.value}",
        ]
        
        if cognition_trail.final_confidence:
            description_parts.append(
                f"Confidence level: {cognition_trail.final_confidence.confidence_level.name.lower().replace('_', ' ')}"
            )
        
        if cognition_trail.alternative_pathways:
            description_parts.append(
                f"Alternative approaches considered: {', '.join(cognition_trail.alternative_pathways[:2])}"
            )
        
        return "\n".join(description_parts)
    
    async def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Get a plan by ID."""
        return self.active_plans.get(plan_id)
    
    async def get_user_plans(self, user_id: str) -> List[Plan]:
        """Get all plans for a user."""
        plan_ids = self.plan_history.get(user_id, [])
        return [
            plan for plan_id in plan_ids
            if (plan := self.active_plans.get(plan_id))
        ]
    
    async def update_plan_status(self, plan_id: str, status: str) -> bool:
        """Update plan status."""
        if plan_id in self.active_plans:
            self.active_plans[plan_id].status = status
            if status == "completed":
                self.active_plans[plan_id].completed_at = datetime.utcnow()
            elif status == "executing":
                self.active_plans[plan_id].started_at = datetime.utcnow()
            return True
        return False
    
    async def learn_from_plan_outcome(
        self,
        plan_id: str,
        outcome: InteractionOutcome,
        user_feedback: Optional[str] = None
    ):
        """Learn from plan execution outcomes."""
        plan = self.active_plans.get(plan_id)
        if not plan or not plan.cognition_trail:
            return
        
        try:
            # Update reasoning engine with outcome
            await self.reasoning_engine.learn_from_outcome(
                plan.cognition_trail, outcome, user_feedback
            )
            
            # Store episodic memory of this plan execution
            await self.episodic_memory.store_episodic_memory(
                conversation_id=plan.session_id,
                user_id=plan.user_id,
                content=f"Executed plan: {plan.name}",
                context_summary=plan.description,
                interaction_type="plan_execution",
                session_id=plan.session_id,
                user_feedback=user_feedback,
                success_indicators=["plan_completed"] if outcome == InteractionOutcome.SUCCESS else [],
                failure_indicators=["plan_failed"] if outcome == InteractionOutcome.FAILURE else [],
                importance=ContextImportance.HIGH,
                tags=["copilot", "plan_execution"],
                metadata={
                    "plan_id": plan_id,
                    "step_count": len(plan.steps),
                    "execution_time": str(plan.total_estimated_time),
                    "confidence": plan.confidence_score.value if plan.confidence_score else None
                }
            )
            
            self.logger.info(f"Learned from plan {plan_id} outcome: {outcome.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn from plan outcome: {e}")