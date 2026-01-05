"""
Register Arada POC Agents

This script registers all Arada POC agents to the file-based storage.
Can work standalone without database.

Usage:
    python scripts/register_arada_agents.py register
    python scripts/register_arada_agents.py list
    python scripts/register_arada_agents.py delete
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.arada_poc_agents import ARADA_POC_AGENTS, get_all_agent_ids
from src.storage.agent_repository import FileAgentRepository


async def register_agents(base_path: str = "./data/agents"):
    """Register all Arada POC agents to file storage."""

    print("=" * 60)
    print("ARADA POC - Agent Registration")
    print("=" * 60)
    print(f"Storage path: {base_path}")
    print()

    repo = FileAgentRepository(base_path=base_path)

    registered = []
    updated = []
    errors = []

    for agent_config in ARADA_POC_AGENTS:
        try:
            # Check if agent already exists
            existing = await repo.get(agent_config.id)

            if existing:
                # Update existing agent
                await repo.save(agent_config)
                updated.append(agent_config.id)
                print(f"[UPDATE] {agent_config.name}")
                print(f"         ID: {agent_config.id}")
                print(f"         Type: {agent_config.agent_type.value}")
            else:
                # Create new agent
                await repo.save(agent_config)
                registered.append(agent_config.id)
                print(f"[CREATE] {agent_config.name}")
                print(f"         ID: {agent_config.id}")
                print(f"         Type: {agent_config.agent_type.value}")

            print()

        except Exception as e:
            errors.append((agent_config.id, str(e)))
            print(f"[ERROR] {agent_config.name}: {e}")
            print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created: {len(registered)} agents")
    print(f"Updated: {len(updated)} agents")
    print(f"Errors:  {len(errors)} agents")
    print()

    if errors:
        print("Failed agents:")
        for agent_id, error in errors:
            print(f"  - {agent_id}: {error}")
        print()

    print("=" * 60)
    print("REGISTERED AGENT IDs")
    print("=" * 60)
    print()
    for agent in ARADA_POC_AGENTS:
        print(f"  {agent.id}")
    print()

    return len(errors) == 0


async def list_agents(base_path: str = "./data/agents"):
    """List all registered agents."""

    print("=" * 60)
    print("REGISTERED AGENTS")
    print("=" * 60)
    print()

    repo = FileAgentRepository(base_path=base_path)
    agents = await repo.list()

    if not agents:
        print("No agents registered yet.")
        print(f"Run: python scripts/register_arada_agents.py register")
        return

    for agent in agents:
        is_arada = "[ARADA]" if agent.id.startswith("arada_") else ""
        print(f"  {agent.id} {is_arada}")
        print(f"    Name: {agent.name}")
        print(f"    Type: {agent.agent_type.value}")
        if agent.orchestrator_config:
            print(f"    Mode: {agent.orchestrator_config.mode.value}")
            print(f"    Child Agents: {len(agent.orchestrator_config.available_agents)}")
        if agent.tools:
            tool_names = [t.tool_id for t in agent.tools]
            print(f"    Tools: {', '.join(tool_names)}")
        print()


async def delete_agents(base_path: str = "./data/agents"):
    """Delete all Arada POC agents."""

    print("Deleting Arada POC agents...")
    print()

    repo = FileAgentRepository(base_path=base_path)

    for agent_id in get_all_agent_ids():
        try:
            deleted = await repo.delete(agent_id)
            if deleted:
                print(f"[DELETE] {agent_id}")
            else:
                print(f"[SKIP] {agent_id} (not found)")
        except Exception as e:
            print(f"[ERROR] {agent_id}: {e}")

    print()
    print("Done.")


async def show_agent(agent_id: str, base_path: str = "./data/agents"):
    """Show details of a specific agent."""

    repo = FileAgentRepository(base_path=base_path)
    agent = await repo.get(agent_id)

    if not agent:
        print(f"Agent '{agent_id}' not found.")
        return

    print("=" * 60)
    print(f"AGENT: {agent.name}")
    print("=" * 60)
    print()
    print(f"ID: {agent.id}")
    print(f"Type: {agent.agent_type.value}")
    print(f"Description: {agent.description}")
    print()
    print("Role:")
    print(f"  Title: {agent.role.title}")
    print(f"  Expertise: {', '.join(agent.role.expertise)}")
    print()
    print("Goal:")
    print(f"  Objective: {agent.goal.objective}")
    print()

    if agent.tools:
        print("Tools:")
        for tool in agent.tools:
            print(f"  - {tool.tool_id}")
    print()

    if agent.orchestrator_config:
        print("Orchestrator Config:")
        print(f"  Mode: {agent.orchestrator_config.mode.value}")
        print(f"  Max Parallel: {agent.orchestrator_config.max_parallel}")
        print(f"  Child Agents:")
        for ref in agent.orchestrator_config.available_agents:
            print(f"    - {ref.agent_id} ({ref.alias})")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage Arada POC agents")
    parser.add_argument(
        "action",
        choices=["register", "delete", "list", "show"],
        default="register",
        nargs="?",
        help="Action to perform (default: register)"
    )
    parser.add_argument(
        "--path",
        default="./data/agents",
        help="Base path for agent storage (default: ./data/agents)"
    )
    parser.add_argument(
        "--agent-id",
        help="Agent ID for 'show' action"
    )

    args = parser.parse_args()

    if args.action == "register":
        success = asyncio.run(register_agents(args.path))
        sys.exit(0 if success else 1)
    elif args.action == "delete":
        asyncio.run(delete_agents(args.path))
    elif args.action == "list":
        asyncio.run(list_agents(args.path))
    elif args.action == "show":
        if not args.agent_id:
            print("Error: --agent-id required for 'show' action")
            sys.exit(1)
        asyncio.run(show_agent(args.agent_id, args.path))
