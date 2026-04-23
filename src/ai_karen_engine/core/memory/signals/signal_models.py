"""
Signal Models for AI Karen Memory System.

Defines schemas for normalized memory signals.
"""

from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class MemorySignal:
    """Normalized output from extraction."""
    text: str
    signal_type: str  # e.g., 'preference', 'entity', 'directive', 'workflow'
    confidence: float
    entities: List[Dict[str, str]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    scope: str = "user"
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ExtractionResult:
    """Result of the extraction pipeline."""
    signals: List[MemorySignal] = field(default_factory=list)
    processing_time_ms: float = 0.0
    status: str = "success"  # 'success', 'degraded', 'failed'
    errors: List[str] = field(default_factory=list)
