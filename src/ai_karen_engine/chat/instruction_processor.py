"""
Enhanced instruction processing for ChatOrchestrator.

This module provides sophisticated prompt parsing, instruction extraction,
and instruction persistence across conversation turns.
"""

from __future__ import annotations

import logging
import re
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

logger = logging.getLogger(__name__)


class InstructionType(str, Enum):
    """Types of instructions that can be extracted from user messages."""
    TASK = "task"
    PREFERENCE = "preference"
    CONSTRAINT = "constraint"
    FORMAT = "format"
    STYLE = "style"
    BEHAVIOR = "behavior"
    CONTEXT = "context"
    CORRECTION = "correction"


class InstructionPriority(str, Enum):
    """Priority levels for instructions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InstructionScope(str, Enum):
    """Scope of instruction application."""
    CURRENT_MESSAGE = "current_message"
    CONVERSATION = "conversation"
    SESSION = "session"
    GLOBAL = "global"


@dataclass
class ExtractedInstruction:
    """Represents an instruction extracted from user input."""
    id: str
    type: InstructionType
    content: str
    priority: InstructionPriority
    scope: InstructionScope
    confidence: float
    extracted_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if the instruction has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "priority": self.priority.value,
            "scope": self.scope.value,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractedInstruction':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=InstructionType(data["type"]),
            content=data["content"],
            priority=InstructionPriority(data["priority"]),
            scope=InstructionScope(data["scope"]),
            confidence=data["confidence"],
            extracted_at=datetime.fromisoformat(data["extracted_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            metadata=data.get("metadata", {})
        )


@dataclass
class InstructionContext:
    """Context for instruction processing."""
    user_id: str
    conversation_id: str
    session_id: Optional[str] = None
    message_history: List[str] = field(default_factory=list)
    active_instructions: List[ExtractedInstruction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class InstructionProcessor:
    """
    Enhanced instruction processor for extracting and managing user instructions.
    
    Features:
    - Pattern-based instruction extraction
    - Instruction priority and scope management
    - Instruction persistence across conversation turns
    - Context-aware instruction application
    """
    
    def __init__(self):
        self.instruction_patterns = self._initialize_patterns()
        self.instruction_memory: Dict[str, List[ExtractedInstruction]] = {}
        logger.info("InstructionProcessor initialized")
    
    def _initialize_patterns(self) -> Dict[InstructionType, List[Dict[str, Any]]]:
        """Initialize instruction extraction patterns."""
        return {
            InstructionType.TASK: [
                {
                    "pattern": r"(?:please\s+)?(?:can you\s+|could you\s+|would you\s+)?([^.!?]+)(?:\.|!|\?|$)",
                    "priority": InstructionPriority.HIGH,
                    "scope": InstructionScope.CURRENT_MESSAGE,
                    "confidence": 0.8
                },
                {
                    "pattern": r"(?:i need you to|i want you to|you should|you must)\s+([^.!?]+)",
                    "priority": InstructionPriority.HIGH,
                    "scope": InstructionScope.CONVERSATION,
                    "confidence": 0.9
                }
            ],
            InstructionType.PREFERENCE: [
                {
                    "pattern": r"(?:i prefer|i like|i want|i'd like)\s+([^.!?]+)",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.SESSION,
                    "confidence": 0.7
                },
                {
                    "pattern": r"(?:always|from now on|going forward)\s+([^.!?]+)",
                    "priority": InstructionPriority.HIGH,
                    "scope": InstructionScope.GLOBAL,
                    "confidence": 0.8
                }
            ],
            InstructionType.CONSTRAINT: [
                {
                    "pattern": r"(?:don't|do not|never|avoid)\s+([^.!?]+)",
                    "priority": InstructionPriority.HIGH,
                    "scope": InstructionScope.CONVERSATION,
                    "confidence": 0.8
                },
                {
                    "pattern": r"(?:make sure|ensure that|be sure to)\s+([^.!?]+)",
                    "priority": InstructionPriority.HIGH,
                    "scope": InstructionScope.CURRENT_MESSAGE,
                    "confidence": 0.7
                }
            ],
            InstructionType.FORMAT: [
                {
                    "pattern": r"(?:format|structure|organize)\s+(?:this|the response|your answer|it)\s+(?:as|in|using)\s+([^.!?]+)",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.CURRENT_MESSAGE,
                    "confidence": 0.8
                },
                {
                    "pattern": r"(?:use|write in|respond in)\s+([^.!?]+)\s+format",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.CURRENT_MESSAGE,
                    "confidence": 0.7
                },
                {
                    "pattern": r"format\s+(?:your\s+)?(?:response|answer)\s+as\s+(?:a\s+)?([^.!?]+)",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.CURRENT_MESSAGE,
                    "confidence": 0.8
                }
            ],
            InstructionType.STYLE: [
                {
                    "pattern": r"(?:be|sound|write)\s+(more\s+)?(?:formal|informal|casual|professional|friendly|concise|detailed|technical|simple)\s*",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.SESSION,
                    "confidence": 0.7
                },
                {
                    "pattern": r"(?:use a|adopt a|take a)\s+([^.!?]+)\s+(?:tone|style|approach)",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.SESSION,
                    "confidence": 0.6
                }
            ],
            InstructionType.BEHAVIOR: [
                {
                    "pattern": r"(?:act like|behave like|pretend to be|you are)\s+([^.!?]+)",
                    "priority": InstructionPriority.HIGH,
                    "scope": InstructionScope.CONVERSATION,
                    "confidence": 0.8
                },
                {
                    "pattern": r"(?:remember|keep in mind|note that)\s+([^.!?]+)",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.SESSION,
                    "confidence": 0.7
                }
            ],
            InstructionType.CONTEXT: [
                {
                    "pattern": r"(?:given that|considering that|assuming that)\s+([^.!?]+)",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.CURRENT_MESSAGE,
                    "confidence": 0.6
                },
                {
                    "pattern": r"(?:in the context of|for the purpose of)\s+([^.!?]+)",
                    "priority": InstructionPriority.MEDIUM,
                    "scope": InstructionScope.CONVERSATION,
                    "confidence": 0.7
                }
            ],
            InstructionType.CORRECTION: [
                {
                    "pattern": r"(?:actually|correction|i meant|let me clarify)\s*[,:]\s*([^.!?]+)",
                    "priority": InstructionPriority.HIGH,
                    "scope": InstructionScope.CURRENT_MESSAGE,
                    "confidence": 0.9
                },
                {
                    "pattern": r"(?:that's wrong|that's incorrect|no,)\s+([^.!?]+)",
                    "priority": InstructionPriority.HIGH,
                    "scope": InstructionScope.CURRENT_MESSAGE,
                    "confidence": 0.8
                }
            ]
        }
    
    async def extract_instructions(
        self,
        message: str,
        context: InstructionContext
    ) -> List[ExtractedInstruction]:
        """
        Extract instructions from a user message.
        
        Args:
            message: User message to analyze
            context: Instruction processing context
            
        Returns:
            List of extracted instructions
        """
        instructions = []
        message_lower = message.lower().strip()
        
        # Skip empty messages
        if not message_lower:
            return instructions
        
        # Extract instructions using patterns
        for instruction_type, patterns in self.instruction_patterns.items():
            for pattern_config in patterns:
                pattern = pattern_config["pattern"]
                matches = re.finditer(pattern, message_lower, re.IGNORECASE)
                
                for match in matches:
                    instruction_content = match.group(1).strip()
                    
                    # Skip very short or generic instructions
                    if len(instruction_content) < 3:
                        continue
                    
                    # Create instruction
                    instruction = ExtractedInstruction(
                        id=f"{instruction_type.value}_{len(instructions)}_{hash(instruction_content) % 10000}",
                        type=instruction_type,
                        content=instruction_content,
                        priority=pattern_config["priority"],
                        scope=pattern_config["scope"],
                        confidence=pattern_config["confidence"],
                        extracted_at=datetime.utcnow(),
                        expires_at=self._calculate_expiry(pattern_config["scope"]),
                        metadata={
                            "original_message": message,
                            "pattern_matched": pattern,
                            "user_id": context.user_id,
                            "conversation_id": context.conversation_id
                        }
                    )
                    
                    instructions.append(instruction)
        
        # Post-process instructions
        instructions = self._post_process_instructions(instructions, message, context)
        
        logger.debug(f"Extracted {len(instructions)} instructions from message")
        return instructions
    
    def _calculate_expiry(self, scope: InstructionScope) -> Optional[datetime]:
        """Calculate expiry time based on instruction scope."""
        now = datetime.utcnow()
        
        if scope == InstructionScope.CURRENT_MESSAGE:
            return now + timedelta(minutes=5)  # Very short-lived
        elif scope == InstructionScope.CONVERSATION:
            return now + timedelta(hours=2)  # Conversation-scoped
        elif scope == InstructionScope.SESSION:
            return now + timedelta(hours=24)  # Session-scoped
        else:  # GLOBAL
            return None  # No expiry
    
    def _post_process_instructions(
        self,
        instructions: List[ExtractedInstruction],
        message: str,
        context: InstructionContext
    ) -> List[ExtractedInstruction]:
        """Post-process extracted instructions for quality and relevance."""
        processed = []
        
        for instruction in instructions:
            # Skip duplicate instructions
            if self._is_duplicate_instruction(instruction, processed):
                continue
            
            # Adjust confidence based on context
            instruction.confidence = self._adjust_confidence(instruction, message, context)
            
            # Skip low-confidence instructions
            if instruction.confidence < 0.3:
                continue
            
            processed.append(instruction)
        
        # Sort by priority and confidence
        processed.sort(key=lambda x: (x.priority.value, -x.confidence))
        
        return processed
    
    def _is_duplicate_instruction(
        self,
        instruction: ExtractedInstruction,
        existing: List[ExtractedInstruction]
    ) -> bool:
        """Check if instruction is a duplicate of existing ones."""
        for existing_instruction in existing:
            if (instruction.type == existing_instruction.type and
                instruction.content.lower() == existing_instruction.content.lower()):
                return True
        return False
    
    def _adjust_confidence(
        self,
        instruction: ExtractedInstruction,
        message: str,
        context: InstructionContext
    ) -> float:
        """Adjust instruction confidence based on context and message characteristics."""
        confidence = instruction.confidence
        
        # Boost confidence for explicit instruction words
        explicit_words = ["please", "must", "should", "always", "never", "make sure"]
        if any(word in message.lower() for word in explicit_words):
            confidence += 0.1
        
        # Boost confidence for imperative sentences
        if message.strip().endswith("!"):
            confidence += 0.1
        
        # Reduce confidence for questions
        if message.strip().endswith("?"):
            confidence -= 0.1
        
        # Boost confidence for repeated instructions
        if self._is_repeated_instruction(instruction, context):
            confidence += 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _is_repeated_instruction(
        self,
        instruction: ExtractedInstruction,
        context: InstructionContext
    ) -> bool:
        """Check if this instruction has been given before."""
        for active_instruction in context.active_instructions:
            if (instruction.type == active_instruction.type and
                instruction.content.lower() in active_instruction.content.lower()):
                return True
        return False
    
    async def store_instructions(
        self,
        instructions: List[ExtractedInstruction],
        context: InstructionContext
    ) -> None:
        """Store instructions in memory for persistence."""
        key = f"{context.user_id}:{context.conversation_id}"
        
        if key not in self.instruction_memory:
            self.instruction_memory[key] = []
        
        # Add new instructions
        self.instruction_memory[key].extend(instructions)
        
        # Clean up expired instructions
        self.instruction_memory[key] = [
            inst for inst in self.instruction_memory[key]
            if not inst.is_expired()
        ]
        
        # Limit memory size (keep most recent 50 instructions)
        if len(self.instruction_memory[key]) > 50:
            self.instruction_memory[key] = self.instruction_memory[key][-50:]
        
        logger.debug(f"Stored {len(instructions)} instructions for {key}")
    
    async def get_active_instructions(
        self,
        context: InstructionContext,
        scope_filter: Optional[Set[InstructionScope]] = None
    ) -> List[ExtractedInstruction]:
        """Get active instructions for the given context."""
        key = f"{context.user_id}:{context.conversation_id}"
        
        if key not in self.instruction_memory:
            return []
        
        active_instructions = []
        
        for instruction in self.instruction_memory[key]:
            # Skip expired instructions
            if instruction.is_expired():
                continue
            
            # Apply scope filter
            if scope_filter and instruction.scope not in scope_filter:
                continue
            
            active_instructions.append(instruction)
        
        # Sort by priority and recency
        active_instructions.sort(
            key=lambda x: (x.priority.value, -x.extracted_at.timestamp())
        )
        
        return active_instructions
    
    async def apply_instructions_to_prompt(
        self,
        base_prompt: str,
        instructions: List[ExtractedInstruction],
        context: InstructionContext
    ) -> str:
        """Apply active instructions to enhance the base prompt."""
        if not instructions:
            return base_prompt
        
        # Group instructions by type
        instruction_groups = {}
        for instruction in instructions:
            if instruction.type not in instruction_groups:
                instruction_groups[instruction.type] = []
            instruction_groups[instruction.type].append(instruction)
        
        # Build instruction context
        instruction_context = []
        
        # Add high-priority instructions first
        high_priority = [inst for inst in instructions if inst.priority == InstructionPriority.HIGH]
        if high_priority:
            instruction_context.append("IMPORTANT INSTRUCTIONS:")
            for inst in high_priority[:3]:  # Limit to top 3
                instruction_context.append(f"- {inst.content}")
        
        # Add preferences and constraints
        preferences = instruction_groups.get(InstructionType.PREFERENCE, [])
        constraints = instruction_groups.get(InstructionType.CONSTRAINT, [])
        
        if preferences:
            instruction_context.append("\nUSER PREFERENCES:")
            for pref in preferences[:2]:  # Limit to top 2
                instruction_context.append(f"- {pref.content}")
        
        if constraints:
            instruction_context.append("\nCONSTRAINTS:")
            for constraint in constraints[:2]:  # Limit to top 2
                instruction_context.append(f"- {constraint.content}")
        
        # Add style and format instructions
        style_instructions = instruction_groups.get(InstructionType.STYLE, [])
        format_instructions = instruction_groups.get(InstructionType.FORMAT, [])
        
        if style_instructions or format_instructions:
            instruction_context.append("\nSTYLE & FORMAT:")
            for inst in (style_instructions + format_instructions)[:2]:
                instruction_context.append(f"- {inst.content}")
        
        # Combine with base prompt
        if instruction_context:
            enhanced_prompt = "\n".join(instruction_context) + "\n\n" + base_prompt
        else:
            enhanced_prompt = base_prompt
        
        return enhanced_prompt
    
    def get_instruction_summary(
        self,
        context: InstructionContext
    ) -> Dict[str, Any]:
        """Get a summary of active instructions for the context."""
        key = f"{context.user_id}:{context.conversation_id}"
        
        if key not in self.instruction_memory:
            return {"total": 0, "by_type": {}, "by_priority": {}}
        
        instructions = [inst for inst in self.instruction_memory[key] if not inst.is_expired()]
        
        by_type = {}
        by_priority = {}
        
        for instruction in instructions:
            # Count by type
            type_key = instruction.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # Count by priority
            priority_key = instruction.priority.value
            by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
        
        return {
            "total": len(instructions),
            "by_type": by_type,
            "by_priority": by_priority,
            "most_recent": instructions[-1].to_dict() if instructions else None
        }
    
    def clear_instructions(
        self,
        context: InstructionContext,
        instruction_type: Optional[InstructionType] = None
    ) -> int:
        """Clear instructions for the given context."""
        key = f"{context.user_id}:{context.conversation_id}"
        
        if key not in self.instruction_memory:
            return 0
        
        original_count = len(self.instruction_memory[key])
        
        if instruction_type:
            # Clear specific type
            self.instruction_memory[key] = [
                inst for inst in self.instruction_memory[key]
                if inst.type != instruction_type
            ]
        else:
            # Clear all
            self.instruction_memory[key] = []
        
        cleared_count = original_count - len(self.instruction_memory[key])
        logger.info(f"Cleared {cleared_count} instructions for {key}")
        
        return cleared_count