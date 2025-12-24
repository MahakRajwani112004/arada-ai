# Arada Real Estate SQL MCP Server

A plug-and-play MCP server for the Arada Real Estate Intelligence Bot. Provides SQL query capabilities over 1,000 real estate booking records.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MagOneAI Platform                       │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  Arada Agent (ToolAgent)                              │  │
│   │  - Analyzes questions                                 │  │
│   │  - Writes SQL queries                                 │  │
│   │  - Provides insights                                  │  │
│   └────────────────────────┬─────────────────────────────┘  │
│                            │ MCP Protocol                    │
│                            ▼                                 │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  Arada SQL MCP Server (this)                          │  │
│   │  - get_schema: Database structure                     │  │
│   │  - execute_sql: Run queries                           │  │
│   │  - get_portfolio_summary: Overview metrics            │  │
│   └────────────────────────┬─────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  PostgreSQL Database                                  │  │
│   │  - bookings table (1,000 records)                    │  │
│   │  - AED 5.37B portfolio                               │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- MagOneAI platform running

### Step 1: Create Database

```bash
# Connect to PostgreSQL and create database
psql -U postgres -c "CREATE DATABASE arada;"
```

### Step 2: Install Dependencies

```bash
cd /Users/mahak/magoneai_v2/mcp_servers/arada-sql
pip install -r requirements.txt
```

### Step 3: Import Data

```bash
# Set database URL (adjust credentials as needed)
export ARADA_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/arada"

# Import CSV data
python import_data.py --csv /Users/mahak/arada-ai/records_real_estate.csv
```

Expected output:
```
Reading CSV: /Users/mahak/arada-ai/records_real_estate.csv
Loaded 1000 records
Creating table...
Inserting data...
Inserted 1000 records successfully!

Development                  Bookings      Avg Price  Cancel %
-----------------------------------------------------------------
DAMAC Lagoons                     178      4,234,567     52.3%
Emaar Beachfront                  172      5,123,456     48.8%
...
```

### Step 4: Start MCP Server

```bash
# Set database URL
export ARADA_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/arada"

# Start server on port 8002
python server.py
```

Server will start at `http://localhost:8002`

### Step 5: Verify Server

```bash
# Check health
curl http://localhost:8002/health

# Expected:
# {"status":"healthy","server":"arada-sql","version":"1.0.0","tools":["get_schema","execute_sql","get_portfolio_summary"]}
```

### Step 6: Register with MagOneAI

```bash
# Register MCP server
curl -X POST http://localhost:8000/api/v1/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "arada-sql",
    "name": "Arada Real Estate SQL",
    "url": "http://localhost:8002"
  }'

# Create agent from config
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d @agent_config.json
```

### Step 7: Use the Agent

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "arada-real-estate",
    "input": "How is DAMAC Bay performing?"
  }'
```

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | PostgreSQL table definition |
| `import_data.py` | CSV to PostgreSQL import script |
| `server.py` | MCP server implementation |
| `agent_config.json` | Agent configuration for MagOneAI |
| `requirements.txt` | Python dependencies |

## MCP Tools

### get_schema
Returns database schema with column descriptions. Use first to understand available data.

### execute_sql
Execute SELECT queries on the bookings table. Only SELECT is allowed (read-only).

Example queries:
```sql
-- Cancellation rate by development
SELECT development,
       AVG(CASE WHEN booking_status='Cancelled' THEN 1 ELSE 0 END)*100 as cancel_rate
FROM bookings
GROUP BY development;

-- Monthly booking trend
SELECT DATE_TRUNC('month', booking_date) as month, COUNT(*) as bookings
FROM bookings
GROUP BY 1 ORDER BY 1;

-- Top nationalities
SELECT nationality, COUNT(*) as bookings, ROUND(AVG(selling_price)/1000000, 2) as avg_price_m
FROM bookings
GROUP BY nationality
ORDER BY bookings DESC
LIMIT 10;
```

### get_portfolio_summary
Returns high-level portfolio metrics including:
- Total bookings and value
- Breakdown by development
- Breakdown by unit type
- Breakdown by lead source

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ARADA_DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/arada` | PostgreSQL connection URL |
| `DATABASE_URL` | (fallback) | Alternative database URL |

## Example Conversations

### Performance Query
```
User: "How is DAMAC Bay performing?"

Agent:
1. Calls get_portfolio_summary for context
2. Calls execute_sql with DAMAC Bay filters
3. Compares to portfolio averages
4. Returns formatted analysis with recommendations
```

### Root Cause Analysis
```
User: "Why is cancellation rate so high?"

Agent:
1. Gets overall cancellation rate
2. Breaks down by lead_source
3. Breaks down by dp_percent
4. Breaks down by development
5. Identifies root cause segments
6. Provides actionable recommendations
```

### What-If Scenario
```
User: "What if we cap discounts at 5%?"

Agent:
1. Counts units with discount > 5%
2. Calculates total discount being given
3. Projects revenue impact
4. Assesses risk by segment
5. Provides recommendation with confidence
```

## Troubleshooting

### Database connection error
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check database exists
psql -U postgres -c "\l" | grep arada
```

### Import fails
```bash
# Check CSV path
ls -la /Users/mahak/arada-ai/records_real_estate.csv

# Check CSV format
head -1 /Users/mahak/arada-ai/records_real_estate.csv
```

### MCP server not responding
```bash
# Check if port is in use
lsof -i :8002

# Check server logs
python server.py  # Look for error messages
```

## Portfolio Data Summary

| Metric | Value |
|--------|-------|
| Total Records | 1,000 bookings |
| Time Period | Aug 2021 - Dec 2025 |
| Total Portfolio Value | ~AED 5.37 Billion |
| Average Unit Price | ~AED 5.67 Million |
| Developments | 6 |
| Unit Types | 6 (Studio to Villa) |

### Developments
- DAMAC Bay
- DAMAC Hills
- DAMAC Lagoons
- Downtown Dubai
- Dubai Hills Estate
- Emaar Beachfront

### Unit Types
- Studio
- 1BR
- 2BR
- 3BR
- Townhouse
- Villa

### Lead Sources
- Event
- Digital
- Broker Network
- Direct
