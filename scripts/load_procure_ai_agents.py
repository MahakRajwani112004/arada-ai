#!/usr/bin/env python3
"""Script to load Procure AI agent configurations into the platform."""

import asyncio
import json
from pathlib import Path

import httpx


async def load_procure_ai_agents(
    api_base_url: str = "http://localhost:8000",
    config_path: str | None = None,
):
    """Load Procure AI agents from configuration file.

    Args:
        api_base_url: Base URL of the MagoneAI API
        config_path: Path to the agent configuration JSON file
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "src/agents/configs/procure_ai_agents.json"

    # Load configuration
    with open(config_path) as f:
        config = json.load(f)

    agents = config.get("agents", [])
    skills = config.get("skills", [])
    workflows = config.get("workflows", [])

    print(f"Loading {len(agents)} Procure AI agents...")
    print(f"Loading {len(skills)} industry-specific skills...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Load skills first (agents depend on them)
        for skill in skills:
            try:
                # Check if skill exists
                response = await client.get(f"{api_base_url}/api/v1/skills/{skill['id']}")

                if response.status_code == 200:
                    # Update existing skill
                    response = await client.put(
                        f"{api_base_url}/api/v1/skills/{skill['id']}",
                        json=skill,
                    )
                    if response.status_code == 200:
                        print(f"  ✓ Updated skill: {skill['id']}")
                    else:
                        print(f"  ✗ Failed to update skill {skill['id']}: {response.text}")
                else:
                    # Create new skill
                    response = await client.post(
                        f"{api_base_url}/api/v1/skills",
                        json=skill,
                    )
                    if response.status_code in (200, 201):
                        print(f"  ✓ Created skill: {skill['id']}")
                    else:
                        print(f"  ✗ Failed to create skill {skill['id']}: {response.text}")

            except Exception as e:
                print(f"  ✗ Error loading skill {skill['id']}: {e}")

        print(f"\n{'='*50}\n")

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

    print(f"\n{'='*50}")
    print(f"Loaded {len(agents)} agents and {len(skills)} skills successfully!")
    print("\nProcure AI agents available:")
    print("  - procure-ai-router: Routes to industry-specific generators")
    print("  - procure-ai-orchestrator: Multi-industry coordination")
    print("  - procure-ai-oil: Oil industry RFP generator")
    print("  - procure-ai-gas: Gas/LNG industry RFP generator")
    print("  - procure-ai-construction: Construction industry RFP generator")
    print("  - procure-ai-document-generator: Final document generation")

    print("\nIndustry Skills loaded:")
    print("  - oil-industry-rfp: Oil sector terminology & standards")
    print("  - gas-industry-rfp: Gas/LNG sector terminology & standards")
    print("  - construction-industry-rfp: Construction terminology & standards")

    print("\n" + "="*50)
    print("HOW TO USE PROCURE AI")
    print("="*50)
    print("\nOption 1: Direct API call to the orchestrator:")
    print(f"  POST {api_base_url}/api/v1/agents/procure-ai-orchestrator/execute")
    print('''  {
    "user_input": "Generate RFP for offshore drilling equipment, 5000m depth capability, $50M budget"
  }''')

    print("\nOption 2: Use industry-specific agent directly:")
    print(f"  POST {api_base_url}/api/v1/agents/procure-ai-oil/execute")
    print('''  {
    "user_input": "Need RFP for pipeline construction, 100km, 36 inch diameter, sour gas service"
  }''')

    print("\nOption 3: Use the router for auto-classification:")
    print(f"  POST {api_base_url}/api/v1/agents/procure-ai-router/execute")
    print('''  {
    "user_input": "Building new LNG terminal, 5 MTPA capacity"
  }''')

    print("\n" + "="*50)
    print("EXAMPLE PROMPTS BY INDUSTRY")
    print("="*50)

    print("\nOIL INDUSTRY:")
    print("  - 'Need drilling rig for offshore platform, 5000m depth, $50M budget'")
    print("  - 'RFP for pipeline construction, 200km, crude oil transport'")
    print("  - 'Equipment for new refinery expansion, crude distillation unit'")

    print("\nGAS INDUSTRY:")
    print("  - 'LNG export terminal equipment, 5 MTPA capacity'")
    print("  - 'Gas processing plant, 500 MMSCFD, H2S removal'")
    print("  - 'Compressor station for gas pipeline, 3000 HP'")

    print("\nCONSTRUCTION:")
    print("  - 'Warehouse 10000 sqm, concrete structure, 12 month timeline'")
    print("  - 'Office building 20 floors, downtown location, LEED certified'")
    print("  - 'Road construction 50km, asphalt, desert conditions'")


async def test_procure_ai(api_base_url: str = "http://localhost:8000"):
    """Run a test query against Procure AI."""

    test_prompt = """
    We need equipment for a new offshore drilling platform:
    - Location: Persian Gulf
    - Water depth: 50 meters
    - Drilling depth capability: 5,000 meters
    - Budget: approximately $50 million USD
    - Timeline: Need delivery within 18 months
    - Special requirements: H2S service rated equipment
    """

    print("\n" + "="*50)
    print("RUNNING TEST QUERY")
    print("="*50)
    print(f"\nTest prompt:\n{test_prompt}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{api_base_url}/api/v1/agents/procure-ai-oil/execute",
                json={"user_input": test_prompt},
            )

            if response.status_code == 200:
                result = response.json()
                print("\n✓ Test successful!")
                print(f"\nResponse preview (first 500 chars):")
                content = result.get("content", result.get("output", str(result)))
                print(content[:500] + "..." if len(content) > 500 else content)
            else:
                print(f"\n✗ Test failed: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"\n✗ Test error: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load Procure AI agents")
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
        "--test",
        action="store_true",
        help="Run a test query after loading agents",
    )

    args = parser.parse_args()

    asyncio.run(load_procure_ai_agents(args.api_url, args.config))

    if args.test:
        asyncio.run(test_procure_ai(args.api_url))
