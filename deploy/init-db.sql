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

-- ============================================
-- Organizations table
-- ============================================
CREATE TABLE IF NOT EXISTS organizations (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default organization
INSERT INTO organizations (id, name, slug)
VALUES ('00000000-0000-0000-0000-000000000000', 'Default Organization', 'default')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- Users table
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(200),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    org_id VARCHAR(36) NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000' REFERENCES organizations(id),
    invited_by VARCHAR(36) REFERENCES users(id),
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- ============================================
-- User invites table
-- ============================================
CREATE TABLE IF NOT EXISTS user_invites (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email VARCHAR(255) NOT NULL,
    invite_code VARCHAR(64) NOT NULL UNIQUE,
    invited_by VARCHAR(36) NOT NULL REFERENCES users(id),
    org_id VARCHAR(36) NOT NULL REFERENCES organizations(id),
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    used_by VARCHAR(36) REFERENCES users(id),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_user_invites_email ON user_invites(email);

-- ============================================
-- Refresh tokens table
-- ============================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens(user_id);

-- ============================================
-- Agents table (with user_id for multi-tenancy)
-- ============================================
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    agent_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    config_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);
CREATE INDEX IF NOT EXISTS idx_agents_created ON agents(created_at DESC);

-- ============================================
-- MCP servers table (with user_id for multi-tenancy)
-- ============================================
CREATE TABLE IF NOT EXISTS mcp_servers (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    template VARCHAR(100),
    url VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'disconnected',
    error_message TEXT,
    secret_ref VARCHAR(500) NOT NULL,
    oauth_token_ref VARCHAR(500),
    headers_config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_mcp_servers_user_id ON mcp_servers(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_servers_name ON mcp_servers(name);
CREATE INDEX IF NOT EXISTS idx_mcp_servers_template ON mcp_servers(template);

-- ============================================
-- Workflows table (with user_id for multi-tenancy)
-- ============================================
CREATE TABLE IF NOT EXISTS workflows (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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

CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
CREATE INDEX IF NOT EXISTS idx_workflows_category ON workflows(category);
CREATE INDEX IF NOT EXISTS idx_workflows_is_template ON workflows(is_template);
CREATE INDEX IF NOT EXISTS idx_workflows_is_active ON workflows(is_active);

-- ============================================
-- Workflow executions table (with user_id for multi-tenancy)
-- ============================================
CREATE TABLE IF NOT EXISTS workflow_executions (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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

CREATE INDEX IF NOT EXISTS idx_workflow_executions_user_id ON workflow_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);

-- ============================================
-- Knowledge bases table (with user_id for multi-tenancy)
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    collection_name VARCHAR(100) NOT NULL UNIQUE,
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    document_count INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    error_message TEXT,
    created_by VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_knowledge_bases_user_id ON knowledge_bases(user_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_bases_name ON knowledge_bases(name);
CREATE INDEX IF NOT EXISTS ix_knowledge_bases_status ON knowledge_bases(status);

-- ============================================
-- Knowledge documents table
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id VARCHAR(100) PRIMARY KEY,
    knowledge_base_id VARCHAR(100) NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size INTEGER NOT NULL,
    file_path VARCHAR(500),
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    indexed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_kb_id ON knowledge_documents(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status ON knowledge_documents(status);

-- ============================================
-- LLM Usage tracking table (for analytics, user-scoped)
-- ============================================
CREATE TABLE IF NOT EXISTS llm_usage (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id VARCHAR(100),
    agent_id VARCHAR(100),
    workflow_id VARCHAR(100),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_cents INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_type VARCHAR(100),
    error_message VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_timestamp ON llm_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user_id ON llm_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_request_id ON llm_usage(request_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_agent_id ON llm_usage(agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_workflow_id ON llm_usage(workflow_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_provider ON llm_usage(provider);
CREATE INDEX IF NOT EXISTS idx_llm_usage_model ON llm_usage(model);

-- ============================================
-- Agent Executions tracking table (for analytics, user-scoped)
-- ============================================
CREATE TABLE IF NOT EXISTS agent_executions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id VARCHAR(100),
    workflow_id VARCHAR(100),
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    llm_calls_count INTEGER NOT NULL DEFAULT 0,
    tool_calls_count INTEGER NOT NULL DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_type VARCHAR(100),
    error_message VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_agent_executions_timestamp ON agent_executions(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_executions_user_id ON agent_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_request_id ON agent_executions(request_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_workflow_id ON agent_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_type ON agent_executions(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_executions_success ON agent_executions(success);
