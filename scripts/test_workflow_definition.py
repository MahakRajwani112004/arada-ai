#!/usr/bin/env python3
"""
Test script for Workflow Definition Execution.

This script demonstrates the WORKFLOW mode of the OrchestratorAgent,
where a predefined JSON workflow definition controls the execution flow.

Workflow features tested:
1. Sequential agent execution
2. Parallel agent execution
3. Conditional branching
4. Template resolution (${steps.id.output})

Prerequisites:
- Temporal server running (docker compose up -d)
- API server running (python -m uvicorn src.api.app:app --reload)
- Worker running (python workers/agent_worker.py)

Usage:
    python scripts/test_workflow_definition.py
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


async def execute_workflow(
    orchestrator_id: str,
    user_input: str,
    workflow_definition: dict,
) -> dict:
    """Execute an orchestrator with a workflow definition via API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/workflow/execute",
            json={
                "agent_id": orchestrator_id,
                "user_input": user_input,
                "workflow_definition": workflow_definition,
            },
            timeout=300.0,
        )
        response.raise_for_status()
        return response.json()


async def create_test_agents():
    """Create agents needed for workflow testing."""
    print("\n1. Creating test agents...")

    # Summarizer Agent
    summarizer = {
        "id": "summarizer",
        "name": "Summarizer",
        "description": "Summarizes text into key points",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Summarizer",
            "expertise": ["summarization"],
            "personality": ["concise"],
            "communication_style": "brief",
        },
        "goal": {
            "objective": "Summarize content into key bullet points",
            "success_criteria": ["Clear summary"],
            "constraints": [],
        },
        "instructions": {
            "steps": ["Read the input", "Extract key points", "Return bullet points"],
            "rules": ["Be concise", "Max 5 bullet points"],
            "prohibited": [],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 512,
        },
    }

    # Fact Checker Agent
    fact_checker = {
        "id": "fact-checker",
        "name": "Fact Checker",
        "description": "Verifies facts and identifies potential issues",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Fact Checker",
            "expertise": ["verification", "analysis"],
            "personality": ["skeptical", "thorough"],
            "communication_style": "analytical",
        },
        "goal": {
            "objective": "Identify potential factual issues",
            "success_criteria": ["Accurate analysis"],
            "constraints": [],
        },
        "instructions": {
            "steps": ["Review claims", "Identify issues", "Rate confidence"],
            "rules": ["Be objective"],
            "prohibited": [],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 512,
        },
    }

    # Translator Agent
    translator = {
        "id": "translator",
        "name": "Translator",
        "description": "Translates text to different languages",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Translator",
            "expertise": ["translation"],
            "personality": ["accurate"],
            "communication_style": "precise",
        },
        "goal": {
            "objective": "Translate text accurately",
            "success_criteria": ["Accurate translation"],
            "constraints": [],
        },
        "instructions": {
            "steps": ["Identify language", "Translate", "Verify"],
            "rules": ["Preserve meaning"],
            "prohibited": [],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 1024,
        },
    }

    # Classifier Agent (for conditional branching)
    classifier = {
        "id": "classifier",
        "name": "Content Classifier",
        "description": "Classifies content type (news, opinion, creative)",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Classifier",
            "expertise": ["classification"],
            "personality": ["precise"],
            "communication_style": "direct",
        },
        "goal": {
            "objective": "Classify content into: news, opinion, creative",
            "success_criteria": ["Accurate classification"],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Read the content",
                "Determine type",
                "Return ONLY one word: news, opinion, or creative",
            ],
            "rules": ["Only return one word: news, opinion, or creative"],
            "prohibited": ["Any other response"],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 10,
        },
    }

    # Workflow Orchestrator (empty shell - uses workflow_definition)
    orchestrator = {
        "id": "workflow-orchestrator",
        "name": "Workflow Orchestrator",
        "description": "Executes predefined workflow definitions",
        "agent_type": "OrchestratorAgent",
        "role": {
            "title": "Workflow Executor",
            "expertise": ["orchestration"],
            "personality": ["systematic"],
            "communication_style": "structured",
        },
        "goal": {
            "objective": "Execute workflow definitions",
            "success_criteria": ["Workflow completed"],
            "constraints": [],
        },
        "instructions": {
            "steps": ["Execute workflow"],
            "rules": [],
            "prohibited": [],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "max_tokens": 2048,
        },
        "orchestrator_config": {
            "mode": "workflow",  # Will be overridden by workflow_definition
            "available_agents": [],
            "max_parallel": 5,
            "max_depth": 3,
        },
    }

    agents = [summarizer, fact_checker, translator, classifier, orchestrator]
    for agent in agents:
        result = await create_agent(agent)
        print(f"  Created: {result.get('id', agent['id'])}")


async def test_sequential_workflow():
    """Test a simple sequential workflow: summarize -> fact check."""
    print("\n" + "=" * 60)
    print("TEST 1: Sequential Workflow")
    print("=" * 60)

    workflow_definition = {
        "id": "sequential-test",
        "name": "Summarize and Verify",
        "steps": [
            {
                "id": "summarize",
                "type": "agent",
                "agent_id": "summarizer",
                "input": "${user_input}",
            },
            {
                "id": "verify",
                "type": "agent",
                "agent_id": "fact-checker",
                "input": "Please verify these claims:\n${steps.summarize.output}",
            },
        ],
        "entry_step": "summarize",
    }

    user_input = """
    The Eiffel Tower was built in 1889 for the World's Fair. It stands 330 meters tall
    and was the tallest man-made structure in the world until the Chrysler Building was
    completed in 1930. Over 7 million people visit it each year.
    """

    print(f"\nInput: {user_input.strip()[:100]}...")
    print("\nWorkflow: summarize -> fact-check")
    print("-" * 40)

    try:
        result = await execute_workflow(
            "workflow-orchestrator",
            user_input,
            workflow_definition,
        )

        print("\nResult:")
        print(result.get("content", "No content"))

        metadata = result.get("metadata", {})
        print(f"\nSteps executed: {metadata.get('steps_executed', [])}")
        print(f"Success: {result.get('success')}")

    except Exception as e:
        print(f"Error: {e}")


async def test_parallel_workflow():
    """Test parallel workflow: translate to multiple languages at once."""
    print("\n" + "=" * 60)
    print("TEST 2: Parallel Workflow")
    print("=" * 60)

    workflow_definition = {
        "id": "parallel-test",
        "name": "Multi-Language Summary",
        "steps": [
            {
                "id": "summarize",
                "type": "agent",
                "agent_id": "summarizer",
                "input": "${user_input}",
            },
            {
                "id": "translate_parallel",
                "type": "parallel",
                "branches": [
                    {
                        "id": "spanish",
                        "agent_id": "translator",
                        "input": "Translate to Spanish:\n${steps.summarize.output}",
                    },
                    {
                        "id": "french",
                        "agent_id": "translator",
                        "input": "Translate to French:\n${steps.summarize.output}",
                    },
                ],
                "aggregation": "all",
            },
        ],
        "entry_step": "summarize",
    }

    user_input = "Python is a programming language known for its simplicity and readability."

    print(f"\nInput: {user_input}")
    print("\nWorkflow: summarize -> [translate to Spanish | translate to French]")
    print("-" * 40)

    try:
        result = await execute_workflow(
            "workflow-orchestrator",
            user_input,
            workflow_definition,
        )

        print("\nResult:")
        print(result.get("content", "No content"))

        metadata = result.get("metadata", {})
        print(f"\nSteps executed: {metadata.get('steps_executed', [])}")

    except Exception as e:
        print(f"Error: {e}")


async def test_conditional_workflow():
    """Test conditional workflow: classify then route to different handlers."""
    print("\n" + "=" * 60)
    print("TEST 3: Conditional Workflow")
    print("=" * 60)

    workflow_definition = {
        "id": "conditional-test",
        "name": "Content-Aware Processing",
        "steps": [
            {
                "id": "classify",
                "type": "agent",
                "agent_id": "classifier",
                "input": "Classify this content:\n${user_input}",
            },
            {
                "id": "route",
                "type": "conditional",
                "condition_source": "${steps.classify.output}",
                "branches": {
                    "news": "news_handler",
                    "opinion": "opinion_handler",
                    "creative": "creative_handler",
                },
                "default": "default_handler",
            },
            {
                "id": "news_handler",
                "type": "agent",
                "agent_id": "fact-checker",
                "input": "Verify this news:\n${user_input}",
            },
            {
                "id": "opinion_handler",
                "type": "agent",
                "agent_id": "summarizer",
                "input": "Summarize the key arguments:\n${user_input}",
            },
            {
                "id": "creative_handler",
                "type": "agent",
                "agent_id": "summarizer",
                "input": "Describe the creative elements:\n${user_input}",
            },
            {
                "id": "default_handler",
                "type": "agent",
                "agent_id": "summarizer",
                "input": "Summarize:\n${user_input}",
            },
        ],
        "entry_step": "classify",
    }

    # Test with news content
    user_input = """
    Breaking: Scientists at CERN have announced the discovery of a new particle
    that could explain dark matter. The finding, published in Nature, has been
    independently verified by three other research teams.
    """

    print(f"\nInput (news): {user_input.strip()[:80]}...")
    print("\nWorkflow: classify -> route(news|opinion|creative) -> handler")
    print("-" * 40)

    try:
        result = await execute_workflow(
            "workflow-orchestrator",
            user_input,
            workflow_definition,
        )

        print("\nResult:")
        print(result.get("content", "No content"))

        metadata = result.get("metadata", {})
        steps_executed = metadata.get("steps_executed", [])
        step_results = metadata.get("step_results", {})

        print(f"\nSteps executed: {steps_executed}")

        if "classify" in step_results:
            print(f"Classification: {step_results['classify'].get('output', 'N/A')}")
        if "route" in step_results:
            print(f"Selected branch: {step_results['route'].get('selected_branch', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")


async def test_loop_workflow():
    """Test loop workflow: iteratively refine content until quality threshold."""
    print("\n" + "=" * 60)
    print("TEST 4: Loop Workflow")
    print("=" * 60)

    # First create a refiner agent for this test
    refiner = {
        "id": "refiner",
        "name": "Content Refiner",
        "description": "Improves and expands content iteratively",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Refiner",
            "expertise": ["editing", "improvement"],
            "personality": ["meticulous"],
            "communication_style": "constructive",
        },
        "goal": {
            "objective": "Improve content quality with each iteration",
            "success_criteria": ["Better content each time"],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Read the content",
                "Identify one area for improvement",
                "Make that improvement",
                "Return the improved version",
            ],
            "rules": ["Make exactly one improvement per iteration"],
            "prohibited": [],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "max_tokens": 512,
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/agents",
            json=refiner,
            timeout=30.0,
        )
        if response.status_code == 409:
            print("  Refiner agent already exists")
        else:
            response.raise_for_status()
            print("  Created refiner agent")

    workflow_definition = {
        "id": "loop-test",
        "name": "Iterative Refinement",
        "steps": [
            {
                "id": "refine_loop",
                "type": "loop",
                "max_iterations": 3,
                "exit_condition": "false",  # Always run max iterations
                "steps": [
                    {
                        "id": "refine_step",
                        "agent_id": "refiner",
                        "input": "Improve this content (iteration ${loop_iteration}):\n${user_input}",
                    },
                ],
            },
            {
                "id": "final_summary",
                "type": "agent",
                "agent_id": "summarizer",
                "input": "Summarize the key improvements made:\n${steps.refine_loop.output}",
            },
        ],
        "entry_step": "refine_loop",
    }

    user_input = "AI is good."

    print(f"\nInput: '{user_input}'")
    print("\nWorkflow: loop(refine x 3) -> summarize improvements")
    print("-" * 40)

    try:
        result = await execute_workflow(
            "workflow-orchestrator",
            user_input,
            workflow_definition,
        )

        print("\nResult:")
        print(result.get("content", "No content"))

        metadata = result.get("metadata", {})
        steps_executed = metadata.get("steps_executed", [])
        step_results = metadata.get("step_results", {})

        print(f"\nSteps executed: {steps_executed}")

        if "refine_loop" in step_results:
            loop_result = step_results["refine_loop"]
            print(f"Loop iterations completed: {loop_result.get('iterations_completed', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")


async def test_error_handling_workflow():
    """Test workflow error handling with on_error options."""
    print("\n" + "=" * 60)
    print("TEST 5: Error Handling Workflow")
    print("=" * 60)

    workflow_definition = {
        "id": "error-test",
        "name": "Error Handling Test",
        "steps": [
            {
                "id": "step1",
                "type": "agent",
                "agent_id": "summarizer",
                "input": "${user_input}",
            },
            {
                "id": "step2_may_fail",
                "type": "agent",
                "agent_id": "non-existent-agent",  # This will fail
                "input": "${steps.step1.output}",
                "on_error": "skip",  # Skip on error and continue
            },
            {
                "id": "step3_fallback",
                "type": "agent",
                "agent_id": "summarizer",
                "input": "Create a final summary: ${steps.step1.output}",
            },
        ],
        "entry_step": "step1",
    }

    user_input = "Testing error handling in workflows."

    print(f"\nInput: '{user_input}'")
    print("\nWorkflow: step1 -> step2(skip on error) -> step3")
    print("-" * 40)

    try:
        result = await execute_workflow(
            "workflow-orchestrator",
            user_input,
            workflow_definition,
        )

        print("\nResult:")
        print(result.get("content", "No content"))

        metadata = result.get("metadata", {})
        print(f"\nSteps executed: {metadata.get('steps_executed', [])}")
        print(f"Success: {result.get('success')}")

    except Exception as e:
        print(f"Error (expected): {e}")


async def main():
    print("=" * 60)
    print("Workflow Definition Execution Test")
    print("=" * 60)
    print("\nThis test demonstrates WORKFLOW mode orchestration")
    print("where a JSON definition controls the execution flow.")

    # Create test agents
    await create_test_agents()

    # Run tests
    await test_sequential_workflow()
    await test_parallel_workflow()
    await test_conditional_workflow()
    await test_loop_workflow()
    await test_error_handling_workflow()

    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
