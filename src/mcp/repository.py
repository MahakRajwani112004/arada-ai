"""MCP Server Repository - database operations for MCP servers."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.secrets import get_secrets_manager
from src.storage.models import MCPServerModel

from .catalog import get_template
from .models import MCPServerConfig, MCPServerInstance, ServerStatus


class MCPServerRepository:
    """Repository for MCP server database operations.

    Handles storing/retrieving MCP server configurations.
    Credentials are stored in vault, not in database.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def create(
        self,
        name: str,
        url: str,
        credentials: Dict[str, str],
        template: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        oauth_token_ref: Optional[str] = None,
    ) -> MCPServerInstance:
        """Create a new MCP server configuration.

        Args:
            name: User-friendly name
            url: MCP server URL
            credentials: Sensitive credentials to store in vault
            template: Optional catalog template ID
            headers: Optional non-sensitive headers
            oauth_token_ref: Optional OAuth token reference for cascade delete

        Returns:
            Created MCPServerInstance
        """
        # Generate unique ID
        server_id = f"srv_{uuid.uuid4().hex[:12]}"
        secret_ref = f"mcp/servers/{server_id}"

        # Store credentials in vault
        secrets_manager = get_secrets_manager()
        await secrets_manager.store(secret_ref, credentials)

        # Create database record
        db_model = MCPServerModel(
            id=server_id,
            name=name,
            template=template,
            url=url,
            status=ServerStatus.DISCONNECTED.value,
            secret_ref=secret_ref,
            oauth_token_ref=oauth_token_ref,
            headers_config=headers or {},
        )

        self._session.add(db_model)
        await self._session.commit()
        await self._session.refresh(db_model)

        return self._to_instance(db_model)

    async def get(self, server_id: str) -> Optional[MCPServerInstance]:
        """Get MCP server by ID.

        Args:
            server_id: Server ID

        Returns:
            MCPServerInstance or None if not found
        """
        result = await self._session.execute(
            select(MCPServerModel).where(MCPServerModel.id == server_id)
        )
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        return self._to_instance(db_model)

    async def list_all(self) -> List[MCPServerInstance]:
        """List all MCP servers.

        Returns:
            List of MCPServerInstance
        """
        result = await self._session.execute(
            select(MCPServerModel).order_by(MCPServerModel.created_at.desc())
        )
        db_models = result.scalars().all()

        return [self._to_instance(m) for m in db_models]

    async def update_status(
        self,
        server_id: str,
        status: ServerStatus,
        error_message: Optional[str] = None,
    ) -> Optional[MCPServerInstance]:
        """Update server status.

        Args:
            server_id: Server ID
            status: New status
            error_message: Optional error message

        Returns:
            Updated MCPServerInstance or None if not found
        """
        result = await self._session.execute(
            select(MCPServerModel).where(MCPServerModel.id == server_id)
        )
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        db_model.status = status.value
        db_model.error_message = error_message
        db_model.last_used_at = datetime.utcnow()

        await self._session.commit()
        await self._session.refresh(db_model)

        return self._to_instance(db_model)

    async def delete(self, server_id: str) -> bool:
        """Delete MCP server and its credentials.

        Args:
            server_id: Server ID

        Returns:
            True if deleted, False if not found
        """
        result = await self._session.execute(
            select(MCPServerModel).where(MCPServerModel.id == server_id)
        )
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return False

        # Delete credentials from vault
        secrets_manager = get_secrets_manager()
        try:
            await secrets_manager.delete(db_model.secret_ref)
        except KeyError:
            pass  # Secret already deleted

        # Delete OAuth token from vault if present (cascade delete)
        if db_model.oauth_token_ref:
            try:
                await secrets_manager.delete(db_model.oauth_token_ref)
            except KeyError:
                pass  # OAuth token already deleted

        # Delete database record
        await self._session.delete(db_model)
        await self._session.commit()

        return True

    async def update_credentials(
        self,
        server_id: str,
        credentials: Dict[str, str],
        oauth_token_ref: Optional[str] = None,
    ) -> Optional[MCPServerInstance]:
        """Update server credentials in vault.

        Args:
            server_id: Server ID
            credentials: New credentials to store
            oauth_token_ref: Optional new OAuth token reference

        Returns:
            Updated MCPServerInstance or None if not found
        """
        result = await self._session.execute(
            select(MCPServerModel).where(MCPServerModel.id == server_id)
        )
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        # Update credentials in vault
        secrets_manager = get_secrets_manager()
        await secrets_manager.store(db_model.secret_ref, credentials)

        # Delete old OAuth token if replacing with new one
        if oauth_token_ref and db_model.oauth_token_ref and db_model.oauth_token_ref != oauth_token_ref:
            try:
                await secrets_manager.delete(db_model.oauth_token_ref)
            except KeyError:
                pass

        # Update OAuth token ref if provided
        if oauth_token_ref:
            db_model.oauth_token_ref = oauth_token_ref

        db_model.status = ServerStatus.DISCONNECTED.value
        db_model.error_message = None

        await self._session.commit()
        await self._session.refresh(db_model)

        return self._to_instance(db_model)

    async def get_config(self, server_id: str) -> Optional[MCPServerConfig]:
        """Get full server config including credentials from vault.

        Args:
            server_id: Server ID

        Returns:
            MCPServerConfig with credentials as headers, or None if not found
        """
        result = await self._session.execute(
            select(MCPServerModel).where(MCPServerModel.id == server_id)
        )
        db_model = result.scalar_one_or_none()

        if db_model is None:
            return None

        # Get credentials from vault
        secrets_manager = get_secrets_manager()
        credentials = await secrets_manager.retrieve(db_model.secret_ref)

        # Build headers from credentials + stored headers
        headers = dict(db_model.headers_config)

        # Map credentials to headers based on template
        if db_model.template:
            template = get_template(db_model.template)
            if template:
                for cred_spec in template.credentials_required + template.credentials_optional:
                    if cred_spec.name in credentials and cred_spec.header_name:
                        headers[cred_spec.header_name] = credentials[cred_spec.name]

        # For custom servers, add credentials as Authorization header
        if not db_model.template and credentials:
            # If there's a single credential that looks like a token, use Bearer
            if len(credentials) == 1:
                key, value = list(credentials.items())[0]
                if key.lower() in ("token", "api_key", "bearer"):
                    headers["Authorization"] = f"Bearer {value}"
                else:
                    headers[f"X-{key}"] = value
            else:
                # Add each as X-{name} header
                for key, value in credentials.items():
                    headers[f"X-{key}"] = value

        return MCPServerConfig(
            id=db_model.id,
            name=db_model.name,
            url=db_model.url,
            headers=headers,
            template=db_model.template,
        )

    def _to_instance(self, db_model: MCPServerModel) -> MCPServerInstance:
        """Convert database model to MCPServerInstance."""
        return MCPServerInstance(
            id=db_model.id,
            name=db_model.name,
            template=db_model.template,
            url=db_model.url,
            status=ServerStatus(db_model.status),
            secret_ref=db_model.secret_ref,
            oauth_token_ref=db_model.oauth_token_ref,
            created_at=db_model.created_at,
            last_used=db_model.last_used_at,
            error_message=db_model.error_message,
        )
