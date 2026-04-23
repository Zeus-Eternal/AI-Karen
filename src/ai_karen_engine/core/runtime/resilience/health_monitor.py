"""
Health Monitor for AI Karen Resilience Layer.

Monitors the health and state of stages and circuit breakers.
"""

from typing import Dict, Any
from .circuit_breaker import get_breaker_registry

class ResilienceHealthMonitor:
    """Monitors the health of optional stages and resilience components."""
    
    def __init__(self):
        self.breaker_registry = get_breaker_registry()
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get the current health status of all monitored stages."""
        breaker_states = self.breaker_registry.get_all_states()
        
        # Calculate overall health
        open_breakers = [name for name, state in breaker_states.items() if state == "OPEN"]
        half_open_breakers = [name for name, state in breaker_states.items() if state == "HALF_OPEN"]
        
        status = "HEALTHY"
        if open_breakers:
            status = "DEGRADED"
            
        return {
            "status": status,
            "circuit_breakers": breaker_states,
            "open_count": len(open_breakers),
            "half_open_count": len(half_open_breakers),
            "healthy_count": len(breaker_states) - len(open_breakers) - len(half_open_breakers)
        }

health_monitor = ResilienceHealthMonitor()

def get_resilience_health_monitor() -> ResilienceHealthMonitor:
    return health_monitor
