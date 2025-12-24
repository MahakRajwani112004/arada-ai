-- Initialize database for MagOneAI Platform
-- Creates separate databases for application and Temporal

-- Create temporal database (required by Temporal auto-setup)
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE temporal TO magone;
GRANT ALL PRIVILEGES ON DATABASE temporal_visibility TO magone;
GRANT ALL PRIVILEGES ON DATABASE magone_db TO magone;

-- Connect to magone_db to create application tables
\c magone_db;

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    agent_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    config_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create MCP servers table (matches MCPServerModel)
CREATE TABLE IF NOT EXISTS mcp_servers (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    template VARCHAR(100),
    url VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'disconnected',
    error_message TEXT,
    secret_ref VARCHAR(500) NOT NULL,
    headers_config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Create workflows table (matches WorkflowModel)
CREATE TABLE IF NOT EXISTS workflows (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category VARCHAR(100) NOT NULL DEFAULT 'general',
    tags VARCHAR[] NOT NULL DEFAULT '{}',
    is_template BOOLEAN NOT NULL DEFAULT FALSE,
    source_template_id VARCHAR(100) REFERENCES workflows(id),
    definition_json JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_by VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create workflow executions table (matches WorkflowExecutionModel)
CREATE TABLE IF NOT EXISTS workflow_executions (
    id VARCHAR(100) PRIMARY KEY,
    workflow_id VARCHAR(100) NOT NULL REFERENCES workflows(id),
    temporal_workflow_id VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    input_json JSONB NOT NULL,
    output_json JSONB,
    error TEXT,
    steps_executed VARCHAR[] NOT NULL DEFAULT '{}',
    step_results JSONB NOT NULL DEFAULT '{}',
    triggered_by VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);
CREATE INDEX IF NOT EXISTS idx_agents_created ON agents(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_mcp_servers_name ON mcp_servers(name);
CREATE INDEX IF NOT EXISTS idx_mcp_servers_template ON mcp_servers(template);

CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
CREATE INDEX IF NOT EXISTS idx_workflows_category ON workflows(category);
CREATE INDEX IF NOT EXISTS idx_workflows_is_template ON workflows(is_template);
CREATE INDEX IF NOT EXISTS idx_workflows_is_active ON workflows(is_active);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
