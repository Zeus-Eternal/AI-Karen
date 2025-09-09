from dataclasses import dataclass
import math

@dataclass
class AdmissionConfig:
    """Configuration for case admission policy"""
    min_reward: float = 0.55
    novelty_threshold: float = 0.12
    max_cases_per_tenant: int = 50000
    decay_lambda: float = 0.1  # v(t)=v0*e^(−λt) per week

class AdmissionPolicy:
    """Policy for deciding which cases to admit to memory"""
    
    def __init__(self, cfg: AdmissionConfig):
        self.cfg = cfg
    
    def should_admit(self, reward: float, novelty: float) -> bool:
        """Determine if a case should be admitted based on reward and novelty"""
        return (reward >= self.cfg.min_reward) and (novelty >= self.cfg.novelty_threshold)
    
    def value_with_decay(self, v: float, weeks: float) -> float:
        """Calculate decayed value over time"""
        return v * math.exp(-self.cfg.decay_lambda * weeks)
