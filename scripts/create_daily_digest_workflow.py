#!/usr/bin/env python3
"""
Daily Calendar Digest Workflow

This script creates a multi-agent workflow that:
1. Fetches calendar events
2. Creates humanized summaries
3. Cross-checks for hallucinations/accuracy
4. Composes and sends an email digest

Agents:
- calendar-fetcher: Gets calendar data via MCP
- summarizer: Creates humanized summaries
- fact-checker: Verifies accuracy, catches hallucinations
- email-composer: Creates professional email content
- email-sender: Sends email via Gmail MCP
- daily-digest-orchestrator: Coordinates the workflow

Prerequisites:
- MCP servers registered (google-calendar, google-gmail)
- OAuth configured for Google APIs
- Temporal, API, and Worker running

Usage:
    python scripts/create_daily_digest_workflow.py
"""
import asyncio
import httpx
import json
from datetime import datetime

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
            print(f"  ⚠ Agent '{agent_data['id']}' already exists, skipping...")
            return {"id": agent_data["id"], "exists": True}
        response.raise_for_status()
        print(f"  ✓ Created: {agent_data['id']}")
        return response.json()


async def delete_agent(agent_id: str) -> bool:
    """Delete an agent."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{API_URL}/agents/{agent_id}")
        return response.status_code == 204


async def execute_agent(agent_id: str, user_input: str) -> dict:
    """Execute an agent via API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/workflow/execute",
            json={
                "agent_id": agent_id,
                "user_input": user_input,
            },
            timeout=300.0,  # 5 min timeout for complex workflows
        )
        response.raise_for_status()
        return response.json()


# =============================================================================
# Agent Definitions
# =============================================================================

AGENTS = {
    # -------------------------------------------------------------------------
    # 1. Calendar Fetcher - Gets calendar data using MCP tool
    # -------------------------------------------------------------------------
    "calendar-fetcher": {
        "id": "calendar-fetcher",
        "name": "Calendar Fetcher",
        "description": "Fetches calendar events using Google Calendar API",
        "agent_type": "ToolAgent",
        "role": {
            "title": "Calendar Data Specialist",
            "expertise": ["calendar management", "event retrieval", "scheduling"],
            "personality": ["precise", "thorough", "organized"],
            "communication_style": "structured and data-focused",
        },
        "goal": {
            "objective": "Retrieve calendar events accurately and completely",
            "success_criteria": [
                "All events fetched for requested period",
                "Event details preserved accurately",
            ],
            "constraints": ["Only fetch data, don't modify calendar"],
        },
        "instructions": {
            "steps": [
                "Determine the date range to fetch (default: today and tomorrow)",
                "Call list_events tool with appropriate parameters",
                "Format the results in a clear, structured way",
                "Include all relevant details: title, time, attendees, location",
            ],
            "rules": [
                "Always include event times in readable format",
                "Group events by date if multiple days",
                "Note if there are no events",
            ],
            "prohibited": ["Creating or modifying events"],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 2048,
        },
        "tools": [
            {"tool_id": "mcp:google-calendar:list_events", "enabled": True},
        ],
    },

    # -------------------------------------------------------------------------
    # 2. Summarizer - Creates humanized summaries
    # -------------------------------------------------------------------------
    "summarizer": {
        "id": "summarizer",
        "name": "Meeting Summarizer",
        "description": "Creates humanized, natural summaries of calendar events",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Communication Specialist",
            "expertise": ["writing", "summarization", "human communication"],
            "personality": ["warm", "clear", "professional", "engaging"],
            "communication_style": "conversational yet professional",
        },
        "goal": {
            "objective": "Transform raw calendar data into friendly, readable summaries",
            "success_criteria": [
                "Natural, human-sounding language",
                "Key information preserved",
                "Easy to scan quickly",
            ],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Read the calendar data carefully",
                "Identify the most important meetings and commitments",
                "Write a natural, conversational summary",
                "Highlight any particularly important or unusual events",
                "Add helpful context where appropriate",
            ],
            "rules": [
                "Use natural language, not bullet points",
                "Start with a friendly overview of the day",
                "Mention preparation needed for meetings",
                "Note any back-to-back meetings or time conflicts",
                "Use phrases like 'You have...' or 'Your day includes...'",
            ],
            "prohibited": [
                "Robotic or overly formal language",
                "Just listing events without context",
                "Making up details not in the data",
            ],
            "output_format": "A warm, professional paragraph summary suitable for a daily digest email",
        },
        "examples": [
            {
                "input": "Events: 9am Team Standup (15min), 10am Client Call - Acme Corp (1hr), 2pm Design Review (30min)",
                "output": "You've got a nicely paced day ahead! You'll kick things off with the usual team standup at 9am - a quick 15 minutes to sync up. Then at 10am, you have an important hour-long call with Acme Corp, so you might want to prep any notes beforehand. The afternoon is lighter, with just a 30-minute design review at 2pm. Overall, plenty of breathing room between meetings!"
            }
        ],
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 1024,
        },
    },

    # -------------------------------------------------------------------------
    # 3. Fact Checker - Catches hallucinations and verifies accuracy
    # -------------------------------------------------------------------------
    "fact-checker": {
        "id": "fact-checker",
        "name": "Accuracy Checker",
        "description": "Verifies summaries against source data to catch hallucinations",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Quality Assurance Specialist",
            "expertise": ["fact checking", "accuracy verification", "error detection"],
            "personality": ["meticulous", "skeptical", "thorough"],
            "communication_style": "analytical and precise",
        },
        "goal": {
            "objective": "Ensure summaries accurately reflect the source data with no fabrications",
            "success_criteria": [
                "All facts in summary match source data",
                "No hallucinated meetings or details",
                "Times and names are accurate",
            ],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Compare the summary against the original calendar data",
                "Check each claim in the summary for accuracy",
                "Identify any hallucinated or incorrect information",
                "Verify times, names, and meeting titles match exactly",
                "Provide a corrected version if issues found",
            ],
            "rules": [
                "Flag any meeting mentioned that doesn't exist in the data",
                "Check that times mentioned are accurate",
                "Verify attendee names and companies",
                "Note if important events were omitted",
            ],
            "prohibited": [
                "Adding new information not in original data",
                "Ignoring discrepancies",
            ],
            "output_format": "JSON with fields: accurate (bool), issues (list), corrected_summary (string if needed)",
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1,
            "max_tokens": 1500,
        },
    },

    # -------------------------------------------------------------------------
    # 4. Email Composer - Creates professional email content
    # -------------------------------------------------------------------------
    "email-composer": {
        "id": "email-composer",
        "name": "Email Composer",
        "description": "Composes professional, well-formatted email content",
        "agent_type": "LLMAgent",
        "role": {
            "title": "Email Content Specialist",
            "expertise": ["email writing", "professional communication", "formatting"],
            "personality": ["professional", "concise", "friendly"],
            "communication_style": "warm professional",
        },
        "goal": {
            "objective": "Create a polished, ready-to-send email from the summary",
            "success_criteria": [
                "Professional greeting and sign-off",
                "Well-structured content",
                "Clear and actionable",
            ],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Take the verified summary",
                "Add a friendly greeting appropriate for the time of day",
                "Structure the content for easy reading",
                "Add a professional sign-off",
                "Include any action items or reminders",
            ],
            "rules": [
                "Keep it concise but complete",
                "Use appropriate greeting based on time of day",
                "Make important items stand out",
            ],
            "prohibited": [
                "Overly long emails",
                "Informal or unprofessional language",
            ],
            "output_format": "Complete email body ready to send",
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "max_tokens": 1024,
        },
    },

    # -------------------------------------------------------------------------
    # 5. Email Sender - Sends email via Gmail MCP
    # -------------------------------------------------------------------------
    "email-sender": {
        "id": "email-sender",
        "name": "Email Sender",
        "description": "Sends emails using Gmail API",
        "agent_type": "ToolAgent",
        "role": {
            "title": "Email Delivery Specialist",
            "expertise": ["email delivery", "Gmail API"],
            "personality": ["reliable", "precise"],
            "communication_style": "action-oriented",
        },
        "goal": {
            "objective": "Send the composed email successfully",
            "success_criteria": ["Email sent successfully", "Confirmation received"],
            "constraints": [],
        },
        "instructions": {
            "steps": [
                "Extract recipient, subject, and body from the request",
                "Call send_email tool with the parameters",
                "Confirm successful delivery",
            ],
            "rules": [
                "Verify email address format before sending",
                "Include appropriate subject line",
            ],
            "prohibited": ["Sending without confirmation"],
        },
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 512,
        },
        "tools": [
            {"tool_id": "mcp:google-gmail:send_email", "enabled": True},
        ],
    },
}

# =============================================================================
# Orchestrator Definition
# =============================================================================

ORCHESTRATOR = {
    "id": "daily-digest-orchestrator",
    "name": "Daily Digest Orchestrator",
    "description": "Orchestrates the daily calendar digest workflow",
    "agent_type": "OrchestratorAgent",
    "role": {
        "title": "Workflow Coordinator",
        "expertise": ["workflow orchestration", "task delegation", "quality control"],
        "personality": ["organized", "thorough", "efficient"],
        "communication_style": "clear and directive",
    },
    "goal": {
        "objective": "Coordinate agents to create and send a daily calendar digest",
        "success_criteria": [
            "Calendar data fetched successfully",
            "Summary created and verified",
            "Email sent to user",
        ],
        "constraints": [],
    },
    "instructions": {
        "steps": [
            "1. First, call the calendar-fetcher to get today's events",
            "2. Pass the calendar data to the summarizer for a human-friendly summary",
            "3. Send both the original data AND the summary to the fact-checker for verification",
            "4. If fact-checker finds issues, have summarizer create a corrected version",
            "5. Once verified, pass to email-composer to format as email",
            "6. Finally, use email-sender to send the digest",
        ],
        "rules": [
            "Always verify summaries before sending",
            "If fact-checker finds hallucinations, get a corrected summary",
            "Include both today and tomorrow's events in the digest",
        ],
        "prohibited": [
            "Sending unverified content",
            "Skipping the fact-check step",
        ],
    },
    "llm_config": {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 2048,
    },
    "orchestrator_config": {
        "mode": "llm_driven",
        "available_agents": [
            {
                "agent_id": "calendar-fetcher",
                "description": "Fetches calendar events for specified dates. Call first to get raw event data.",
            },
            {
                "agent_id": "summarizer",
                "description": "Creates humanized, natural-sounding summaries from calendar data. Use after fetching events.",
            },
            {
                "agent_id": "fact-checker",
                "description": "Verifies summary accuracy against source data. Catches hallucinations. ALWAYS use before sending.",
            },
            {
                "agent_id": "email-composer",
                "description": "Formats the verified summary as a professional email ready to send.",
            },
            {
                "agent_id": "email-sender",
                "description": "Sends the composed email via Gmail. Call last with recipient, subject, and body.",
            },
        ],
        "max_parallel": 2,
        "max_depth": 2,
        "default_aggregation": "all",
    },
}


async def main():
    print("=" * 70)
    print("Daily Calendar Digest Workflow Setup")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # =========================================================================
    # Step 1: Create specialist agents
    # =========================================================================
    print("1. Creating specialist agents...")
    print("-" * 40)

    for agent_id, agent_data in AGENTS.items():
        await create_agent(agent_data)

    # =========================================================================
    # Step 2: Create orchestrator
    # =========================================================================
    print("\n2. Creating orchestrator agent...")
    print("-" * 40)
    await create_agent(ORCHESTRATOR)

    # =========================================================================
    # Step 3: Show available agents
    # =========================================================================
    print("\n3. Workflow ready!")
    print("-" * 40)
    print("Agents created:")
    for agent_id in AGENTS.keys():
        print(f"  • {agent_id}")
    print(f"  • {ORCHESTRATOR['id']} (orchestrator)")

    # =========================================================================
    # Step 4: Show how to run
    # =========================================================================
    print("\n" + "=" * 70)
    print("HOW TO RUN THE WORKFLOW")
    print("=" * 70)

    print("""
1. Make sure prerequisites are running:
   - Temporal: docker compose up -d
   - API: uvicorn src.api.app:app --reload --port 8000
   - Worker: python workers/agent_worker.py
   - Calendar MCP: python mcp_servers/google-calendar/server.py
   - Gmail MCP: python mcp_servers/google-gmail/server.py

2. Run the workflow:

   curl -X POST http://localhost:8000/api/v1/workflow/execute \\
     -H "Content-Type: application/json" \\
     -d '{
       "agent_id": "daily-digest-orchestrator",
       "user_input": "Create a daily digest of my calendar for today and tomorrow, then email it to me at myemail@example.com with subject 'Your Daily Calendar Digest'"
     }'

3. Or use the test script:

   python scripts/test_daily_digest.py
""")

    # =========================================================================
    # Optional: Test the workflow
    # =========================================================================
    run_test = input("\nWould you like to run a test now? (y/n): ").strip().lower()

    if run_test == 'y':
        recipient = input("Enter your email address for the digest: ").strip()
        if not recipient:
            print("No email provided, skipping test.")
            return

        print("\n" + "=" * 70)
        print("RUNNING WORKFLOW TEST")
        print("=" * 70)

        user_input = f"""
        Please create my daily calendar digest:
        1. Fetch my calendar events for today and tomorrow
        2. Create a friendly, humanized summary
        3. Verify the summary is accurate (no hallucinations)
        4. Format it as a professional email
        5. Send it to {recipient} with subject "Your Daily Calendar Digest"
        """

        print(f"\nUser Input:\n{user_input}")
        print("\n" + "-" * 70)
        print("Executing workflow (this may take 1-2 minutes)...")

        try:
            result = await execute_agent("daily-digest-orchestrator", user_input)

            print("\n" + "=" * 70)
            print("WORKFLOW RESULT")
            print("=" * 70)
            print(f"\nSuccess: {result.get('success')}")
            print(f"\nResponse:\n{result.get('content', 'No content')[:2000]}")

            metadata = result.get("metadata", {})
            if metadata.get("agent_results"):
                print("\n" + "-" * 40)
                print("Agents Called:")
                for ar in metadata["agent_results"]:
                    agent = ar.get("agent", "unknown")
                    success = ar.get("result", {}).get("success", False)
                    status = "✓" if success else "✗"
                    print(f"  {status} {agent}")

        except httpx.HTTPStatusError as e:
            print(f"\nHTTP Error: {e.response.status_code}")
            print(e.response.text[:500])
        except Exception as e:
            print(f"\nError: {e}")

    print("\n" + "=" * 70)
    print("Setup complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
