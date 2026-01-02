# MagoneAI Chatbot Knowledge Base

This document is optimized for use with a Q&A chatbot to answer user questions about the MagoneAI platform.

---

## PLATFORM OVERVIEW

### What is MagoneAI?

MagoneAI is a dynamic AI agent platform that enables users to build, deploy, and manage sophisticated AI-powered automation without deep AI expertise. It allows you to create intelligent assistants that can understand natural language, execute tasks, search knowledge bases, orchestrate complex workflows, and integrate with external services.

### What are the main features of MagoneAI?

The main features of MagoneAI are:
1. **Agents** - AI entities that perform specific tasks
2. **Skills** - Reusable domain expertise modules
3. **Workflows** - Orchestrated multi-step processes
4. **Integrations** - Connections to external services via MCP
5. **Knowledge Bases** - Document storage for RAG agents
6. **Monitoring** - Analytics and performance tracking

### What LLM providers does MagoneAI support?

MagoneAI supports OpenAI (GPT-4, GPT-4o, GPT-3.5-turbo) and Anthropic (Claude 3 Opus, Sonnet, Haiku).

### What is the technology stack?

The technology stack includes:
- Backend: FastAPI with Python 3.11+
- Frontend: Next.js with TypeScript
- Workflow Engine: Temporal
- Database: PostgreSQL
- External Integration: MCP Protocol

---

## AGENTS

### What is an Agent?

An Agent is an AI entity configured to perform specific tasks. Each agent has a defined personality, goals, and capabilities. When you send a message to an agent, it processes your request and returns an intelligent response.

### What agent types are available?

There are 7 agent types:
1. **Simple Agent** - Rule-based pattern matching, no LLM needed
2. **LLM Agent** - Direct LLM calls for conversations and analysis
3. **RAG Agent** - Searches knowledge base before responding
4. **Tool Agent** - LLM with function calling for task automation
5. **Full Agent** - Combines RAG + LLM + Tools
6. **Router Agent** - Classifies intent and routes to other agents
7. **Orchestrator Agent** - Coordinates multiple agents

### Which agent type should I use?

- For simple questions and conversations: **LLM Agent**
- For knowledge-based Q&A: **RAG Agent**
- For task automation (APIs, calculations): **Tool Agent**
- For complex automation: **Full Agent**
- For multi-domain routing: **Router Agent**
- For multi-agent orchestration: **Orchestrator Agent**

### How do I create an agent?

To create an agent:
1. Navigate to Agents → Create New Agent
2. Fill in basic info (name, type, description)
3. Configure persona (role, goal, instructions)
4. Select LLM configuration (provider and model)
5. Enable tools if needed (for Tool/Full agents)
6. Attach skills if needed
7. Save the agent

### What is agent persona?

Agent persona consists of three parts:
- **Role**: Who the agent is (title, expertise, personality)
- **Goal**: What the agent aims to achieve (objective, success criteria)
- **Instructions**: How the agent should behave (steps, rules, output format)

### Can I generate an agent using AI?

Yes! You can generate an agent configuration using AI. Go to Agents → Create New Agent → Generate with AI, then describe what you want in natural language. The AI will create a complete agent configuration that you can customize.

### How do I test an agent?

To test an agent, go to the agent's detail page and find the Test section. Enter a message and click Send to see the agent's response.

---

## SKILLS

### What is a Skill?

A Skill is a reusable domain expertise module that enhances agents with specialized knowledge. Skills bundle terminology, reasoning patterns, examples, resources, and parameters.

### What are the components of a Skill?

A skill includes:
- **Terminology**: Domain-specific terms with definitions and aliases
- **Reasoning Patterns**: Step-by-step frameworks for problem-solving
- **Examples**: Input/output pairs showing the skill in action
- **Resources**: Reference documents, templates, code snippets
- **Parameters**: Configurable settings for skill behavior

### What skill categories are available?

Available categories:
- **Domain Expertise**: Subject matter knowledge (legal, medical, financial)
- **Document Generation**: Template-based document creation
- **Data Analysis**: Data processing expertise
- **Communication**: Style and communication guidance
- **Research**: Research methodology
- **Coding**: Programming patterns and examples
- **Custom**: User-defined categories

### What is the difference between Skills and Tools?

Skills provide knowledge and reasoning - they enhance HOW the agent thinks. Tools provide actions - they enable WHAT the agent can do. Skills make agents smarter in a domain, while tools let agents take actions.

### How do I create a Skill?

To create a skill:
1. Navigate to Skills → Create New Skill
2. Enter basic info (name, category, tags)
3. Add terminology (domain terms and definitions)
4. Add reasoning patterns (step-by-step frameworks)
5. Add examples (input/output pairs)
6. Upload resources (optional - documents, templates)
7. Configure parameters (optional)
8. Save the skill

### How do I attach a Skill to an Agent?

To attach a skill to an agent:
1. Edit the agent
2. Scroll to the Skills section
3. Browse available skills
4. Enable the skills you want
5. Configure skill parameters if available
6. Save changes

### Can I share skills across agents?

Yes! Skills are designed to be reusable. Create a skill once and attach it to multiple agents.

### How many skills can I attach to one agent?

You can attach multiple skills, but more skills means more context for the LLM. We recommend 3-5 highly relevant skills per agent for optimal performance.

---

## WORKFLOWS

### What is a Workflow?

A Workflow is an orchestrated sequence of steps that can involve multiple agents, parallel execution, conditional branching, and loops. Workflows enable complex multi-step processes.

### What is the difference between an Agent and a Workflow?

An Agent is a single AI entity that handles one interaction. A Workflow orchestrates multiple agents and steps to handle complex, multi-stage processes.

### What step types are available in Workflows?

There are 4 step types:
1. **Agent Step**: Execute a single agent
2. **Parallel Step**: Execute multiple agents simultaneously
3. **Conditional Step**: Branch based on conditions
4. **Loop Step**: Iterate until a condition is met

### How do I create a Workflow?

You can create workflows in three ways:
1. **From Scratch**: Use the visual builder to drag and drop steps
2. **From Template**: Copy an existing workflow and customize it
3. **AI Generated**: Describe what you need in natural language

### What happens if a workflow step fails?

You can configure error handling per step: retry the step, skip the step, or jump to an error handler step.

### How long can workflows run?

Workflows can run for hours thanks to Temporal's durable execution. Individual steps have configurable timeouts (default 5 minutes).

### Can workflows run on a schedule?

Scheduled workflows are planned for a future release. Currently, workflows are triggered via API.

---

## INTEGRATIONS (MCP)

### What is MCP?

MCP (Model Context Protocol) is a standardized way to connect AI agents with external services. MCP servers expose tools that agents can call during execution.

### What integrations are available?

Available integrations:
- **Google Calendar**: List, create, update, delete events
- **Gmail**: List, send, search emails
- **Google Drive**: List, upload, download files
- **Outlook Calendar**: List, create, update events
- **Outlook Email**: List, send emails
- **Slack**: Send messages, list channels, search

### How do I connect Google Calendar?

To connect Google Calendar:
1. Navigate to Integrations → Servers → Add Server
2. Select Google Calendar template
3. Name your connection
4. Click Connect to Google
5. Sign in and grant permissions
6. Return to MagoneAI - status shows Active

### How do I connect Gmail?

To connect Gmail:
1. Navigate to Integrations → Servers → Add Server
2. Select Gmail template
3. Complete OAuth flow with Gmail permissions
4. Enable Gmail tools in your agents

### How do I use MCP tools in an agent?

Once you've connected an MCP server:
1. Edit your agent (must be Tool Agent or Full Agent)
2. Go to the Tools section
3. Enable the MCP tools you want (e.g., google-calendar:create_event)
4. Save the agent
5. The agent can now use those tools

### Can I connect custom APIs?

Yes! You can add custom MCP servers by providing the server URL and credentials when adding a new server.

### Is my data sent to external services?

Your data only goes to external services when an agent explicitly calls an MCP tool like Google Calendar. Your data stays within MagoneAI unless an external tool is called.

### How are OAuth tokens stored?

OAuth tokens are stored encrypted in a secure vault. They're never exposed in the UI or API responses.

---

## KNOWLEDGE BASES (RAG)

### What is a Knowledge Base?

A Knowledge Base is a collection of documents that RAG agents can search for context before generating responses.

### What is RAG?

RAG stands for Retrieval Augmented Generation. It's a technique where the agent searches a knowledge base for relevant information before generating a response, making answers more accurate and grounded in your documentation.

### How do I create a Knowledge Base?

To create a knowledge base:
1. Navigate to Integrations → Knowledge → Create Collection
2. Name your collection
3. Upload documents (PDFs, text files, etc.)
4. Wait for processing (documents are chunked and embedded)

### How do I create a RAG Agent?

To create a RAG Agent:
1. Navigate to Agents → Create New Agent
2. Select type: RAG Agent
3. Configure name, persona
4. Select the knowledge base to use
5. Set Top K results (how many chunks to retrieve, default 5)
6. Save the agent

### What types of documents can I upload?

You can upload PDFs, text files, Word documents, and other common document formats.

### Why isn't my RAG agent finding relevant content?

If your RAG agent isn't finding relevant content:
1. Verify documents were uploaded successfully
2. Check if processing completed (embedding finished)
3. Try rephrasing your question
4. Increase the Top K results setting
5. Verify the document content is relevant to your question

---

## MONITORING

### How do I monitor agent performance?

To monitor performance:
1. Navigate to Monitoring
2. View the dashboard showing:
   - Total executions
   - Success rate
   - Average response time
   - Token usage
   - Tool usage breakdown

### How do I view execution history?

To view execution history:
1. Go to an agent's detail page
2. View the Execution History section
3. Click any execution to see full details including conversation, tools called, response time, and errors

---

## API

### What is the base API URL?

The base API URL is: `https://your-instance.magoneai.com/api/v1`

### How do I authenticate API requests?

Use a JWT token in the Authorization header: `Authorization: Bearer <your_jwt_token>`

### How do I execute an agent via API?

Send a POST request to `/workflow/execute`:
```json
{
  "agent_id": "my-agent",
  "user_input": "Your message here",
  "conversation_history": [],
  "session_id": "optional-session-id"
}
```

### What are the main API endpoints?

Main endpoints:
- `GET /agents` - List agents
- `POST /agents` - Create agent
- `POST /workflow/execute` - Execute agent
- `GET /skills` - List skills
- `POST /skills` - Create skill
- `GET /workflows` - List workflows
- `POST /workflows` - Create workflow
- `GET /mcp/servers` - List MCP servers

---

## TROUBLESHOOTING

### Agent not responding

If an agent is not responding or timing out:
1. Check if the LLM provider (OpenAI/Anthropic) is accessible
2. Verify API keys are configured correctly
3. Check if Temporal workers are running
4. Review agent logs for errors

### Tool execution fails

If tool execution fails:
1. Verify MCP server is connected (Integrations → Servers)
2. Re-authenticate if OAuth token expired
3. Check tool permissions
4. Review tool parameters in agent config

### OAuth connection failed

If OAuth connection fails:
1. Ensure popup blockers are disabled
2. Check if correct account is selected
3. Verify OAuth credentials in settings
4. Try disconnecting and reconnecting

### Workflow stuck

If a workflow is stuck:
1. Check Temporal UI for workflow status
2. Review step configurations
3. Check for circular dependencies
4. Verify all referenced agents exist
5. Check timeout settings

---

## GLOSSARY

- **Agent**: An AI entity configured to perform specific tasks
- **Skill**: Reusable domain expertise module for agents
- **Workflow**: Orchestrated sequence of steps involving agents
- **MCP**: Model Context Protocol - standard for external integrations
- **RAG**: Retrieval Augmented Generation - search before generate
- **Tool**: An action an agent can perform (API call, calculation)
- **LLM**: Large Language Model (GPT-4, Claude)
- **Temporal**: Durable workflow execution engine
- **Knowledge Base**: Collection of documents for RAG agents
- **OAuth**: Authentication protocol for external services
- **Persona**: Agent's role, goal, and instructions
- **Top K**: Number of document chunks to retrieve in RAG
