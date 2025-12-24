#!/usr/bin/env python3
"""CLI tool to scaffold new MCP servers.

Usage:
    python scripts/create_mcp.py <name> [options]

Examples:
    python scripts/create_mcp.py notion --tools "search_pages,create_page,update_page"
    python scripts/create_mcp.py jira --auth-type api_token --port 8010
    python scripts/create_mcp.py github --tools "list_repos,create_issue" --auth-type oauth

This creates:
    mcp_servers/<name>/
    ├── server.py          # Server class extending BaseMCPServer
    ├── requirements.txt   # Dependencies
    ├── Dockerfile         # Container setup
    └── .env.example       # Environment template

And updates:
    - src/mcp/catalog.py (adds template entry)
    - docker/docker-compose.yml (adds service)
"""
import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
MCP_SERVERS_DIR = PROJECT_ROOT / "mcp_servers"
CATALOG_FILE = PROJECT_ROOT / "src" / "mcp" / "catalog.py"
DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker" / "docker-compose.yml"


def to_class_name(name: str) -> str:
    """Convert kebab-case to PascalCase. e.g., 'google-calendar' -> 'GoogleCalendarServer'"""
    parts = name.replace("_", "-").split("-")
    return "".join(p.capitalize() for p in parts) + "Server"


def to_snake_case(name: str) -> str:
    """Convert kebab-case to snake_case. e.g., 'google-calendar' -> 'google_calendar'"""
    return name.replace("-", "_")


def to_env_var(name: str) -> str:
    """Convert to environment variable format. e.g., 'google-calendar' -> 'GOOGLE_CALENDAR'"""
    return name.replace("-", "_").upper()


def generate_server_py(
    name: str,
    description: str,
    tools: List[str],
    auth_type: str,
) -> str:
    """Generate server.py content."""
    class_name = to_class_name(name)
    env_prefix = to_env_var(name)

    # Determine credential headers based on auth type
    if auth_type == "oauth":
        credential_headers = f'''credential_headers=[
            "X-{name.title().replace("-", "-")}-Refresh-Token",
        ]'''
        cred_doc = f"X-{name.title().replace('-', '-')}-Refresh-Token: OAuth refresh token"
    elif auth_type == "api_token":
        credential_headers = f'''credential_headers=[
            "X-{name.title().replace("-", "-")}-Api-Token",
        ]'''
        cred_doc = f"X-{name.title().replace('-', '-')}-Api-Token: API token"
    else:
        credential_headers = "credential_headers=[]"
        cred_doc = "No credentials required"

    # Generate tool stubs
    tool_methods = []
    for tool in tools:
        tool_method = f'''
    @tool(
        name="{tool}",
        description="TODO: Add description for {tool}",
        input_schema={{
            "type": "object",
            "properties": {{
                # TODO: Define input parameters
            }},
        }},
        {credential_headers},
    )
    async def {tool}(
        self,
        credentials: Dict[str, str],
        **kwargs,
    ) -> Dict[str, Any]:
        """TODO: Implement {tool}."""
        self.logger.info("{tool}_called", params=kwargs)

        # TODO: Implement tool logic
        raise NotImplementedError("{tool} not implemented yet")
'''
        tool_methods.append(tool_method)

    tools_code = "\n".join(tool_methods)

    return f'''"""{name.replace("-", " ").title()} MCP Server.

{description}

Tools:
{chr(10).join(f"- {t}: TODO: Add description" for t in tools)}

Credentials passed via HTTP header:
- {cred_doc}
"""
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseMCPServer, tool


class {class_name}(BaseMCPServer):
    """{name.replace("-", " ").title()} MCP Server."""

    def __init__(self):
        super().__init__(
            name="{name}",
            version="1.0.0",
            description="{description}",
        )
{tools_code}

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="{class_name}")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    server = {class_name}()
    server.run(host=args.host, port=args.port)
'''


def generate_requirements_txt(name: str, auth_type: str) -> str:
    """Generate requirements.txt content."""
    base_deps = """# {name} MCP Server
fastapi>=0.109.0
uvicorn>=0.27.0
python-dotenv>=1.0.0
structlog>=24.1.0
httpx>=0.27.0
"""

    # Add auth-specific dependencies
    extra_deps = ""
    if auth_type == "oauth":
        extra_deps = """
# OAuth dependencies
# TODO: Add OAuth library for your provider
"""
    elif auth_type == "api_token":
        extra_deps = """
# API client dependencies
# TODO: Add API client library for your service
"""

    return base_deps.format(name=name.replace("-", " ").title()) + extra_deps


def generate_dockerfile(name: str, port: int) -> str:
    """Generate Dockerfile content."""
    return f'''FROM python:3.11-slim

WORKDIR /app

# Copy base server
COPY ../base.py /app/base.py

# Copy server implementation
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py /app/server.py
COPY .env /app/.env 2>/dev/null || true

EXPOSE {port}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

CMD ["python", "server.py", "--port", "{port}"]
'''


def generate_env_example(name: str, auth_type: str) -> str:
    """Generate .env.example content."""
    env_prefix = to_env_var(name)

    base = f"""# {name.replace("-", " ").title()} MCP Server Configuration

# Server settings
LOG_LEVEL=INFO
"""

    if auth_type == "oauth":
        base += f"""
# OAuth Configuration
{env_prefix}_CLIENT_ID=your-client-id
{env_prefix}_CLIENT_SECRET=your-client-secret
"""
    elif auth_type == "api_token":
        base += f"""
# API Configuration
{env_prefix}_API_URL=https://api.example.com
"""

    return base


def get_next_port() -> int:
    """Determine the next available port based on existing MCP servers."""
    used_ports = set()

    # Check catalog for existing URLs
    if CATALOG_FILE.exists():
        content = CATALOG_FILE.read_text()
        # Find port numbers in URLs like http://localhost:800X/mcp
        ports = re.findall(r"localhost:(\d+)/mcp", content)
        used_ports.update(int(p) for p in ports)

    # Start from 8001 and find next available
    port = 8001
    while port in used_ports:
        port += 1

    return port


def update_catalog(
    name: str,
    description: str,
    tools: List[str],
    auth_type: str,
    port: int,
) -> None:
    """Update src/mcp/catalog.py with new template."""
    if not CATALOG_FILE.exists():
        print(f"Warning: Catalog file not found at {CATALOG_FILE}")
        return

    content = CATALOG_FILE.read_text()
    env_var_name = f"MCP_{to_env_var(name)}_URL"

    # Add URL constant if not exists
    url_line = f'{env_var_name} = os.getenv("{env_var_name}", "http://localhost:{port}/mcp")'

    # Find where to insert URL constant (after existing MCP_*_URL lines)
    url_section_match = re.search(r"(MCP_\w+_URL = os\.getenv.*\n)+", content)
    if url_section_match and env_var_name not in content:
        insert_pos = url_section_match.end()
        content = content[:insert_pos] + url_line + "\n" + content[insert_pos:]

    # Generate credential spec based on auth type
    if auth_type == "oauth":
        cred_spec = f'''CredentialSpec(
            name="{to_env_var(name)}_REFRESH_TOKEN",
            description="OAuth refresh token",
            sensitive=True,
            header_name="X-{name.title().replace("-", "-")}-Refresh-Token",
        )'''
    elif auth_type == "api_token":
        cred_spec = f'''CredentialSpec(
            name="{to_env_var(name)}_API_TOKEN",
            description="API token",
            sensitive=True,
            header_name="X-{name.title().replace("-", "-")}-Api-Token",
        )'''
    else:
        cred_spec = ""

    # Generate template entry
    template_entry = f'''
    "{name}": MCPServerTemplate(
        id="{name}",
        name="{name.replace("-", " ").title()}",
        url_template={env_var_name},
        auth_type="{auth_type if auth_type != "oauth" else "oauth_token"}",
        scopes=[],
        credentials_required=[{cred_spec}] if "{auth_type}" != "none" else [],
        tools={tools},
    ),'''

    # Find the end of MCP_SERVER_CATALOG dict and insert before closing brace
    # Look for the last entry before the closing }
    catalog_pattern = r"(MCP_SERVER_CATALOG: Dict\[str, MCPServerTemplate\] = \{.*?)(^\})"
    match = re.search(catalog_pattern, content, re.MULTILINE | re.DOTALL)

    if match and f'"{name}":' not in content:
        # Insert before the closing brace
        insert_pos = match.end(1)
        content = content[:insert_pos] + template_entry + "\n" + content[insert_pos:]

        CATALOG_FILE.write_text(content)
        print(f"✓ Updated {CATALOG_FILE}")
    else:
        print(f"⚠ Could not update catalog (entry may already exist)")


def update_docker_compose(name: str, port: int) -> None:
    """Update docker/docker-compose.yml with new service."""
    if not DOCKER_COMPOSE_FILE.exists():
        print(f"Warning: Docker compose file not found at {DOCKER_COMPOSE_FILE}")
        return

    content = DOCKER_COMPOSE_FILE.read_text()
    service_name = f"mcp-{name}"

    if service_name in content:
        print(f"⚠ Service {service_name} already exists in docker-compose.yml")
        return

    # Generate service entry
    service_entry = f'''
  # MCP Server: {name.replace("-", " ").title()}
  {service_name}:
    build:
      context: ../mcp_servers/{name}
      dockerfile: Dockerfile
    container_name: magure-{service_name}
    ports:
      - "{port}:{port}"
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
'''

    # Find the volumes section and insert before it
    volumes_match = re.search(r"^volumes:", content, re.MULTILINE)
    if volumes_match:
        insert_pos = volumes_match.start()
        content = content[:insert_pos] + service_entry + "\n" + content[insert_pos:]

        DOCKER_COMPOSE_FILE.write_text(content)
        print(f"✓ Updated {DOCKER_COMPOSE_FILE}")
    else:
        # Append to end if no volumes section
        content += service_entry
        DOCKER_COMPOSE_FILE.write_text(content)
        print(f"✓ Updated {DOCKER_COMPOSE_FILE}")


def create_mcp_server(
    name: str,
    description: str,
    tools: List[str],
    auth_type: str,
    port: Optional[int] = None,
    skip_catalog: bool = False,
    skip_docker: bool = False,
) -> None:
    """Create a new MCP server with all required files."""
    # Validate name
    if not re.match(r"^[a-z][a-z0-9-]*$", name):
        print(f"Error: Name must be lowercase alphanumeric with hyphens (e.g., 'my-service')")
        sys.exit(1)

    # Determine port
    if port is None:
        port = get_next_port()

    # Create directory
    server_dir = MCP_SERVERS_DIR / name
    if server_dir.exists():
        print(f"Error: Directory {server_dir} already exists")
        sys.exit(1)

    server_dir.mkdir(parents=True)
    print(f"✓ Created {server_dir}")

    # Generate files
    files = {
        "server.py": generate_server_py(name, description, tools, auth_type),
        "requirements.txt": generate_requirements_txt(name, auth_type),
        "Dockerfile": generate_dockerfile(name, port),
        ".env.example": generate_env_example(name, auth_type),
    }

    for filename, content in files.items():
        filepath = server_dir / filename
        filepath.write_text(content)
        print(f"✓ Created {filepath}")

    # Update catalog
    if not skip_catalog:
        update_catalog(name, description, tools, auth_type, port)

    # Update docker-compose
    if not skip_docker:
        update_docker_compose(name, port)

    # Print summary
    print(f"""
{'='*60}
MCP Server '{name}' created successfully!
{'='*60}

Directory: {server_dir}
Port: {port}
Auth: {auth_type}
Tools: {', '.join(tools)}

Next steps:
1. Implement the tool methods in {server_dir}/server.py
2. Add any required dependencies to requirements.txt
3. Copy .env.example to .env and configure credentials

To run locally:
    cd {server_dir}
    pip install -r requirements.txt
    python server.py --port {port}

To run with Docker:
    docker-compose -f docker/docker-compose.yml up {f"mcp-{name}"}
""")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s notion --tools "search_pages,create_page"
    %(prog)s jira --auth-type api_token --port 8010
    %(prog)s github --tools "list_repos,create_issue" --auth-type oauth
        """,
    )

    parser.add_argument(
        "name",
        help="Server name in kebab-case (e.g., 'google-sheets', 'notion')",
    )
    parser.add_argument(
        "--description", "-d",
        default="",
        help="Server description",
    )
    parser.add_argument(
        "--tools", "-t",
        default="",
        help="Comma-separated list of tool names (e.g., 'list_items,create_item')",
    )
    parser.add_argument(
        "--auth-type", "-a",
        choices=["oauth", "api_token", "none"],
        default="api_token",
        help="Authentication type (default: api_token)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Port number (auto-assigned if not specified)",
    )
    parser.add_argument(
        "--skip-catalog",
        action="store_true",
        help="Don't update catalog.py",
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Don't update docker-compose.yml",
    )

    args = parser.parse_args()

    # Parse tools
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    if not tools:
        tools = ["example_tool"]  # Default tool

    # Set default description
    description = args.description or f"{args.name.replace('-', ' ').title()} integration"

    create_mcp_server(
        name=args.name,
        description=description,
        tools=tools,
        auth_type=args.auth_type,
        port=args.port,
        skip_catalog=args.skip_catalog,
        skip_docker=args.skip_docker,
    )


if __name__ == "__main__":
    main()
