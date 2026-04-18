"""
Database service for the extension registry system.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, or_, func

from .database_models import (
    ExtensionDBModel,
    ExtensionInstallationHistory,
    ExtensionHookAssignment,
    ExtensionDependencyGraph,
    ExtensionValidationLog,
    ExtensionUsageMetrics,
    Base,
)
from .manifest import ExtensionStatus, ExtensionRecord
from .plugin_registry import PluginRegistry

logger = logging.getLogger("kari.extension_database")


class ExtensionDatabaseService:
    """
    Database service for managing extension registry data.
    Handles all database operations for extensions, hooks, and dependencies.
    """

    def __init__(self, database_url: str, pool_size: int = 10, max_overflow: int = 20):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        # Create async engine
        self.engine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,  # Set to True for SQL debugging
            future=True,
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        async with self.SessionLocal() as session:
            yield session

    async def initialize(self):
        """Initialize database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Extension database tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize extension database: {e}")
            raise

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Extension database connections closed")

    # Extension CRUD operations
    async def create_extension(
        self, manifest: Dict[str, Any], directory_path: Optional[str] = None
    ) -> ExtensionDBModel:
        """Create a new extension record."""
        async with self.SessionLocal() as session:
            extension = ExtensionDBModel(
                name=manifest["name"],
                version=manifest["version"],
                display_name=manifest["display_name"],
                description=manifest["description"],
                author=manifest.get("author"),
                license=manifest.get("license"),
                category=manifest.get("category"),
                tags=manifest.get("tags", []),
                api_version=manifest.get("api_version", "1.0"),
                kari_min_version=manifest.get("kari_min_version", "0.4.0"),
                capabilities=manifest.get("capabilities", {}),
                dependencies=manifest.get("dependencies", {}),
                permissions=manifest.get("permissions", {}),
                resources=manifest.get("resources", {}),
                ui_config=manifest.get("ui", {}),
                api_config=manifest.get("api", {}),
                background_tasks=manifest.get("background_tasks", []),
                marketplace_info=manifest.get("marketplace", {}),
                directory_path=directory_path,
                status=ExtensionStatus.INACTIVE,
            )

            session.add(extension)
            await session.flush()
            await session.refresh(extension)

            # Log the installation
            await self._log_installation(
                session,
                extension.id,
                "install",
                manifest.get("version"),
                None,
                "system",
            )

            logger.info(
                f"Created extension record: {manifest['name']} v{manifest['version']}"
            )
            return extension

    async def get_extension(
        self, extension_id: uuid.UUID
    ) -> Optional[ExtensionDBModel]:
        """Get extension by ID."""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(ExtensionDBModel).where(ExtensionDBModel.id == extension_id)
            )
            return result.scalar_one_or_none()

    async def get_extension_by_name(
        self, name: str, version: Optional[str] = None
    ) -> Optional[ExtensionDBModel]:
        """Get extension by name and optionally version."""
        async with self.SessionLocal() as session:
            query = select(ExtensionDBModel).where(ExtensionDBModel.name == name)
            if version:
                query = query.where(ExtensionDBModel.version == version)

            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def list_extensions(
        self,
        status: Optional[ExtensionStatus] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ExtensionDBModel]:
        """List extensions with optional filtering."""
        async with self.SessionLocal() as session:
            query = select(ExtensionDBModel)

            if status:
                query = query.where(ExtensionDBModel.status == status)
            if category:
                query = query.where(ExtensionDBModel.category == category)

            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def update_extension(
        self, extension_id: uuid.UUID, updates: Dict[str, Any]
    ) -> Optional[ExtensionDBModel]:
        """Update extension record."""
        async with self.SessionLocal() as session:
            await session.execute(
                update(ExtensionDBModel)
                .where(ExtensionDBModel.id == extension_id)
                .values(**updates, updated_at=datetime.utcnow())
            )
            await session.flush()

            return await self.get_extension(extension_id)

    async def delete_extension(self, extension_id: uuid.UUID) -> bool:
        """Delete extension record and all related data."""
        async with self.SessionLocal() as session:
            # Delete related records first (due to foreign key constraints)
            await session.execute(
                delete(ExtensionHookAssignment).where(
                    ExtensionHookAssignment.extension_id == extension_id
                )
            )
            await session.execute(
                delete(ExtensionDependencyGraph).where(
                    or_(
                        ExtensionDependencyGraph.extension_id == extension_id,
                        ExtensionDependencyGraph.dependency_id == extension_id,
                    )
                )
            )
            await session.execute(
                delete(ExtensionValidationLog).where(
                    ExtensionValidationLog.extension_id == extension_id
                )
            )
            await session.execute(
                delete(ExtensionUsageMetrics).where(
                    ExtensionUsageMetrics.extension_id == extension_id
                )
            )
            await session.execute(
                delete(ExtensionInstallationHistory).where(
                    or_(
                        ExtensionInstallationHistory.extension_id == extension_id,
                        ExtensionInstallationHistory.version_from == extension_id,
                        ExtensionInstallationHistory.version_to == extension_id,
                    )
                )
            )

            # Delete the extension itself
            result = await session.execute(
                delete(ExtensionDBModel).where(ExtensionDBModel.id == extension_id)
            )

            await session.flush()
            return result.rowcount > 0

    # Hook management
    async def assign_hook(
        self,
        extension_id: uuid.UUID,
        hook_point: str,
        priority: int = 0,
        assigned_by: str = "system",
    ) -> ExtensionHookAssignment:
        """Assign an extension to a hook point."""
        async with self.SessionLocal() as session:
            # Check if assignment exists
            result = await session.execute(
                select(ExtensionHookAssignment).where(
                    and_(
                        ExtensionHookAssignment.extension_id == extension_id,
                        ExtensionHookAssignment.hook_point == hook_point,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing assignment
                existing.hook_priority = priority
                existing.is_active = True
                existing.assigned_by = assigned_by
                await session.flush()
                return existing
            else:
                # Create new assignment
                assignment = ExtensionHookAssignment(
                    extension_id=extension_id,
                    hook_point=hook_point,
                    hook_priority=priority,
                    assigned_by=assigned_by,
                )
                session.add(assignment)
                await session.flush()
                await session.refresh(assignment)
                return assignment

    async def unassign_hook(self, extension_id: uuid.UUID, hook_point: str) -> bool:
        """Remove an extension from a hook point."""
        async with self.SessionLocal() as session:
            result = await session.execute(
                delete(ExtensionHookAssignment).where(
                    and_(
                        ExtensionHookAssignment.extension_id == extension_id,
                        ExtensionHookAssignment.hook_point == hook_point,
                    )
                )
            )
            await session.flush()
            return result.rowcount > 0

    async def get_hook_assignments(
        self, hook_point: Optional[str] = None, active_only: bool = True
    ) -> List[ExtensionHookAssignment]:
        """Get hook assignments, optionally filtered."""
        async with self.SessionLocal() as session:
            query = select(ExtensionHookAssignment)

            if hook_point:
                query = query.where(ExtensionHookAssignment.hook_point == hook_point)
            if active_only:
                query = query.where(ExtensionHookAssignment.is_active == True)

            query = query.order_by(ExtensionHookAssignment.hook_priority.desc())
            result = await session.execute(query)
            return result.scalars().all()

    # Installation history
    async def _log_installation(
        self,
        session: AsyncSession,
        extension_id: uuid.UUID,
        action: str,
        version_from: Optional[str],
        version_to: str,
        performed_by: str,
        reason: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Log installation history."""
        history = ExtensionInstallationHistory(
            extension_id=extension_id,
            action=action,
            version_from=version_from,
            version_to=version_to,
            performed_by=performed_by,
            reason=reason,
            success=success,
            error_message=error_message,
        )
        session.add(history)

    async def get_installation_history(
        self, extension_id: uuid.UUID, limit: int = 50
    ) -> List[ExtensionInstallationHistory]:
        """Get installation history for an extension."""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(ExtensionInstallationHistory)
                .where(ExtensionInstallationHistory.extension_id == extension_id)
                .order_by(ExtensionInstallationHistory.performed_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    # Statistics and analytics
    async def get_extension_stats(self) -> Dict[str, Any]:
        """Get extension statistics."""
        async with self.SessionLocal() as session:
            # Total extensions
            total_result = await session.execute(
                select(func.count(ExtensionDBModel.id))
            )
            total_extensions = total_result.scalar() or 0

            # Extensions by status
            status_counts = {}
            for status in ExtensionStatus:
                count_result = await session.execute(
                    select(func.count(ExtensionDBModel.id)).where(
                        ExtensionDBModel.status == status
                    )
                )
                status_counts[status.value] = count_result.scalar() or 0

            # Extensions by category
            category_result = await session.execute(
                select(
                    ExtensionDBModel.category,
                    func.count(ExtensionDBModel.id).label("count"),
                )
                .group_by(ExtensionDBModel.category)
                .order_by(func.count(ExtensionDBModel.id).desc())
            )
            category_counts = {
                row.category: row.count for row in category_result.fetchall()
            }

            return {
                "total_extensions": total_extensions,
                "by_status": status_counts,
                "by_category": category_counts,
            }

    async def get_usage_metrics(
        self, extension_id: uuid.UUID, days: int = 30
    ) -> Dict[str, Any]:
        """Get usage metrics for an extension."""
        async with self.SessionLocal() as session:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await session.execute(
                select(ExtensionUsageMetrics)
                .where(
                    and_(
                        ExtensionUsageMetrics.extension_id == extension_id,
                        ExtensionUsageMetrics.period_start >= cutoff_date,
                    )
                )
                .order_by(ExtensionUsageMetrics.period_start.desc())
            )

            metrics = result.scalars().all()

            if not metrics:
                return {
                    "usage_count": 0,
                    "unique_users": 0,
                    "error_count": 0,
                    "average_execution_time_ms": 0,
                    "period_days": days,
                }

            total_usage = sum(m.usage_count for m in metrics)
            total_users = sum(m.unique_users for m in metrics)
            total_errors = sum(m.error_count for m in metrics)
            avg_time = sum(m.average_execution_time_ms or 0 for m in metrics) / len(
                metrics
            )

            return {
                "usage_count": total_usage,
                "unique_users": total_users,
                "error_count": total_errors,
                "average_execution_time_ms": avg_time,
                "period_days": days,
            }

    # Utility methods
    async def search_extensions(
        self, query: str, limit: int = 20
    ) -> List[ExtensionDBModel]:
        """Search extensions by name, description, or tags."""
        async with self.SessionLocal() as session:
            search_pattern = f"%{query}%"

            result = await session.execute(
                select(ExtensionDBModel)
                .where(
                    or_(
                        ExtensionDBModel.name.ilike(search_pattern),
                        ExtensionDBModel.display_name.ilike(search_pattern),
                        ExtensionDBModel.description.ilike(search_pattern),
                        ExtensionDBModel.tags.ilike(search_pattern),
                    )
                )
                .limit(limit)
            )
            return result.scalars().all()

    async def get_extensions_needing_attention(self) -> List[ExtensionDBModel]:
        """Get extensions that need attention (errors, validation issues, etc.)."""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(ExtensionDBModel)
                .where(
                    or_(
                        ExtensionDBModel.status == ExtensionStatus.ERROR,
                        ExtensionDBModel.error_count > 0,
                        ExtensionDBModel.is_validated == False,
                    )
                )
                .order_by(ExtensionDBModel.last_error_at.desc())
            )
            return result.scalars().all()


# Global database service instance
_database_service: Optional[ExtensionDatabaseService] = None


def get_database_service() -> ExtensionDatabaseService:
    """Get the global database service instance."""
    global _database_service
    if _database_service is None:
        raise ValueError("Database service not initialized")
    return _database_service


def initialize_database_service(
    database_url: str, pool_size: int = 10, max_overflow: int = 20
) -> ExtensionDatabaseService:
    """Initialize the global database service."""
    global _database_service
    _database_service = ExtensionDatabaseService(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
    return _database_service
