"""Agent Repository - stores and retrieves agent configurations."""
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.agent_config import AgentConfig
from src.storage.models import AgentModel


class BaseAgentRepository(ABC):
    """Abstract base class for agent storage."""

    @abstractmethod
    async def save(self, config: AgentConfig) -> str:
        """Save agent configuration. Returns agent ID."""
        pass

    @abstractmethod
    async def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        pass

    @abstractmethod
    async def list(self) -> List[AgentConfig]:
        """List all agent configurations."""
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """Delete agent configuration. Returns True if deleted."""
        pass

    @abstractmethod
    async def exists(self, agent_id: str) -> bool:
        """Check if agent exists."""
        pass


class InMemoryAgentRepository(BaseAgentRepository):
    """In-memory agent repository for testing and development."""

    def __init__(self):
        """Initialize empty repository."""
        self._agents: Dict[str, AgentConfig] = {}

    async def save(self, config: AgentConfig) -> str:
        """Save agent configuration."""
        self._agents[config.id] = config
        return config.id

    async def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        return self._agents.get(agent_id)

    async def list(self) -> List[AgentConfig]:
        """List all agent configurations."""
        return list(self._agents.values())

    async def delete(self, agent_id: str) -> bool:
        """Delete agent configuration."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    async def exists(self, agent_id: str) -> bool:
        """Check if agent exists."""
        return agent_id in self._agents


class FileAgentRepository(BaseAgentRepository):
    """File-based agent repository."""

    def __init__(self, base_path: str = "./data/agents"):
        """Initialize with base path."""
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_path(self, agent_id: str) -> str:
        """Get file path for agent ID."""
        return os.path.join(self.base_path, f"{agent_id}.json")

    async def save(self, config: AgentConfig) -> str:
        """Save agent configuration to file."""
        path = self._get_path(config.id)
        with open(path, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
        return config.id

    async def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration from file."""
        path = self._get_path(agent_id)
        if not os.path.exists(path):
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return AgentConfig.model_validate(data)

    async def list(self) -> List[AgentConfig]:
        """List all agent configurations."""
        agents = []
        for filename in os.listdir(self.base_path):
            if filename.endswith(".json"):
                agent_id = filename[:-5]  # Remove .json
                config = await self.get(agent_id)
                if config:
                    agents.append(config)
        return agents

    async def delete(self, agent_id: str) -> bool:
        """Delete agent configuration file."""
        path = self._get_path(agent_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    async def exists(self, agent_id: str) -> bool:
        """Check if agent file exists."""
        return os.path.exists(self._get_path(agent_id))


class PostgresAgentRepository(BaseAgentRepository):
    """PostgreSQL-backed agent repository."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    def _to_model(self, config: AgentConfig) -> AgentModel:
        """Convert AgentConfig to ORM model."""
        return AgentModel(
            id=config.id,
            name=config.name,
            description=config.description,
            agent_type=config.agent_type.value,
            is_active=config.is_active,
            config_json=config.model_dump(mode="json"),
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    def _to_config(self, model: AgentModel) -> AgentConfig:
        """Convert ORM model to AgentConfig."""
        return AgentConfig.model_validate(model.config_json)

    async def save(self, config: AgentConfig) -> str:
        """Save agent configuration to database."""
        # Check if exists for update vs insert
        existing = await self.session.get(AgentModel, config.id)

        if existing:
            # Update existing
            existing.name = config.name
            existing.description = config.description
            existing.agent_type = config.agent_type.value
            existing.is_active = config.is_active
            existing.config_json = config.model_dump(mode="json")
            existing.updated_at = datetime.utcnow()
        else:
            # Insert new
            model = self._to_model(config)
            self.session.add(model)

        await self.session.flush()
        return config.id

    async def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        model = await self.session.get(AgentModel, agent_id)
        if model is None:
            return None
        return self._to_config(model)

    async def list(self) -> List[AgentConfig]:
        """List all active agent configurations."""
        stmt = select(AgentModel).where(AgentModel.is_active == True)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_config(m) for m in models]

    async def delete(self, agent_id: str) -> bool:
        """Delete agent configuration (soft delete)."""
        model = await self.session.get(AgentModel, agent_id)
        if model is None:
            return False

        model.is_active = False
        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return True

    async def exists(self, agent_id: str) -> bool:
        """Check if agent exists and is active."""
        model = await self.session.get(AgentModel, agent_id)
        return model is not None and model.is_active
