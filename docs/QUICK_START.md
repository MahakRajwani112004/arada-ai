# MagoneAI Quick Start Guide

Get up and running with MagoneAI in under 10 minutes.

---

## Step 1: Create Your First Agent (2 minutes)

### Option A: Simple Conversational Agent

1. Go to **Agents** → **Create New Agent**
2. Fill in:
   - **Name**: "My Assistant"
   - **Type**: LLM Agent
   - **Description**: "A helpful assistant"
3. Set the persona:
   - **Role**: Helpful Assistant
   - **Goal**: Answer questions accurately
4. Choose LLM: OpenAI GPT-4o (recommended)
5. Click **Save**

### Option B: AI-Generated Agent

1. Go to **Agents** → **Create New Agent**
2. Click **"Generate with AI"**
3. Describe what you want:
   ```
   Create a friendly customer support agent that helps
   users with software troubleshooting. Be patient and
   always offer to escalate if the issue is complex.
   ```
4. Review and customize the generated config
5. Click **Save**

---

## Step 2: Test Your Agent (1 minute)

1. Open your agent's detail page
2. Find the **Test** section
3. Type: "Hello! What can you help me with?"
4. Click **Send**
5. See the response!

---

## Step 3: Add Capabilities (3 minutes)

### Add Tools (for Task Automation)

1. **Edit** your agent
2. Change type to **Tool Agent**
3. Scroll to **Tools** section
4. Enable:
   - Calculator (for math)
   - DateTime (for current time)
5. **Save**
6. Test: "What is 15% of $2,340?"

### Add a Skill (for Domain Expertise)

1. Go to **Skills** → **Create New Skill**
2. Quick setup:
   - **Name**: "Professional Tone"
   - **Category**: Communication
3. Add terminology:
   - "Client" = "The customer we're serving"
4. Add reasoning pattern:
   - "Always acknowledge the question before answering"
   - "Use professional but friendly language"
5. **Save**
6. Edit your agent → Enable this skill

---

## Step 4: Connect External Services (3 minutes)

### Connect Google Calendar

1. Go to **Integrations** → **Servers**
2. Click **Add Server**
3. Select **Google Calendar**
4. Click **Connect to Google**
5. Sign in and grant permissions
6. Done! Status shows "Active"

### Use Calendar in Your Agent

1. Edit your agent (must be Tool Agent)
2. Enable tools:
   - `google-calendar:list_events`
   - `google-calendar:create_event`
3. **Save**
4. Test: "What's on my calendar tomorrow?"

---

## Step 5: Create a Simple Workflow (2 minutes)

1. Go to **Workflows** → **Create New Workflow**
2. **Name**: "Q&A Pipeline"
3. Add two steps:

   **Step 1: Answer Question**
   - Type: Agent
   - Agent: Your assistant

   **Step 2: Quality Check**
   - Type: Agent
   - Agent: quality-checker (or create one)

4. Connect: Step 1 → Step 2
5. **Save**

---

## What's Next?

### Explore Agent Types

| If you need... | Use this type |
|----------------|---------------|
| Simple chat | LLM Agent |
| Search docs first | RAG Agent |
| Call APIs/tools | Tool Agent |
| Everything | Full Agent |
| Route to specialists | Router Agent |
| Coordinate agents | Orchestrator Agent |

### Build More Skills

Create skills for:
- Your industry terminology
- Standard operating procedures
- Common response templates
- Domain-specific reasoning

### Connect More Services

Available integrations:
- Google Calendar
- Gmail
- Google Drive
- Outlook Calendar
- Outlook Email
- Slack

### Create Complex Workflows

Build workflows for:
- Customer support pipelines
- Document processing
- Multi-step automation
- Parallel research

---

## Quick Reference

### Agent Creation Checklist

- [ ] Descriptive name
- [ ] Appropriate type selected
- [ ] Role defined (who is the agent?)
- [ ] Goal set (what should it achieve?)
- [ ] Instructions added (how should it behave?)
- [ ] LLM configured
- [ ] Tools enabled (if needed)
- [ ] Skills attached (if needed)
- [ ] Tested with sample messages

### Skill Creation Checklist

- [ ] Clear name and category
- [ ] Relevant terminology added
- [ ] Reasoning patterns defined
- [ ] Examples included (input/output pairs)
- [ ] Resources uploaded (optional)
- [ ] Parameters configured (optional)

### Workflow Creation Checklist

- [ ] Clear name and description
- [ ] All steps defined
- [ ] Entry point set
- [ ] Steps connected properly
- [ ] Error handling configured
- [ ] Tested end-to-end

---

## Need Help?

- **Documentation**: See full docs in `/docs/PLATFORM_DOCUMENTATION.md`
- **API Reference**: See `/docs/API_REFERENCE.md`
- **Support**: Contact your administrator
