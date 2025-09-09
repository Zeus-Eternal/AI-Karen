"""
Recall Types for AI-Karen
Data structures for the recalls system
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

@dataclass
class RecallEntry:
    """
    A single recall entry containing question-plan pairs with metadata
    """
    question: str
    plan: str
    reward: float = 0.0
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    line_index: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            'question': self.question,
            'plan': self.plan,
            'reward': self.reward
        }
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        if self.metadata:
            result['metadata'] = self.metadata
        if self.line_index is not None:
            result['line_index'] = self.line_index
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecallEntry':
        """Create from dictionary format"""
        timestamp = None
        if 'timestamp' in data:
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls(
            question=data['question'],
            plan=data['plan'],
            reward=data.get('reward', 0.0),
            timestamp=timestamp,
            metadata=data.get('metadata'),
            line_index=data.get('line_index')
        )

@dataclass
class RecallQuery:
    """
    Query parameters for recall retrieval
    """
    task: str
    top_k: int = 5
    max_length: int = 256
    min_score: float = 0.0
    device: str = "auto"
    
@dataclass 
class RecallResult:
    """
    Result from recall retrieval
    """
    rank: int
    score: float
    question: str
    plan: str
    line_index: int
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            'rank': self.rank,
            'score': self.score,
            'question': self.question,
            'plan': self.plan,
            'line_index': self.line_index
        }
        if self.metadata:
            result['metadata'] = self.metadata
        return result
