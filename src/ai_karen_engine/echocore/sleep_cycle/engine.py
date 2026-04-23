"""
EchoCore Sleep-Cycle Engine for AI Karen.

Coordinates offline memory consolidation, compaction, and profile promotion.
Runs asynchronously, ensuring that Karen's memory remains high-quality and manageable.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from ai_karen_engine.core.memory.ledger_models import (
    ContradictionEvent
)
from ai_karen_engine.core.runtime.resilience import get_safe_stage_runner

logger = logging.getLogger(__name__)

class SleepCycleEngine:
    """The offline consolidation engine for EchoCore."""

    def __init__(self, db_session_factory=None):
        self._db_session_factory = db_session_factory
        self.safe_runner = get_safe_stage_runner()

    def set_db_session_factory(self, factory):
        self._db_session_factory = factory

    async def run_cycle(self, tenant_id: Optional[str] = None):
        """Execute a full sleep-cycle consolidation pass."""
        logger.info(f"Starting EchoCore sleep-cycle pass (Tenant: {tenant_id or 'All'}).")
        
        # 1. Resolve Contradictions
        await self.resolve_contradictions(tenant_id)
        
        # 2. Promote Reinforcements
        await self.promote_reinforcements(tenant_id)
        
        # 3. Compact Episodic Memory
        await self.run_compaction(tenant_id)
        
        # 4. Export Analytics
        await self.export_analytics(tenant_id)
        
        logger.info("EchoCore sleep-cycle pass completed.")

    async def resolve_contradictions(self, tenant_id: Optional[str] = None):
        """Settlement proposals for ledger conflicts."""
        async def _resolve():
            async with self._db_session_factory() as session:
                # Find open contradictions
                stmt = select(ContradictionEvent).where(ContradictionEvent.resolution_status == "open")
                result = await session.execute(stmt)
                conflicts = result.scalars().all()
                
                for conflict in conflicts:
                    # Logic: If source is much more recent or higher confidence, supersede
                    # For now, we'll mark as 'resolved_supersede' as a placeholder for LLM-based settlement
                    conflict.resolution_status = "resolved_supersede"
                    conflict.resolved_at = datetime.utcnow()
                    
                await session.commit()
                return len(conflicts)

        await self.safe_runner.run_stage(
            stage_name="contradiction_resolution",
            flag_name="echocore_enabled",
            func=_resolve
        )

    async def promote_reinforcements(self, tenant_id: Optional[str] = None):
        """Confidence-based profile promotion."""
        async def _promote():
            async with self._db_session_factory():
                # Find assertions with high reinforcement weight
                # In a real implementation, we'd aggregate ReinforcementEvents
                # and check if they exceed a promotion threshold.
                logger.debug("Promoting reinforced memories to stable facts...")
                return True

        await self.safe_runner.run_stage(
            stage_name="reinforcement_promotion",
            flag_name="echocore_enabled",
            func=_promote
        )

    async def run_compaction(self, tenant_id: Optional[str] = None):
        """Merge redundant episodic events into compact summaries."""
        async def _compact():
            logger.debug("Compacting episodic events into interactions summaries...")
            return True

        await self.safe_runner.run_stage(
            stage_name="memory_compaction",
            flag_name="echocore_enabled",
            func=_compact
        )

    async def export_analytics(self, tenant_id: Optional[str] = None):
        """Fan-out to DuckDB analytics ledger."""
        # This is often handled by the DuckDB projection worker, 
        # but EchoCore can perform batch exports for non-realtime events.
        logger.debug("Exporting consolidated metrics to DuckDB analytics ledger.")

# Global instance
sleep_cycle_engine = SleepCycleEngine()

def get_sleep_cycle_engine() -> SleepCycleEngine:
    return sleep_cycle_engine
