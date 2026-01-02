#!/usr/bin/env python3
"""Seed the NDA Generator skill and NDA Assistant agent into the database.

Usage:
    python scripts/seed_nda_skill_and_agent.py

This script creates:
1. NDA Generator skill configured to use DOCX template from storage
2. NDA Assistant agent configured to use the skill

Note: Run upload_nda_template.py first to upload the DOCX template to MinIO.
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
from src.storage.models import SkillModel, AgentModel, UserModel


async def seed_skill_and_agent():
    """Seed the NDA skill and agent into the database."""

    # Load configurations
    data_dir = Path(__file__).parent.parent / "data"
    skill_path = data_dir / "skills" / "nda_generator_skill.json"
    agent_path = data_dir / "agents" / "nda_assistant_agent.json"

    with open(skill_path) as f:
        skill_data = json.load(f)

    with open(agent_path) as f:
        agent_data = json.load(f)

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

            # Check if skill exists
            existing_skill = await session.execute(
                select(SkillModel).where(SkillModel.id == skill_data["id"])
            )
            existing = existing_skill.scalar_one_or_none()

            if existing:
                print(f"Skill '{skill_data['id']}' already exists. Updating...")
                existing.name = skill_data["name"]
                existing.description = skill_data["description"]
                existing.definition_json = skill_data["definition"]
                existing.updated_at = datetime.now(tz=None)
            else:
                skill_model = SkillModel(
                    id=skill_data["id"],
                    user_id=user_id,
                    name=skill_data["name"],
                    description=skill_data["description"],
                    category=skill_data["category"],
                    tags=skill_data["tags"],
                    definition_json=skill_data["definition"],
                    version=1,
                    status="published",
                )
                session.add(skill_model)
                print(f"Created skill: {skill_data['id']}")

            # Check if agent exists
            existing_agent = await session.execute(
                select(AgentModel).where(AgentModel.id == agent_data["id"])
            )
            existing = existing_agent.scalar_one_or_none()

            if existing:
                print(f"Agent '{agent_data['id']}' already exists. Deleting and recreating...")
                await session.delete(existing)
                await session.flush()

            # Create new agent
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

            await session.commit()
            print("\nSuccessfully seeded NDA skill and agent!")
            print(f"\nSkill ID: {skill_data['id']}")
            print(f"Agent ID: {agent_data['id']}")
            print("\nNOTE: Make sure to run upload_nda_template.py to upload the DOCX template to MinIO.")
            print("You can now use the NDA Assistant agent to generate NDAs.")

        except Exception as e:
            await session.rollback()
            print(f"Error seeding data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_skill_and_agent())
