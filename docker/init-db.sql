-- Initialize database for Magure AI Platform
-- Creates separate databases for application and Temporal

-- Create temporal database (required by Temporal auto-setup)
CREATE DATABASE temporal;
CREATE DATABASE temporal_visibility;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE temporal TO magure;
GRANT ALL PRIVILEGES ON DATABASE temporal_visibility TO magure;
GRANT ALL PRIVILEGES ON DATABASE magure_db TO magure;

-- Connect to magure_db to create application tables
\c magure_db;

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

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);
CREATE INDEX IF NOT EXISTS idx_agents_created ON agents(created_at DESC);
