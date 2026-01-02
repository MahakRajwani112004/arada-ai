#!/usr/bin/env python3
"""Seed the NDA Email Sender agent and NDA workflow into the database.

Usage:
    python scripts/seed_nda_email_workflow.py

This script creates:
1. NDA Email Sender agent - composes and sends professional emails with NDA documents
2. NDA Generation and Email Workflow - orchestrates NDA generation and email delivery

Prerequisites:
- Run seed_nda_skill_and_agent.py first to create the NDA Assistant agent
- Run upload_nda_template.py to upload the NDA template to MinIO
- Gmail MCP server should be configured for email sending
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from src.storage.database import get_session, init_database
from src.storage.models import AgentModel, WorkflowModel, UserModel


async def seed_email_agent_and_workflow():
    """Seed the NDA email sender agent and workflow into the database."""

    # Load configurations
    data_dir = Path(__file__).parent.parent / "data"
    agent_path = data_dir / "agents" / "nda_email_sender_agent.json"
    workflow_path = data_dir / "workflows" / "nda_generation_and_email_workflow.json"

    with open(agent_path) as f:
        agent_data = json.load(f)

    with open(workflow_path) as f:
        workflow_data = json.load(f)

    # Initialize database
    await init_database()

    async for session in get_session():
        try:
            # Get the superuser to use as owner
            result = await session.execute(
                select(UserModel).where(UserModel.is_superuser == True)
            )
            superuser = result.scalar_one_or_none()

            if not superuser:
                print("ERROR: No superuser found. Please create a superuser first.")
                return

            user_id = superuser.id
            print(f"Using user: {superuser.email} (ID: {user_id})")

            # Check if NDA Assistant agent exists (prerequisite)
            nda_agent_result = await session.execute(
                select(AgentModel).where(AgentModel.id == "agent-nda-assistant")
            )
            nda_agent = nda_agent_result.scalar_one_or_none()

            if not nda_agent:
                print("WARNING: NDA Assistant agent (agent-nda-assistant) not found.")
                print("Please run seed_nda_skill_and_agent.py first.")
                print("Continuing anyway, but the workflow may not work correctly.\n")

            # ========== Create Email Sender Agent ==========
            existing_agent = await session.execute(
                select(AgentModel).where(AgentModel.id == agent_data["id"])
            )
            existing = existing_agent.scalar_one_or_none()

            if existing:
                print(f"Agent '{agent_data['id']}' already exists. Deleting and recreating...")
                await session.delete(existing)
                await session.flush()

            agent_model = AgentModel(
                id=agent_data["id"],
                user_id=user_id,
                name=agent_data["name"],
                description=agent_data["description"],
                agent_type=agent_data["agent_type"],
                config_json=agent_data,
                is_active=True,
            )
            session.add(agent_model)
            print(f"Created agent: {agent_data['id']}")

            # ========== Create Workflow ==========
            existing_workflow = await session.execute(
                select(WorkflowModel).where(WorkflowModel.id == workflow_data["id"])
            )
            existing = existing_workflow.scalar_one_or_none()

            if existing:
                print(f"Workflow '{workflow_data['id']}' already exists. Deleting and recreating...")
                await session.delete(existing)
                await session.flush()

            # Extract workflow definition (steps, entry_step, context)
            workflow_definition = {
                "id": workflow_data["id"],
                "name": workflow_data.get("name"),
                "description": workflow_data.get("description"),
                "steps": workflow_data["steps"],
                "entry_step": workflow_data.get("entry_step"),
                "context": workflow_data.get("context", {}),
            }

            workflow_model = WorkflowModel(
                id=workflow_data["id"],
                user_id=user_id,
                name=workflow_data["name"],
                description=workflow_data.get("description", ""),
                category=workflow_data.get("category", "general"),
                tags=workflow_data.get("tags", []),
                is_template=False,
                definition_json=workflow_definition,
                version=1,
                is_active=True,
                is_published=True,
                created_by=superuser.email,
            )
            session.add(workflow_model)
            print(f"Created workflow: {workflow_data['id']}")

            await session.commit()

            print("\n" + "=" * 60)
            print("Successfully seeded NDA Email workflow!")
            print("=" * 60)
            print(f"\nAgent ID: {agent_data['id']}")
            print(f"Workflow ID: {workflow_data['id']}")
            print("\nWorkflow Steps:")
            for i, step in enumerate(workflow_data["steps"], 1):
                print(f"  {i}. {step['name']} (agent: {step['agent_id']})")

            print("\n" + "-" * 60)
            print("PREREQUISITES:")
            print("-" * 60)
            print("1. Run seed_nda_skill_and_agent.py (NDA Assistant agent)")
            print("2. Run upload_nda_template.py (NDA DOCX template)")
            print("3. Start Outlook Email MCP server on port 8005:")
            print("   PORT=8005 PYTHONPATH=. .venv/bin/python mcp_servers/outlook-email/server.py")
            print("4. Configure Microsoft OAuth credentials in the application")

            print("\n" + "-" * 60)
            print("USAGE:")
            print("-" * 60)
            print("To test the workflow, provide company details like:")
            print('  "Create an NDA for Acme Corp at 123 Main St, for partnership')
            print('   exploration. Effective date: January 15, 2025. Signatory:')
            print('   John Smith, CEO. Send to john@acmecorp.com"')

        except Exception as e:
            await session.rollback()
            print(f"Error seeding data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_email_agent_and_workflow())
