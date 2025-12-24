#!/usr/bin/env python3
"""Script to load Arada AI agent configurations into the platform."""

import asyncio
import json
from pathlib import Path

import httpx


async def load_arada_agents(
    api_base_url: str = "http://localhost:8000",
    config_path: str | None = None,
):
    """Load Arada AI agents from configuration file.

    Args:
        api_base_url: Base URL of the MagoneAI API
        config_path: Path to the agent configuration JSON file
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "src/agents/configs/arada_ai_agents.json"

    # Load configuration
    with open(config_path) as f:
        config = json.load(f)

    agents = config.get("agents", [])
    workflows = config.get("workflows", [])

    print(f"Loading {len(agents)} Arada AI agents...")

    async with httpx.AsyncClient() as client:
        # Load each agent
        for agent in agents:
            try:
                # Check if agent exists
                response = await client.get(f"{api_base_url}/api/v1/agents/{agent['id']}")

                if response.status_code == 200:
                    # Update existing agent
                    response = await client.put(
                        f"{api_base_url}/api/v1/agents/{agent['id']}",
                        json=agent,
                    )
                    if response.status_code == 200:
                        print(f"  ✓ Updated agent: {agent['id']}")
                    else:
                        print(f"  ✗ Failed to update {agent['id']}: {response.text}")
                else:
                    # Create new agent
                    response = await client.post(
                        f"{api_base_url}/api/v1/agents",
                        json=agent,
                    )
                    if response.status_code in (200, 201):
                        print(f"  ✓ Created agent: {agent['id']}")
                    else:
                        print(f"  ✗ Failed to create {agent['id']}: {response.text}")

            except Exception as e:
                print(f"  ✗ Error loading {agent['id']}: {e}")

    print(f"\nLoaded {len(agents)} agents successfully!")
    print("\nArada AI agents available:")
    print("  - arada-router: Entry point for all queries")
    print("  - arada-orchestrator: Multi-agent coordination")
    print("  - arada-kpi-analyzer: Dynamic KPI calculation")
    print("  - arada-root-cause-agent: Root cause analysis")
    print("  - arada-trend-analyzer: Time-series trends")
    print("  - arada-benchmark-agent: Comparative analysis")
    print("  - arada-scenario-agent: What-if simulations")
    print("  - arada-risk-agent: Risk identification")
    print("  - arada-executive-reporter: Executive summaries")
    print("  - arada-data-agent: Data queries")

    print("\nTo use Arada AI, send requests to:")
    print(f"  POST {api_base_url}/api/v1/workflow/execute")
    print('  {"agent_id": "arada-orchestrator", "user_input": "How is DAMAC Bay performing?"}')


async def initialize_data_service(csv_path: str | None = None):
    """Initialize the real estate data service with CSV data.

    Args:
        csv_path: Path to the real estate bookings CSV file
    """
    from src.services.real_estate_data_service import initialize_real_estate_service

    if csv_path:
        print(f"Loading real estate data from: {csv_path}")
        await initialize_real_estate_service(csv_path)
        print("  ✓ Data service initialized")
    else:
        print("No CSV path provided. Using database connection.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load Arada AI agents")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the MagoneAI API",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to agent configuration JSON file",
    )
    parser.add_argument(
        "--data-csv",
        default=None,
        help="Path to real estate bookings CSV file",
    )

    args = parser.parse_args()

    asyncio.run(load_arada_agents(args.api_url, args.config))
