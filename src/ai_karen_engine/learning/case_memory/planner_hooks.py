f"""
Planner Hooks for Case-Memory Learning Integration
Provides hooks for injecting prior episodes and admitting new cases
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from .case_types import Case, StepTrace, ToolIO, Reward
from .retriever import CaseRetriever
from .case_store import CaseStore
from .metrics import get_observer

logger = logging.getLogger(__name__)

HINT_TMPL = "# Prior Episodes (Hints)\n{lines}\n# Use above patterns judiciously.\n"

def _render(cases):
    """Render cases into hint format for prompt injection"""
    L = []
    for i, item in enumerate(cases, 1):
        c = item["case"]
        L.append(f"- [{i}] tags={','.join(c.tags)} | reward={c.reward.score:.2f}")
        if c.plan_text:
            L.append(f"  plan≈ {c.plan_text[:220]}")
    return HINT_TMPL.format(lines="\n".join(L))

class PlannerHooks:
    """Hooks for integrating case memory with planner and executor"""
    
    def __init__(self, retriever, embedder, store, reward_adapters: List):
        self.retriever = retriever
        self.embedder = embedder
        self.store = store
        self.reward_adapters = reward_adapters

    def pre_plan_context(self, tenant_id: str, task_text: str, tags: List[str]) -> str:
        """Generate context hints from prior episodes for planning"""
        observer = get_observer()
        operation_id = f"hint_injection_{tenant_id}_{hash(task_text)}"
        observer.start_timing(operation_id, "retrieval")
        
        try:
            cases = self.retriever.retrieve(tenant_id, task_text, tags)
            
            if cases:
                # Calculate average similarity score
                avg_score = sum(case.get("score", 0) for case in cases) / len(cases)
                observer.end_timing(operation_id, success=True, 
                                  hints_count=len(cases), avg_score=avg_score)
                return _render(cases)
            else:
                observer.end_timing(operation_id, success=True, hints_count=0)
                return ""
                
        except Exception as e:
            observer.end_timing(operation_id, success=False, error=str(e))
            logger.error(f"Failed to generate pre-plan context: {e}")
            return ""

    def on_run_complete(self, *, tenant_id: str, user_id: str | None, task_text: str,
                        goal_text: str | None, plan_text: str | None, steps: List[StepTrace],
                        outcome_text: str, tags: List[str], pointers: Dict[str, str]) -> None:
        """Process completed run and admit case to memory"""
        observer = get_observer()
        operation_id = f"case_admission_{tenant_id}_{hash(task_text)}"
        observer.start_timing(operation_id, "admission")
        
        try:
            # Compute reward signals from adapters
            signals = {}
            for r in self.reward_adapters:
                try:
                    v = r.compute()  # adapter returns 0..1 or None
                    if v is not None:
                        signals[r.name] = float(v)
                except Exception as e:
                    logger.warning(f"Reward adapter {getattr(r, 'name', 'unknown')} failed: {e}")
            
            # Fallback baseline if no signals
            if not signals:
                signals["baseline"] = 0.5
            
            # Average signals for overall score
            score = sum(signals.values()) / len(signals)
            
            # Create case with embeddings
            case = Case(
                case_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                created_at=datetime.utcnow(),
                task_text=task_text,
                goal_text=goal_text,
                plan_text=plan_text,
                steps=tuple(steps),
                outcome_text=outcome_text,
                tags=tuple(tags),
                reward=Reward(score=score, signals=signals),
                pointers=pointers,
                embeddings={
                    "task": self.embedder.embed(task_text),
                    "plan": self.embedder.embed(plan_text or task_text),
                    "outcome": self.embedder.embed(outcome_text),
                }
            )
            
            # Calculate case size for metrics
            case_size = len(str(case).encode('utf-8'))
            
            # Admit case to storage
            self.store.admit(case)
            
            # Record metrics
            observer.record_case_admission(case_size, score, tags[0] if tags else None)
            observer.end_timing(operation_id, success=True, case_size=case_size, reward=score)
            
            logger.info(f"Admitted case {case.case_id} with reward {score:.3f}")
            
        except Exception as e:
            observer.end_timing(operation_id, success=False, error=str(e))
            logger.error(f"Failed to process run completion: {e}")
            # Never break user flow due to learning layer failures
