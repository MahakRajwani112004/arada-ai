#!/usr/bin/env python3
"""
Test the Daily Calendar Digest Workflow.

Run this after create_daily_digest_workflow.py to test the workflow.

Usage:
    python scripts/test_daily_digest.py [email@example.com]
"""
import asyncio
import sys
import httpx
from datetime import datetime

API_URL = "http://localhost:8000/api/v1"


async def execute_workflow(user_input: str) -> dict:
    """Execute the daily digest orchestrator."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/workflow/execute",
            json={
                "agent_id": "daily-digest-orchestrator",
                "user_input": user_input,
            },
            timeout=300.0,
        )
        response.raise_for_status()
        return response.json()


async def test_individual_agent(agent_id: str, query: str) -> dict:
    """Test an individual agent."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/workflow/execute",
            json={"agent_id": agent_id, "user_input": query},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()


async def main():
    print("=" * 70)
    print("Daily Calendar Digest - Workflow Test")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get email from args or prompt
    if len(sys.argv) > 1:
        recipient = sys.argv[1]
    else:
        recipient = input("\nEnter your email for the digest (or press Enter to skip sending): ").strip()

    # Choose test mode
    print("\nTest Options:")
    print("  1. Full workflow (calendar → summarize → verify → compose → send)")
    print("  2. Just fetch calendar events")
    print("  3. Test summarizer with sample data")
    print("  4. Test fact-checker with sample data")

    choice = input("\nSelect option (1-4): ").strip()

    if choice == "1":
        # Full workflow
        print("\n" + "-" * 70)
        print("Running full workflow...")
        print("-" * 70)

        if recipient:
            user_input = f"""
            Create my daily calendar digest:
            1. Fetch my calendar events for today and tomorrow
            2. Create a friendly, human-sounding summary
            3. Verify the summary is accurate with no hallucinations
            4. Format it as a professional email
            5. Send it to {recipient} with subject "Your Daily Calendar Digest - {datetime.now().strftime('%B %d')}"
            """
        else:
            user_input = """
            Create my daily calendar digest:
            1. Fetch my calendar events for today and tomorrow
            2. Create a friendly, human-sounding summary
            3. Verify the summary is accurate with no hallucinations
            4. Format it as a professional email
            5. Show me the final email (don't send it)
            """

        try:
            result = await execute_workflow(user_input)
            print_result(result)
        except Exception as e:
            print(f"\nError: {e}")

    elif choice == "2":
        # Just calendar fetch
        print("\n" + "-" * 70)
        print("Fetching calendar events...")
        print("-" * 70)

        try:
            result = await test_individual_agent(
                "calendar-fetcher",
                "List my calendar events for today and tomorrow"
            )
            print_result(result)
        except Exception as e:
            print(f"\nError: {e}")

    elif choice == "3":
        # Test summarizer
        print("\n" + "-" * 70)
        print("Testing summarizer with sample data...")
        print("-" * 70)

        sample_data = """
        Calendar Events for December 22, 2024:

        1. Team Standup
           Time: 9:00 AM - 9:15 AM
           Attendees: team@company.com
           Location: Zoom

        2. Client Call - Acme Corp Q4 Review
           Time: 10:00 AM - 11:00 AM
           Attendees: john@acme.com, sarah@acme.com
           Location: Google Meet
           Description: Quarterly business review

        3. Lunch with Sarah
           Time: 12:30 PM - 1:30 PM
           Location: Cafe Luna, 123 Main St

        4. Design Review - New Dashboard
           Time: 2:00 PM - 2:30 PM
           Attendees: design-team@company.com
           Location: Conference Room B

        5. 1:1 with Manager
           Time: 4:00 PM - 4:30 PM
           Attendees: manager@company.com
        """

        try:
            result = await test_individual_agent(
                "summarizer",
                f"Create a humanized summary of this calendar data:\n\n{sample_data}"
            )
            print_result(result)
        except Exception as e:
            print(f"\nError: {e}")

    elif choice == "4":
        # Test fact-checker
        print("\n" + "-" * 70)
        print("Testing fact-checker...")
        print("-" * 70)

        # Include a hallucination to test
        original_data = """
        Events:
        - 9am Team Standup (15 min)
        - 10am Client Call with Acme (1 hour)
        - 2pm Design Review (30 min)
        """

        summary_with_error = """
        You've got a busy day! Starting with the team standup at 9am,
        then an important 2-hour call with Acme Corp at 10am (make sure to prep!).
        After lunch you have a design review at 2pm, followed by a 1:1 with your manager at 3pm.
        """

        try:
            result = await test_individual_agent(
                "fact-checker",
                f"""
                Please verify this summary against the original data.

                ORIGINAL CALENDAR DATA:
                {original_data}

                SUMMARY TO VERIFY:
                {summary_with_error}

                Check for any hallucinations, incorrect times, or made-up meetings.
                """
            )
            print_result(result)
        except Exception as e:
            print(f"\nError: {e}")

    else:
        print("Invalid option")


def print_result(result: dict):
    """Pretty print the result."""
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)

    print(f"\nSuccess: {result.get('success')}")

    if result.get('error'):
        print(f"Error: {result.get('error')}")

    print(f"\nContent:\n{'-' * 40}")
    content = result.get('content', 'No content')
    # Truncate if too long
    if len(content) > 3000:
        print(content[:3000] + "\n... (truncated)")
    else:
        print(content)

    metadata = result.get("metadata", {})

    if metadata.get("tool_calls"):
        print(f"\n{'-' * 40}")
        print(f"Tool Calls: {len(metadata['tool_calls'])}")
        for tc in metadata["tool_calls"][:5]:
            tool = tc.get("tool", "unknown")
            success = tc.get("result", {}).get("success", False)
            status = "✓" if success else "✗"
            print(f"  {status} {tool}")

    if metadata.get("agent_results"):
        print(f"\n{'-' * 40}")
        print(f"Agent Calls: {len(metadata['agent_results'])}")
        for ar in metadata["agent_results"]:
            agent = ar.get("agent", "unknown")
            success = ar.get("result", {}).get("success", False)
            status = "✓" if success else "✗"
            print(f"  {status} {agent}")

    if metadata.get("iterations"):
        print(f"\nIterations: {metadata['iterations']}")


if __name__ == "__main__":
    asyncio.run(main())
