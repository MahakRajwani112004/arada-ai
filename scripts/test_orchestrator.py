#!/usr/bin/env python3
"""
Test script for Multi-Agent Orchestration.

This script demonstrates how to:
1. Create specialist agents (e.g., research, writing, coding)
2. Create an orchestrator agent that coordinates them
3. Execute the orchestrator via the API

Prerequisites:
- Temporal server running (docker compose up -d)
- API server running (python -m uvicorn src.api.app:app --reload)
- Worker running (python workers/agent_worker.py)

Usage:
    python scripts/test_orchestrator.py
"""
import asyncio
import httpx
import json

API_URL = "http://localhost:8000/api/v1"


async def create_agent(agent_data: dict) -> dict:
    """Create an agent via API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/agents",
            json=agent_data,
            timeout=30.0,
        )
        if response.status_code == 409:
            print(f"  Agent '{agent_data['id']}' already exists")
            return {"id": agent_data["id"]}
        response.raise_for_status()
        return response.json()


async def execute_agent(agent_id: str, user_input: str) -> dict:
    """Execute an agent via API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/workflow/execute",
            json={
                "agent_id": agent_id,
                "user_input": user_input,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()


async def main():
    print("=" * 60)
    print("Multi-Agent Orchestration Test")
    print("=" * 60)

    # =========================================================================
    # Step 1: Create specialist agents
    # =========================================================================
    print("\n1. Creating specialist agents...")

    # Research Agent - good at finding information
    research_agent = {
        "id": "research-agent",
        "name": "Research Specialist",
        "description": "Expert at researching topics and finding information",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Research Specialist",
            "expertise": ["research", "information gathering", "fact checking"],
            "personality": ["thorough", "analytical", "detail-oriented"],
            "communication_style": "concise and factual",
        },
        "goal": {
            "objective": "Provide accurate, well-researched information on any topic",
            "success_criteria": ["Accurate information", "Cited sources when possible"],
            "constraints": ["Only provide verified information"],
        },
        "instructions": {
            "steps": [
                "Analyze the research question",
                "Gather relevant information",
                "Verify facts",
                "Present findings clearly",
            ],
            "rules": ["Be accurate", "Cite sources"],
            "prohibited": ["Making up facts"],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 1024,
        },
    }

    # Writing Agent - good at drafting content
    writing_agent = {
        "id": "writing-agent",
        "name": "Content Writer",
        "description": "Expert at writing clear, engaging content",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Content Writer",
            "expertise": ["writing", "editing", "content creation"],
            "personality": ["creative", "articulate", "engaging"],
            "communication_style": "clear and engaging",
        },
        "goal": {
            "objective": "Create well-written, engaging content",
            "success_criteria": ["Clear prose", "Engaging style", "Proper structure"],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Understand the writing task",
                "Create an outline",
                "Write the content",
                "Review and polish",
            ],
            "rules": ["Write clearly", "Engage the reader"],
            "prohibited": [],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2048,
        },
    }

    # Code Agent - good at writing code
    code_agent = {
        "id": "code-agent",
        "name": "Code Expert",
        "description": "Expert at writing and explaining code",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Software Engineer",
            "expertise": ["programming", "debugging", "code review"],
            "personality": ["precise", "logical", "helpful"],
            "communication_style": "technical but approachable",
        },
        "goal": {
            "objective": "Write clean, efficient, well-documented code",
            "success_criteria": ["Working code", "Clear comments", "Best practices"],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Understand the requirements",
                "Design the solution",
                "Write the code",
                "Add comments and documentation",
            ],
            "rules": ["Follow best practices", "Write readable code"],
            "prohibited": [],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 2048,
        },
    }

    for agent in [research_agent, writing_agent, code_agent]:
        result = await create_agent(agent)
        print(f"  Created: {result.get('id', agent['id'])}")

    # =========================================================================
    # Step 2: Create the orchestrator agent
    # =========================================================================
    print("\n2. Creating orchestrator agent...")

    orchestrator = {
        "id": "team-orchestrator",
        "name": "Team Orchestrator",
        "description": "Coordinates specialist agents to complete complex tasks",
        "agent_type": "OrchestratorAgent",
        "role": {
            "title": "Team Lead",
            "expertise": ["coordination", "task delegation", "synthesis"],
            "personality": ["organized", "strategic", "collaborative"],
            "communication_style": "clear and directive",
        },
        "goal": {
            "objective": "Coordinate agents to complete tasks effectively",
            "success_criteria": ["Task completed", "Agents used appropriately"],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Analyze the user request",
                "Identify which specialists are needed",
                "Delegate tasks to appropriate agents",
                "Synthesize results into a coherent response",
            ],
            "rules": [
                "Use the right agent for each task",
                "Combine agent outputs effectively",
            ],
            "prohibited": [],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",  # Using stronger model for orchestration
            "temperature": 0.5,
            "max_tokens": 2048,
        },
        "orchestrator_config": {
            "mode": "llm_driven",
            "available_agents": [
                {
                    "agent_id": "research-agent",
                    "description": "Use for researching topics and gathering information",
                },
                {
                    "agent_id": "writing-agent",
                    "description": "Use for writing and content creation tasks",
                },
                {
                    "agent_id": "code-agent",
                    "description": "Use for programming and code-related tasks",
                },
            ],
            "max_parallel": 3,
            "max_depth": 2,
            "default_aggregation": "all",
        },
    }

    result = await create_agent(orchestrator)
    print(f"  Created: {result.get('id', orchestrator['id'])}")

    # =========================================================================
    # Step 3: Test the orchestrator
    # =========================================================================
    print("\n3. Testing orchestrator with a complex task...")
    print("-" * 60)

    test_prompt = """
    I need help creating a Python script that fetches weather data.
    Please:
    1. Research the best free weather APIs available
    2. Write a Python script to fetch current weather for a city
    3. Create clear documentation for the script
    """

    print(f"User: {test_prompt.strip()}")
    print("-" * 60)
    print("Executing orchestrator (this may take a minute)...")

    try:
        result = await execute_agent("team-orchestrator", test_prompt)

        print("\nOrchestrator Response:")
        print("=" * 60)
        print(result.get("content", "No content"))
        print("=" * 60)

        print("\nMetadata:")
        metadata = result.get("metadata", {})
        print(f"  Success: {result.get('success')}")
        print(f"  Iterations: {metadata.get('iterations', 'N/A')}")
        print(f"  Tool calls: {len(metadata.get('tool_calls', []))}")
        print(f"  Agent results: {len(metadata.get('agent_results', []))}")

        if metadata.get("agent_results"):
            print("\n  Agents called:")
            for ar in metadata["agent_results"]:
                agent = ar.get("agent", "unknown")
                success = ar.get("result", {}).get("success", False)
                print(f"    - {agent}: {'✓' if success else '✗'}")

    except httpx.HTTPStatusError as e:
        print(f"\nError: {e.response.status_code}")
        print(e.response.text)
    except Exception as e:
        print(f"\nError: {e}")

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
