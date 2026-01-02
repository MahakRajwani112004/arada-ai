"""Agent Repository - stores and retrieves agent configurations."""
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
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

    def __init__(self, session: AsyncSession, user_id: str | None = None):
        """Initialize with database session and optional user_id for filtering."""
        self.session = session
        self.user_id = user_id

    def _to_model(self, config: AgentConfig) -> AgentModel:
        """Convert AgentConfig to ORM model."""
        model = AgentModel(
            id=config.id,
            name=config.name,
            description=config.description,
            agent_type=config.agent_type.value,
            is_active=config.is_active,
            config_json=config.model_dump(mode="json"),
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
        # Set user_id if available
        if self.user_id:
            model.user_id = self.user_id
        return model

    def _to_config(self, model: AgentModel) -> AgentConfig:
        """Convert ORM model to AgentConfig."""
        return AgentConfig.model_validate(model.config_json)

    async def save(self, config: AgentConfig) -> str:
        """Save agent configuration to database."""
        # Check if exists for update vs insert (scoped to user if user_id is set)
        stmt = select(AgentModel).where(AgentModel.id == config.id)
        if self.user_id:
            stmt = stmt.where(AgentModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.name = config.name
            existing.description = config.description
            existing.agent_type = config.agent_type.value
            existing.is_active = config.is_active
            existing.config_json = config.model_dump(mode="json")
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # Insert new
            model = self._to_model(config)
            self.session.add(model)

        await self.session.flush()
        return config.id

    async def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID (scoped to user if user_id is set)."""
        stmt = select(AgentModel).where(AgentModel.id == agent_id)
        if self.user_id:
            stmt = stmt.where(AgentModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_config(model)

    async def list(self) -> List[AgentConfig]:
        """List all active agent configurations (scoped to user if user_id is set)."""
        stmt = select(AgentModel).where(AgentModel.is_active == True)
        if self.user_id:
            stmt = stmt.where(AgentModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_config(m) for m in models]

    async def delete(self, agent_id: str) -> bool:
        """Delete agent configuration (soft delete, scoped to user if user_id is set)."""
        stmt = select(AgentModel).where(AgentModel.id == agent_id)
        if self.user_id:
            stmt = stmt.where(AgentModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        model.is_active = False
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def exists(self, agent_id: str) -> bool:
        """Check if agent exists and is active (scoped to user if user_id is set)."""
        stmt = select(AgentModel).where(
            AgentModel.id == agent_id,
            AgentModel.is_active == True,
        )
        if self.user_id:
            stmt = stmt.where(AgentModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model is not None

    async def migrate_mcp_tool_references(
        self,
        old_server_id: str,
        new_server_id: str,
    ) -> int:
        """Migrate agent tool references from old MCP server ID to new one.

        This is used when an MCP server is reconnected/recreated and gets a new ID.
        Updates all agents that reference tools from the old server.

        Args:
            old_server_id: The old MCP server ID (e.g., "srv_abc123")
            new_server_id: The new MCP server ID (e.g., "srv_def456")

        Returns:
            Number of agents updated
        """
        # Find all active agents for this user that have tools referencing the old server
        stmt = select(AgentModel).where(AgentModel.is_active == True)
        if self.user_id:
            stmt = stmt.where(AgentModel.user_id == self.user_id)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        updated_count = 0
        for model in models:
            config = model.config_json
            tools = config.get("tools", [])
            if not tools:
                continue

            # Check if any tool references the old server
            updated_tools = []
            has_updates = False
            for tool in tools:
                tool_id = tool.get("tool_id", "")
                if tool_id.startswith(f"{old_server_id}:"):
                    # Replace old server ID with new one
                    tool_name = tool_id.split(":", 1)[1]
                    tool["tool_id"] = f"{new_server_id}:{tool_name}"
                    has_updates = True
                updated_tools.append(tool)

            if has_updates:
                config["tools"] = updated_tools
                model.config_json = config
                model.updated_at = datetime.now(timezone.utc)
                updated_count += 1

        if updated_count > 0:
            await self.session.flush()

        return updated_count

    async def find_agents_with_stale_mcp_tools(
        self,
        valid_server_ids: List[str],
    ) -> List[tuple]:
        """Find agents that have tool references to non-existent MCP servers.

        Args:
            valid_server_ids: List of currently valid MCP server IDs

        Returns:
            List of tuples: (agent_id, stale_server_ids)
        """
        stmt = select(AgentModel).where(AgentModel.is_active == True)
        if self.user_id:
            stmt = stmt.where(AgentModel.user_id == self.user_id)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        stale_agents = []
        for model in models:
            config = model.config_json
            tools = config.get("tools", [])
            if not tools:
                continue

            stale_servers = set()
            for tool in tools:
                tool_id = tool.get("tool_id", "")
                if ":" in tool_id:
                    server_id = tool_id.split(":", 1)[0]
                    if server_id.startswith("srv_") and server_id not in valid_server_ids:
                        stale_servers.add(server_id)

            if stale_servers:
                stale_agents.append((model.id, list(stale_servers)))

        return stale_agents
