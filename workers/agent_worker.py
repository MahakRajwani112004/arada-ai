"""Temporal Worker for Agent Workflows."""
import asyncio
import os
import signal
import sys
from typing import List

from dotenv import load_dotenv
from temporalio.client import Client
from temporalio.worker import Worker

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.activities.action_validator_activity import validate_action
from src.activities.agent_tool_activity import (
    execute_agent_as_tool,
    get_agent_tool_definitions,
)
from src.activities.hallucination_checker_activity import check_hallucination
from src.activities.input_sanitizer_activity import sanitize_input, sanitize_tool_result
from src.activities.knowledge_activity import retrieve_knowledge
from src.activities.llm_activity import llm_completion
from src.activities.loop_detector_activity import detect_loop
from src.activities.safety_activity import check_input_safety, check_output_safety
from src.activities.simple_agent_activity import execute_simple_agent
from src.activities.tool_activity import execute_tool, get_tool_definitions
from src.config.logging import get_logger
from src.mcp import MCPManager, get_mcp_manager
from src.mcp.repository import MCPServerRepository
from src.secrets import init_secrets_manager
from src.storage.database import get_session, init_database
from src.tools.builtin import register_builtin_tools
from src.workflows.agent_workflow import AgentWorkflow

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "agent-tasks")


async def initialize_mcp_tools() -> None:
    """Initialize MCP connections and register tools in the global registry.

    This loads all configured MCP servers from the database and connects to them,
    which registers their tools in the global tool registry.
    """
    logger.info("mcp_initialization_started")

    try:
        # Initialize secrets manager first (needed for MCP credentials)
        init_secrets_manager()
        logger.info("secrets_manager_initialized")

        # Initialize database
        await init_database()
        logger.info("database_initialized")

        # Get database session
        async for session in get_session():
            repository = MCPServerRepository(session)
            manager = get_mcp_manager()

            # Get all configured MCP servers
            servers = await repository.list_all()
            logger.info("mcp_servers_found", count=len(servers))

            # Connect to each server
            for server in servers:
                try:
                    # Get full config with credentials
                    config = await repository.get_config(server.id)
                    if config is None:
                        logger.warning("mcp_server_config_not_found", server_id=server.id)
                        continue

                    # Connect to the MCP server (this registers tools)
                    await manager.add_server(config, register_tools=True)
                    logger.info("mcp_server_connected", server_id=server.id, name=server.name)

                except Exception as e:
                    logger.error(
                        "mcp_server_connection_failed",
                        server_id=server.id,
                        name=server.name,
                        error=str(e),
                    )

            # Log registered tools
            from src.tools.registry import get_registry
            registry = get_registry()
            logger.info("mcp_tools_registered", tools=registry.available_tools)
            break  # Only need one iteration

    except Exception as e:
        logger.error("mcp_initialization_failed", error=str(e))


async def create_worker() -> Worker:
    """Create and return a Temporal worker."""
    # Register builtin tools
    register_builtin_tools()

    # Initialize MCP tools
    await initialize_mcp_tools()

    client = await Client.connect(TEMPORAL_HOST)

    # Collect all activities
    activities: List = [
        llm_completion,
        check_input_safety,
        check_output_safety,
        retrieve_knowledge,
        execute_tool,
        get_tool_definitions,
        execute_agent_as_tool,
        get_agent_tool_definitions,
        execute_simple_agent,
        validate_action,
        # Validation activities
        detect_loop,
        check_hallucination,
        # Sanitization activities
        sanitize_input,
        sanitize_tool_result,
    ]

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AgentWorkflow],
        activities=activities,
    )

    return worker


async def run_worker() -> None:
    """Run the Temporal worker."""
    print(f"Starting Temporal worker...")
    print(f"  Host: {TEMPORAL_HOST}")
    print(f"  Task Queue: {TASK_QUEUE}")

    worker = await create_worker()

    # Handle graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler():
        print("\nShutdown signal received...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Run worker
    async with worker:
        print("Worker started successfully!")
        print("Waiting for tasks...")
        await shutdown_event.wait()

    # Cleanup MCP connections
    from src.mcp import shutdown_mcp_manager
    await shutdown_mcp_manager()

    print("Worker shutdown complete.")


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("\nWorker interrupted.")


if __name__ == "__main__":
    main()
