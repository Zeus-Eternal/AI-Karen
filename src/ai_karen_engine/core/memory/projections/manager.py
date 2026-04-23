"""
Projection Manager for AI Karen Memory System.

Orchestrates multiple projection workers to fan out memory events.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from .base import ProjectionWorker
from .milvus_worker import MilvusWorker
from .elastic_worker import ElasticWorker
from .redis_worker import RedisWorker
from .leangraph_worker import LeanGraphWorker
from .duckdb_worker import DuckDBWorker
from ...runtime.resilience import get_safe_stage_runner

logger = logging.getLogger(__name__)

class ProjectionManager:
    """Manages the fan-out of memory projections."""

    def __init__(self):
        self.workers: Dict[str, ProjectionWorker] = {
            "milvus": MilvusWorker(),
            "elasticsearch": ElasticWorker(),
            "redis": RedisWorker(),
            "leangraph": LeanGraphWorker(),
            "duckdb": DuckDBWorker()
        }
        self.safe_runner = get_safe_stage_runner()

    async def project_event(self, event_data: Dict[str, Any], assertion_data: Optional[Dict[str, Any]] = None):
        """
        Fan out the event to all registered workers.
        Uses SafeStageRunner for each projection to ensure isolation and resilience.
        """
        event_id = str(event_data.get("event_id"))
        tenant_id = str(event_data.get("tenant_id"))
        user_id = str(event_data.get("user_id"))

        tasks = []
        for store_name, worker in self.workers.items():
            # Use specific flag for each projection store if desired, 
            # or generic feature flags.
            flag_name = f"{store_name}_enabled"
            if store_name == "leangraph":
                flag_name = "graph_relationships_enabled"
            elif store_name == "elasticsearch":
                flag_name = "elasticsearch_hybrid_enabled"

            # Projection task
            tasks.append(
                self.safe_runner.run_stage(
                    stage_name=f"{store_name}_projection",
                    flag_name=flag_name,
                    func=worker.project,
                    event_data=event_data,
                    assertion_data=assertion_data,
                    tenant_id=tenant_id,
                    user_id=user_id
                )
            )

        # Execute projections concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for idx, (store_name, _) in enumerate(self.workers.items()):
            res = results[idx]
            if isinstance(res, Exception):
                logger.error(f"Projection to {store_name} failed with exception: {res}")
            elif res is False:
                logger.warning(f"Projection to {store_name} returned False (failed/blocked).")
            else:
                logger.debug(f"Projection to {store_name} successful for event {event_id}")

# Singleton instance
projection_manager = ProjectionManager()

def get_projection_manager() -> ProjectionManager:
    return projection_manager
