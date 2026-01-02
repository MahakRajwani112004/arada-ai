# MagoneAI Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the MagoneAI platform.

---

## Table of Contents

1. [Agent Issues](#1-agent-issues)
2. [Skill Issues](#2-skill-issues)
3. [Workflow Issues](#3-workflow-issues)
4. [Integration Issues (MCP)](#4-integration-issues-mcp)
5. [OAuth Issues](#5-oauth-issues)
6. [Knowledge Base Issues](#6-knowledge-base-issues)
7. [Performance Issues](#7-performance-issues)
8. [API Issues](#8-api-issues)
9. [Infrastructure Issues](#9-infrastructure-issues)

---

## 1. Agent Issues

### Agent Not Responding / Timeout

**Symptoms:**
- Agent hangs for a long time
- Request times out
- No response received

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| LLM provider unavailable | Check OpenAI/Anthropic status pages |
| Invalid API keys | Verify API keys in Settings |
| Temporal worker not running | Start the worker: `python workers/agent_worker.py` |
| Network issues | Check network connectivity |

**Diagnostic Steps:**
1. Check worker logs: `docker logs magoneai-worker`
2. Check API logs: `docker logs magoneai-api`
3. Verify LLM provider status
4. Try a simple LLM Agent first

---

### Agent Returns Empty Response

**Symptoms:**
- Agent responds with empty or null content
- Success is true but no content

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Incomplete persona config | Add role, goal, and instructions |
| LLM temperature too low | Increase temperature (try 0.7) |
| Conflicting instructions | Review and simplify instructions |

**Diagnostic Steps:**
1. Review agent configuration
2. Check if all persona fields are populated
3. Test with simplified instructions

---

### Agent Gives Wrong/Irrelevant Responses

**Symptoms:**
- Agent doesn't follow instructions
- Responses are off-topic
- Agent ignores context

**Solutions:**
1. **Improve Instructions**: Make them more specific and numbered
2. **Add Examples**: Include few-shot examples in the agent config
3. **Use Skills**: Add domain-specific skills for better context
4. **Check LLM Model**: Try GPT-4o or Claude 3 Opus for better reasoning
5. **Lower Temperature**: Reduce temperature for more focused responses

---

### Tool Calling Not Working

**Symptoms:**
- Agent doesn't use available tools
- Tool execution fails
- "Tool not found" errors

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Wrong agent type | Change to Tool Agent or Full Agent |
| Tools not enabled | Enable tools in agent configuration |
| MCP server disconnected | Reconnect the MCP server |
| Invalid tool parameters | Check tool input schema |

**Diagnostic Steps:**
1. Verify agent type is ToolAgent or FullAgent
2. Check which tools are enabled
3. Verify MCP server status in Integrations
4. Review tool execution logs

---

## 2. Skill Issues

### Skill Not Affecting Agent Responses

**Symptoms:**
- Agent doesn't use skill terminology
- Reasoning patterns not followed
- Examples not reflected

**Solutions:**
1. **Verify Skill is Attached**: Check agent configuration
2. **Check Skill Status**: Skill must be "published" not "draft"
3. **Clear Terminology**: Ensure terms are distinct and well-defined
4. **Simplify Reasoning Patterns**: Break into clear, numbered steps

---

### Skill File Upload Fails

**Symptoms:**
- File upload returns error
- Files don't appear in skill

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| File too large | Reduce file size (max 10MB) |
| Unsupported format | Use PDF, DOCX, TXT, MD |
| Storage full | Clean up old files |
| Permission issues | Check file system permissions |

---

### Too Many Skills Degrading Performance

**Symptoms:**
- Slow agent responses
- Token limit errors
- Confused agent responses

**Solutions:**
1. **Reduce Skills**: Use 3-5 most relevant skills per agent
2. **Consolidate Skills**: Merge similar skills
3. **Use Parameters**: Make skills more focused with parameters
4. **Prioritize**: Enable only essential terminology/patterns

---

## 3. Workflow Issues

### Workflow Stuck / Not Completing

**Symptoms:**
- Workflow shows "RUNNING" indefinitely
- Steps don't progress
- No output received

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Step timeout | Increase step timeout in workflow config |
| Circular dependency | Review step connections |
| Missing agent | Ensure all referenced agents exist |
| Temporal issues | Restart Temporal worker |

**Diagnostic Steps:**
1. Check Temporal UI: `http://localhost:8233`
2. Review workflow execution history
3. Check individual step status
4. Look for error messages in logs

---

### Workflow Step Fails

**Symptoms:**
- Step shows "FAILED" status
- Error message in execution details

**Solutions:**

1. **Check Agent**: Verify the agent used in the step works independently
2. **Check Input**: Ensure step input references are valid (${steps.x.output})
3. **Add Error Handling**: Configure retry or skip on error
4. **Check Timeout**: Increase if step is timing out

---

### Parallel Steps Not Executing Together

**Symptoms:**
- Parallel branches run sequentially
- Poor performance on parallel steps

**Solutions:**
1. **Verify Step Type**: Ensure step type is "parallel"
2. **Check Branch Config**: All branches must be properly defined
3. **Check Worker Capacity**: May need more workers for parallel execution

---

### Conditional Routing Not Working

**Symptoms:**
- Wrong branch selected
- Default branch always taken

**Solutions:**
1. **Check Condition Source**: Verify the ${steps.x.field} reference is correct
2. **Check Branch Keys**: Keys must match exactly (case-sensitive)
3. **Add Default Branch**: Always include a default path
4. **Debug Output**: Log the condition value to see what's being evaluated

---

## 4. Integration Issues (MCP)

### MCP Server Shows "Disconnected"

**Symptoms:**
- Server status shows disconnected/error
- Tools not available

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Server not running | Start the MCP server |
| Wrong URL | Check server URL configuration |
| OAuth token expired | Re-authenticate with OAuth |
| Network issues | Check connectivity to MCP server |

**Diagnostic Steps:**
1. Check MCP server health: `GET /mcp/health`
2. Verify server is running: `curl http://localhost:8001/health`
3. Check server logs
4. Try reconnecting the server

---

### MCP Tools Not Appearing

**Symptoms:**
- Connected server shows no tools
- Tools list is empty

**Solutions:**
1. **Refresh Connection**: Disconnect and reconnect the server
2. **Check Server Implementation**: Verify tools are properly exposed
3. **Check Credentials**: Some tools require specific permissions

---

### MCP Tool Execution Fails

**Symptoms:**
- "Tool execution failed" error
- External service errors

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Invalid credentials | Re-authenticate or update credentials |
| Service quota exceeded | Check external service quotas |
| Invalid parameters | Review tool input schema |
| Service outage | Check external service status |

---

## 5. OAuth Issues

### OAuth Redirect Fails

**Symptoms:**
- Redirect doesn't happen
- Error after Google login

**Solutions:**
1. **Check Redirect URI**: Must match Google Console configuration
2. **Disable Popup Blockers**: Allow popups for the site
3. **Check OAuth Credentials**: Verify client ID and secret
4. **HTTPS Required**: OAuth may require HTTPS in production

---

### "Access Denied" from Google

**Symptoms:**
- Google shows access denied screen
- Cannot grant permissions

**Solutions:**
1. **Check Scopes**: Ensure requested scopes are enabled in Google Console
2. **App Verification**: App may need verification for sensitive scopes
3. **Account Restrictions**: Work/school accounts may have restrictions
4. **Try Different Account**: Test with a personal Google account

---

### Refresh Token Invalid

**Symptoms:**
- Previously working integration fails
- "Invalid refresh token" errors

**Solutions:**
1. **Re-authenticate**: Go through OAuth flow again
2. **Check Token Expiry**: Some tokens expire after period of inactivity
3. **Revoke and Reconnect**: Revoke app access in Google settings, then reconnect

---

## 6. Knowledge Base Issues

### Documents Not Being Found

**Symptoms:**
- RAG agent returns "I don't have information about..."
- No relevant context retrieved

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Processing not complete | Wait for document embedding to finish |
| Wrong collection selected | Verify correct knowledge base in agent |
| Too few results | Increase Top K setting (try 10) |
| Question too vague | Rephrase with specific terms |

---

### Poor Quality RAG Responses

**Symptoms:**
- Retrieved context is irrelevant
- Agent makes up information

**Solutions:**
1. **Improve Documents**: Use clearer, well-structured documents
2. **Increase Top K**: Retrieve more chunks
3. **Adjust Chunking**: Use smaller chunks for more precise retrieval
4. **Add More Documents**: Ensure coverage of the topic
5. **Use Better Model**: GPT-4 or Claude 3 for better synthesis

---

### Document Upload Fails

**Symptoms:**
- Upload times out
- Error during processing

**Solutions:**
1. **Check File Size**: Max 50MB per file
2. **Check Format**: Use supported formats (PDF, DOCX, TXT, MD)
3. **Check Encoding**: Ensure text files use UTF-8
4. **Split Large Files**: Break into smaller documents

---

## 7. Performance Issues

### Slow Agent Responses

**Symptoms:**
- Responses take > 10 seconds
- Consistent latency issues

**Solutions:**

| Issue | Solution |
|-------|----------|
| LLM latency | Use faster model (GPT-3.5, Claude Haiku) |
| Too many skills | Reduce to 3-5 essential skills |
| Large knowledge base | Optimize chunking, reduce Top K |
| Tool overhead | Limit tool iterations |
| Network latency | Check connection to LLM provider |

---

### High Token Usage

**Symptoms:**
- Unexpectedly high costs
- Token quota exceeded

**Solutions:**
1. **Reduce Skills**: Each skill adds to prompt size
2. **Limit Conversation History**: Cap at 10-20 messages
3. **Use Smaller Models**: GPT-3.5 for simple tasks
4. **Optimize Instructions**: Make them concise
5. **Monitor Usage**: Check analytics for patterns

---

### Workflow Takes Too Long

**Symptoms:**
- Multi-step workflows very slow
- Sequential bottlenecks

**Solutions:**
1. **Use Parallel Steps**: Execute independent agents concurrently
2. **Simplify Agents**: Use lighter agents for sub-tasks
3. **Cache Results**: Avoid redundant processing
4. **Increase Workers**: Add more Temporal workers

---

## 8. API Issues

### 401 Unauthorized

**Symptoms:**
- All API calls return 401

**Solutions:**
1. **Check Token**: Ensure JWT token is valid and not expired
2. **Refresh Token**: Get new access token with refresh token
3. **Check Header**: Use `Authorization: Bearer <token>`

---

### 404 Not Found

**Symptoms:**
- Resource returns 404

**Solutions:**
1. **Check ID**: Verify the resource ID is correct
2. **Check Ownership**: Resource must belong to your user
3. **Check Deletion**: Resource may have been deleted

---

### 422 Validation Error

**Symptoms:**
- Request returns 422 with validation details

**Solutions:**
1. **Check Request Body**: Ensure all required fields present
2. **Check Types**: Ensure values match expected types
3. **Check Enums**: Use valid enum values
4. **Read Error Details**: Response includes specific field errors

---

### 500 Internal Server Error

**Symptoms:**
- Server returns 500

**Solutions:**
1. **Check Logs**: Review API server logs for stack trace
2. **Retry**: May be transient error
3. **Report Bug**: If persistent, file a bug report

---

## 9. Infrastructure Issues

### Temporal Worker Not Starting

**Symptoms:**
- Worker fails to connect
- "Temporal unavailable" errors

**Solutions:**
1. **Check Temporal Server**: Ensure it's running on port 7233
2. **Check Namespace**: Verify namespace exists
3. **Check Network**: Worker must reach Temporal server
4. **Check Logs**: Review worker startup logs

**Start Temporal:**
```bash
docker-compose up -d temporal
```

---

### Database Connection Issues

**Symptoms:**
- "Cannot connect to database" errors
- Data not persisting

**Solutions:**
1. **Check PostgreSQL**: Ensure it's running on port 5432
2. **Check Credentials**: Verify DATABASE_URL in .env
3. **Check Migrations**: Run `alembic upgrade head`

---

### MCP Server Crashes

**Symptoms:**
- MCP server repeatedly restarts
- Connection errors

**Solutions:**
1. **Check Dependencies**: Ensure all Python packages installed
2. **Check Port Conflicts**: Each MCP server needs unique port
3. **Check Logs**: Review crash logs
4. **Memory Issues**: May need more RAM

---

## Quick Reference: Error Codes

| Error | Meaning | Common Fix |
|-------|---------|------------|
| `AGENT_NOT_FOUND` | Agent ID doesn't exist | Check agent ID |
| `WORKFLOW_TIMEOUT` | Workflow exceeded time limit | Increase timeout |
| `TOOL_EXECUTION_FAILED` | External tool call failed | Check MCP connection |
| `LLM_ERROR` | LLM provider error | Check API keys/quotas |
| `INVALID_CONFIG` | Configuration is invalid | Review agent/skill config |
| `RATE_LIMITED` | Too many requests | Wait and retry |
| `TOKEN_EXPIRED` | JWT token expired | Refresh token |
| `OAUTH_FAILED` | OAuth flow failed | Re-authenticate |

---

## Getting Help

If you can't resolve an issue:

1. **Check Logs**: API, worker, and MCP server logs
2. **Check Temporal UI**: For workflow execution details
3. **Collect Info**: Note error messages, IDs, and timestamps
4. **Contact Support**: Provide collected information

---

## Common Log Locations

| Component | Log Location |
|-----------|--------------|
| API Server | `docker logs magoneai-api` |
| Worker | `docker logs magoneai-worker` |
| Temporal | `docker logs temporal` |
| MCP Servers | `docker logs magoneai-mcp-calendar` |
| PostgreSQL | `docker logs postgres` |
