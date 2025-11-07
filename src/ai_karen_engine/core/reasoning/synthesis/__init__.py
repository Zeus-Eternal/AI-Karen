"""
Synthesis and ICE Module

Provides Integrated Cognitive Engine (ICE) wrapper and synthesis capabilities.

Components:
- PremiumICEWrapper / KariICEWrapper: ICE integration with policies
- ICEWritebackPolicy: Writeback policies and configuration
- ReasoningTrace: Trace of reasoning process
- SynthesisSubEngine: Protocol for synthesis sub-engines
"""

from ai_karen_engine.core.reasoning.synthesis.ice_wrapper import (
    PremiumICEWrapper,
    ICEWritebackPolicy,
    ReasoningTrace,
    RecallStrategy,
    SynthesisMode,
    ICEPerformanceBaseline,
    ICECircuitBreaker,
)
from ai_karen_engine.core.reasoning.synthesis.subengines import (
    SynthesisSubEngine,
    LangGraphSubEngine,
    DSPySubEngine,
)

# Alias for backward compatibility
KariICEWrapper = PremiumICEWrapper

__all__ = [
    "PremiumICEWrapper",
    "KariICEWrapper",
    "ICEWritebackPolicy",
    "ReasoningTrace",
    "RecallStrategy",
    "SynthesisMode",
    "ICEPerformanceBaseline",
    "ICECircuitBreaker",
    "SynthesisSubEngine",
    "LangGraphSubEngine",
    "DSPySubEngine",
]
