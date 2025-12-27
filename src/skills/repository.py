"""Skill Repository - database operations for skills."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.storage.models import SkillModel, SkillVersionModel, SkillExecutionModel

from .models import (
    Skill,
    SkillDefinition,
    SkillCategory,
    SkillStatus,
)

logger = get_logger(__name__)


class SkillRepository:
    """Repository for skill database operations.

    Handles storing/retrieving skills and their versions.
    """

    def __init__(self, session: AsyncSession, user_id: str | None = None):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
            user_id: Optional user ID for filtering (multi-tenant)
        """
        self._session = session
        self._user_id = user_id

    async def create(
        self,
        name: str,
        description: str,
        category: SkillCategory,
        tags: List[str],
        definition: SkillDefinition,
        created_by: Optional[str] = None,
    ) -> Skill:
        """Create a new skill.

        Args:
            name: Skill name
            description: Skill description
            category: Skill category
            tags: List of tags
            definition: Full skill definition
            created_by: Creator identifier

        Returns:
            Created Skill

        Raises:
            ValueError: If user_id is not set
        """
        if not self._user_id:
            raise ValueError("user_id is required for creating skills")

        # Generate unique ID
        skill_id = f"skill_{uuid.uuid4().hex[:12]}"

        # Update definition metadata with the generated ID
        definition.metadata.id = skill_id

        # Create database record
        db_model = SkillModel(
            id=skill_id,
            user_id=self._user_id,
            name=name,
            description=description,
            category=category.value,
            tags=tags,
            definition_json=definition.to_dict(),
            version=1,
            status=SkillStatus.DRAFT.value,
            is_public=False,
            created_by=created_by or self._user_id,
        )

        self._session.add(db_model)
        await self._session.commit()
        await self._session.refresh(db_model)

        logger.info("skill_created", skill_id=skill_id, name=name, category=category.value)

        return self._to_skill(db_model)

    async def get(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID (scoped to user if user_id is set).

        Args:
            skill_id: Skill ID

        Returns:
            Skill if found, None otherwise
        """
        query = select(SkillModel).where(SkillModel.id == skill_id)

        # If user_id is set, filter by user or public skills
        if self._user_id:
            query = query.where(
                or_(
                    SkillModel.user_id == self._user_id,
                    SkillModel.is_public == True,
                )
            )

        result = await self._session.execute(query)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        return self._to_skill(db_model)

    async def list(
        self,
        category: Optional[SkillCategory] = None,
        tags: Optional[List[str]] = None,
        status: Optional[SkillStatus] = None,
        search: Optional[str] = None,
        include_public: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Skill]:
        """List skills with optional filtering.

        Args:
            category: Filter by category
            tags: Filter by tags (any match)
            status: Filter by status
            search: Search in name/description
            include_public: Include public skills from marketplace
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of skills
        """
        query = select(SkillModel)

        # Base filter: user's skills or public
        if self._user_id:
            if include_public:
                query = query.where(
                    or_(
                        SkillModel.user_id == self._user_id,
                        SkillModel.is_public == True,
                    )
                )
            else:
                query = query.where(SkillModel.user_id == self._user_id)

        # Category filter
        if category:
            query = query.where(SkillModel.category == category.value)

        # Status filter
        if status:
            query = query.where(SkillModel.status == status.value)

        # Tags filter (any match)
        if tags:
            query = query.where(SkillModel.tags.overlap(tags))

        # Search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    SkillModel.name.ilike(search_pattern),
                    SkillModel.description.ilike(search_pattern),
                )
            )

        # Order by updated_at descending
        query = query.order_by(SkillModel.updated_at.desc())

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self._session.execute(query)
        db_models = result.scalars().all()

        return [self._to_skill(m) for m in db_models]

    async def update(
        self,
        skill_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[SkillCategory] = None,
        tags: Optional[List[str]] = None,
        definition: Optional[SkillDefinition] = None,
        status: Optional[SkillStatus] = None,
        changelog: Optional[str] = None,
    ) -> Optional[Skill]:
        """Update a skill.

        If definition is updated, creates a new version.

        Args:
            skill_id: Skill ID
            name: New name
            description: New description
            category: New category
            tags: New tags
            definition: New definition (triggers version bump)
            status: New status
            changelog: Description of changes

        Returns:
            Updated Skill if found, None otherwise
        """
        if not self._user_id:
            raise ValueError("user_id is required for updating skills")

        # Get existing skill
        query = select(SkillModel).where(
            and_(
                SkillModel.id == skill_id,
                SkillModel.user_id == self._user_id,
            )
        )
        result = await self._session.execute(query)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        # Track if definition changed for versioning
        definition_changed = False

        # Update fields
        if name is not None:
            db_model.name = name
        if description is not None:
            db_model.description = description
        if category is not None:
            db_model.category = category.value
        if tags is not None:
            db_model.tags = tags
        if status is not None:
            db_model.status = status.value

        if definition is not None:
            # Save current version before updating
            version_id = f"sv_{uuid.uuid4().hex[:12]}"
            version_model = SkillVersionModel(
                id=version_id,
                skill_id=skill_id,
                version=db_model.version,
                definition_json=db_model.definition_json,
                changelog=changelog or f"Version {db_model.version}",
            )
            self._session.add(version_model)

            # Update definition and bump version
            definition.metadata.id = skill_id
            db_model.definition_json = definition.to_dict()
            db_model.version += 1
            definition_changed = True

        db_model.updated_at = datetime.now(timezone.utc)

        await self._session.commit()
        await self._session.refresh(db_model)

        if definition_changed:
            logger.info(
                "skill_updated_with_new_version",
                skill_id=skill_id,
                new_version=db_model.version,
            )
        else:
            logger.info("skill_updated", skill_id=skill_id)

        return self._to_skill(db_model)

    async def delete(self, skill_id: str) -> bool:
        """Delete a skill.

        Args:
            skill_id: Skill ID

        Returns:
            True if deleted, False if not found
        """
        if not self._user_id:
            raise ValueError("user_id is required for deleting skills")

        query = select(SkillModel).where(
            and_(
                SkillModel.id == skill_id,
                SkillModel.user_id == self._user_id,
            )
        )
        result = await self._session.execute(query)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return False

        await self._session.delete(db_model)
        await self._session.commit()

        logger.info("skill_deleted", skill_id=skill_id)

        return True

    async def get_versions(self, skill_id: str) -> List[Dict[str, Any]]:
        """Get version history for a skill.

        Args:
            skill_id: Skill ID

        Returns:
            List of version info (not full definitions)
        """
        query = (
            select(SkillVersionModel)
            .where(SkillVersionModel.skill_id == skill_id)
            .order_by(SkillVersionModel.version.desc())
        )
        result = await self._session.execute(query)
        versions = result.scalars().all()

        return [
            {
                "version": v.version,
                "changelog": v.changelog,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ]

    async def get_version(self, skill_id: str, version: int) -> Optional[SkillDefinition]:
        """Get a specific version of a skill's definition.

        Args:
            skill_id: Skill ID
            version: Version number

        Returns:
            SkillDefinition for that version, or None
        """
        query = select(SkillVersionModel).where(
            and_(
                SkillVersionModel.skill_id == skill_id,
                SkillVersionModel.version == version,
            )
        )
        result = await self._session.execute(query)
        version_model = result.scalar_one_or_none()

        if version_model is None:
            return None

        return SkillDefinition.from_dict(version_model.definition_json)

    async def rollback_to_version(
        self, skill_id: str, version: int
    ) -> Optional[Skill]:
        """Rollback a skill to a previous version.

        Args:
            skill_id: Skill ID
            version: Version to rollback to

        Returns:
            Updated skill, or None if not found
        """
        # Get the version definition
        old_definition = await self.get_version(skill_id, version)
        if old_definition is None:
            return None

        # Update with the old definition (will create a new version)
        return await self.update(
            skill_id=skill_id,
            definition=old_definition,
            changelog=f"Rolled back to version {version}",
        )

    async def publish_to_marketplace(self, skill_id: str) -> Optional[Skill]:
        """Publish a skill to the marketplace.

        Args:
            skill_id: Skill ID

        Returns:
            Updated skill, or None if not found
        """
        if not self._user_id:
            raise ValueError("user_id is required for publishing skills")

        query = select(SkillModel).where(
            and_(
                SkillModel.id == skill_id,
                SkillModel.user_id == self._user_id,
            )
        )
        result = await self._session.execute(query)
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        # Generate marketplace ID if not exists
        if not db_model.marketplace_id:
            db_model.marketplace_id = f"mp_{uuid.uuid4().hex[:12]}"

        db_model.is_public = True
        db_model.status = SkillStatus.PUBLISHED.value
        db_model.updated_at = datetime.now(timezone.utc)

        await self._session.commit()
        await self._session.refresh(db_model)

        logger.info(
            "skill_published_to_marketplace",
            skill_id=skill_id,
            marketplace_id=db_model.marketplace_id,
        )

        return self._to_skill(db_model)

    async def record_execution(
        self,
        skill_id: str,
        agent_id: Optional[str],
        success: bool,
        duration_ms: float,
        error_message: Optional[str] = None,
        task_preview: Optional[str] = None,
    ) -> None:
        """Record a skill execution for analytics.

        Args:
            skill_id: Skill ID
            agent_id: Agent that used the skill
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed
            task_preview: First 500 chars of input task
        """
        if not self._user_id:
            return  # Skip recording if no user context

        execution_id = f"se_{uuid.uuid4().hex[:12]}"

        execution = SkillExecutionModel(
            id=execution_id,
            skill_id=skill_id,
            agent_id=agent_id,
            user_id=self._user_id,
            success=success,
            duration_ms=int(duration_ms),
            error_message=error_message,
            task_preview=task_preview[:500] if task_preview else None,
        )

        self._session.add(execution)
        await self._session.commit()

    async def get_stats(self, skill_id: str) -> Dict[str, Any]:
        """Get execution statistics for a skill.

        Args:
            skill_id: Skill ID

        Returns:
            Stats dict with execution counts, success rate, avg duration
        """
        # Total executions
        total_query = select(func.count()).where(
            SkillExecutionModel.skill_id == skill_id
        )
        total_result = await self._session.execute(total_query)
        total_count = total_result.scalar() or 0

        if total_count == 0:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
            }

        # Success count
        success_query = select(func.count()).where(
            and_(
                SkillExecutionModel.skill_id == skill_id,
                SkillExecutionModel.success == True,
            )
        )
        success_result = await self._session.execute(success_query)
        success_count = success_result.scalar() or 0

        # Average duration
        avg_query = select(func.avg(SkillExecutionModel.duration_ms)).where(
            SkillExecutionModel.skill_id == skill_id
        )
        avg_result = await self._session.execute(avg_query)
        avg_duration = avg_result.scalar() or 0.0

        return {
            "total_executions": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0.0,
            "avg_duration_ms": float(avg_duration),
        }

    def _to_skill(self, db_model: SkillModel) -> Skill:
        """Convert database model to Skill domain object."""
        return Skill(
            id=db_model.id,
            tenant_id=db_model.user_id,
            name=db_model.name,
            description=db_model.description,
            category=SkillCategory(db_model.category),
            tags=db_model.tags or [],
            definition=SkillDefinition.from_dict(db_model.definition_json),
            version=db_model.version,
            status=SkillStatus(db_model.status),
            is_public=db_model.is_public,
            rating_avg=db_model.rating_avg / 10.0 if db_model.rating_avg else None,
            rating_count=db_model.rating_count,
            install_count=db_model.install_count,
            created_by=db_model.created_by,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )
