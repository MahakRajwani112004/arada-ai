"""Storage package."""
from .agent_repository import (
    BaseAgentRepository,
    FileAgentRepository,
    InMemoryAgentRepository,
    PostgresAgentRepository,
)
from .database import close_database, get_async_session, get_session, init_database
from .models import AgentModel, Base, WorkflowApprovalModel, WorkflowExecutionModel, WorkflowModel
from .workflow_repository import WorkflowRepository
from .approval_repository import ApprovalRepository
from .schedule_repository import ScheduleRepository

# Import monitoring models so they're registered with SQLAlchemy metadata
# This ensures tables are created when init_database() calls Base.metadata.create_all()
from src.monitoring.analytics.models import AgentExecutionModel, LLMUsageModel

__all__ = [
    "Base",
    "AgentModel",
    "WorkflowModel",
    "WorkflowExecutionModel",
    "WorkflowApprovalModel",
    "LLMUsageModel",
    "AgentExecutionModel",
    "BaseAgentRepository",
    "InMemoryAgentRepository",
    "FileAgentRepository",
    "PostgresAgentRepository",
    "WorkflowRepository",
    "ApprovalRepository",
    "ScheduleRepository",
    "init_database",
    "close_database",
    "get_session",
    "get_async_session",
]
