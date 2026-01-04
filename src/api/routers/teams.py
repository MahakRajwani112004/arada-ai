"""Microsoft Teams integration API routes.

Provides endpoints for:
- Teams bot webhook (incoming messages from Teams)
- Teams configuration management
- Conversation management
"""
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.channels.teams.handler import TeamsHandler
from src.config.logging import get_logger
from src.storage.database import get_session
from src.storage.models import TeamsConfigurationModel, TeamsConversationModel
from src.secrets import get_secrets_manager

router = APIRouter(prefix="/teams", tags=["teams"])
logger = get_logger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================


class TeamsConfigCreate(BaseModel):
    """Request to create a Teams configuration."""

    app_id: str = Field(..., description="Microsoft App ID")
    app_password: str = Field(..., description="Microsoft App Password (will be stored in vault)")
    tenant_id: Optional[str] = Field(None, description="Azure AD Tenant ID")
    default_agent_id: Optional[str] = Field(None, description="Default agent for conversations")


class TeamsConfigResponse(BaseModel):
    """Teams configuration response."""

    id: str
    app_id: str
    tenant_id: Optional[str]
    default_agent_id: Optional[str]
    is_active: bool
    webhook_url: str


class TeamsConversationResponse(BaseModel):
    """Teams conversation response."""

    id: str
    conversation_id: str
    conversation_type: str
    agent_id: Optional[str]
    last_message_at: Optional[str]


class UpdateConversationAgent(BaseModel):
    """Request to update conversation agent."""

    agent_id: str


# =============================================================================
# Webhook Endpoint (called by Microsoft Teams)
# =============================================================================


@router.post("/webhook/{config_id}")
async def teams_webhook(
    config_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Handle incoming activities from Microsoft Teams.

    This endpoint is called by the Bot Framework when users interact
    with the bot in Teams.

    Args:
        config_id: Teams configuration ID
        request: FastAPI request with Bot Framework activity

    Returns:
        Response based on activity type
    """
    try:
        # Get the activity payload
        activity = await request.json()
        activity_type = activity.get("type", "")

        logger.info(
            "teams_webhook_received",
            config_id=config_id,
            activity_type=activity_type,
        )

        # Get Teams configuration
        stmt = select(TeamsConfigurationModel).where(
            TeamsConfigurationModel.id == config_id,
            TeamsConfigurationModel.is_active == True,
        )
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            logger.warning("teams_config_not_found", config_id=config_id)
            raise HTTPException(status_code=404, detail="Teams configuration not found")

        # Get app password from secrets manager
        secrets = get_secrets_manager()
        secret_data = await secrets.retrieve(config.app_password_ref)
        app_password = secret_data.get("password") if secret_data else None

        if not app_password:
            logger.error("teams_password_not_found", config_id=config_id)
            raise HTTPException(status_code=500, detail="Teams credentials not configured")

        # Create handler and process activity
        handler = TeamsHandler(session=session)
        response = await handler.handle_activity(
            activity=activity,
            config=config,
            app_password=app_password,
        )

        if response:
            return response

        # Return 200 OK for successful processing
        return Response(status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("teams_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Configuration Management Endpoints
# =============================================================================


@router.post("/configurations", response_model=TeamsConfigResponse)
async def create_teams_config(
    config: TeamsConfigCreate,
    current_user: CurrentUser,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Create a new Teams bot configuration.

    Stores the app credentials and creates a webhook URL for Teams.
    """
    try:
        # Store app password in secrets manager
        secrets = get_secrets_manager()
        password_ref = f"teams/{current_user.id}/{config.app_id}"
        await secrets.store(password_ref, {"password": config.app_password})

        # Create configuration
        db_config = TeamsConfigurationModel(
            user_id=current_user.id,
            app_id=config.app_id,
            app_password_ref=password_ref,
            tenant_id=config.tenant_id,
            default_agent_id=config.default_agent_id,
            is_active=True,
        )
        session.add(db_config)
        await session.commit()
        await session.refresh(db_config)

        # Build webhook URL
        base_url = str(request.base_url).rstrip("/")
        webhook_url = f"{base_url}/api/v1/teams/webhook/{db_config.id}"

        logger.info(
            "teams_config_created",
            config_id=db_config.id,
            webhook_url=webhook_url,
        )

        return TeamsConfigResponse(
            id=db_config.id,
            app_id=db_config.app_id,
            tenant_id=db_config.tenant_id,
            default_agent_id=db_config.default_agent_id,
            is_active=db_config.is_active,
            webhook_url=webhook_url,
        )

    except Exception as e:
        logger.exception("teams_config_create_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configurations", response_model=List[TeamsConfigResponse])
async def list_teams_configs(
    current_user: CurrentUser,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """List all Teams configurations for the current user."""
    stmt = select(TeamsConfigurationModel).where(
        TeamsConfigurationModel.user_id == current_user.id,
    )
    result = await session.execute(stmt)
    configs = result.scalars().all()

    base_url = str(request.base_url).rstrip("/")

    return [
        TeamsConfigResponse(
            id=c.id,
            app_id=c.app_id,
            tenant_id=c.tenant_id,
            default_agent_id=c.default_agent_id,
            is_active=c.is_active,
            webhook_url=f"{base_url}/api/v1/teams/webhook/{c.id}",
        )
        for c in configs
    ]


@router.get("/configurations/{config_id}", response_model=TeamsConfigResponse)
async def get_teams_config(
    config_id: str,
    current_user: CurrentUser,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific Teams configuration."""
    stmt = select(TeamsConfigurationModel).where(
        TeamsConfigurationModel.id == config_id,
        TeamsConfigurationModel.user_id == current_user.id,
    )
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    base_url = str(request.base_url).rstrip("/")

    return TeamsConfigResponse(
        id=config.id,
        app_id=config.app_id,
        tenant_id=config.tenant_id,
        default_agent_id=config.default_agent_id,
        is_active=config.is_active,
        webhook_url=f"{base_url}/api/v1/teams/webhook/{config.id}",
    )


@router.delete("/configurations/{config_id}")
async def delete_teams_config(
    config_id: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Delete a Teams configuration."""
    stmt = select(TeamsConfigurationModel).where(
        TeamsConfigurationModel.id == config_id,
        TeamsConfigurationModel.user_id == current_user.id,
    )
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Delete from secrets manager
    try:
        secrets = get_secrets_manager()
        await secrets.delete(config.app_password_ref)
    except Exception as e:
        logger.warning("teams_secrets_delete_failed", error=str(e))

    await session.delete(config)
    await session.commit()

    return {"message": "Configuration deleted"}


# =============================================================================
# Conversation Management Endpoints
# =============================================================================


@router.get("/configurations/{config_id}/conversations", response_model=List[TeamsConversationResponse])
async def list_conversations(
    config_id: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """List conversations for a Teams configuration."""
    # Verify user owns the config
    config_stmt = select(TeamsConfigurationModel).where(
        TeamsConfigurationModel.id == config_id,
        TeamsConfigurationModel.user_id == current_user.id,
    )
    config_result = await session.execute(config_stmt)
    if not config_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Configuration not found")

    stmt = select(TeamsConversationModel).where(
        TeamsConversationModel.config_id == config_id,
    ).order_by(TeamsConversationModel.last_message_at.desc())

    result = await session.execute(stmt)
    conversations = result.scalars().all()

    return [
        TeamsConversationResponse(
            id=c.id,
            conversation_id=c.conversation_id,
            conversation_type=c.conversation_type,
            agent_id=c.agent_id,
            last_message_at=c.last_message_at.isoformat() if c.last_message_at else None,
        )
        for c in conversations
    ]


@router.patch("/conversations/{conversation_id}/agent")
async def update_conversation_agent(
    conversation_id: str,
    update: UpdateConversationAgent,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Update the agent for a specific conversation."""
    # Get conversation with config check
    stmt = (
        select(TeamsConversationModel)
        .join(TeamsConfigurationModel)
        .where(
            TeamsConversationModel.id == conversation_id,
            TeamsConfigurationModel.user_id == current_user.id,
        )
    )
    result = await session.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.agent_id = update.agent_id
    await session.commit()

    return {"message": "Agent updated", "agent_id": update.agent_id}


# =============================================================================
# Send Message Endpoint (for proactive messaging)
# =============================================================================


class SendMessageRequest(BaseModel):
    """Request to send a message to a Teams conversation."""

    message: str = Field(..., description="Message text to send")


@router.post("/conversations/{conversation_id}/send")
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Send a proactive message to a Teams conversation.

    Use this to send messages to Teams outside of the normal
    request-response flow.
    """
    # Get conversation with config
    stmt = (
        select(TeamsConversationModel, TeamsConfigurationModel)
        .join(TeamsConfigurationModel)
        .where(
            TeamsConversationModel.id == conversation_id,
            TeamsConfigurationModel.user_id == current_user.id,
        )
    )
    result = await session.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation, config = row

    # Get app password from secrets manager
    secrets = get_secrets_manager()
    secret_data = await secrets.retrieve(config.app_password_ref)
    app_password = secret_data.get("password") if secret_data else None

    if not app_password:
        raise HTTPException(status_code=500, detail="Teams credentials not configured")

    # Create handler and send message
    handler = TeamsHandler(session=session)
    client = await handler.get_client(config, app_password)

    result = await client.send_message(
        service_url=conversation.service_url,
        conversation_id=conversation.conversation_id,
        message=request.message,
    )

    return {
        "message": "Message sent",
        "teams_message_id": result.get("id"),
    }
