"""Conversation API routes for agent chat history."""
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_conversation_repository
from src.auth.dependencies import CurrentUser
from src.api.schemas.conversation import (
    AddMessageRequest,
    AddMessageResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationSummaryResponse,
    CreateConversationRequest,
    CreateConversationResponse,
    MessageResponse,
    SendMessageRequest,
    UpdateConversationRequest,
)
from src.storage.conversation_repository import PostgresConversationRepository
from src.streaming import execute_with_streaming, StreamEventType


router = APIRouter(prefix="/conversations", tags=["conversations"])


# ==================== All Conversations (for /chat page) ====================


@router.get("", response_model=ConversationListResponse)
async def list_all_conversations(
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=100, description="Max conversations to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    include_archived: bool = Query(False, description="Include archived conversations"),
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
) -> ConversationListResponse:
    """List all conversations for the current user across all agents.

    Returns conversations sorted by most recently updated first.
    Used for the main /chat page.
    """
    conversations, total = await conversation_repo.list_all_conversations(
        limit=limit,
        offset=offset,
        include_archived=include_archived,
    )

    return ConversationListResponse(
        conversations=[
            ConversationSummaryResponse(
                id=c.id,
                agent_id=c.agent_id,
                agent_name=c.agent_name,
                agent_type=c.agent_type,
                title=c.title,
                message_count=c.message_count,
                last_message_preview=c.last_message_preview,
                last_message_at=c.last_message_at,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in conversations
        ],
        total=total,
    )


# ==================== Single Conversation ====================


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser,
    message_limit: int = Query(100, ge=1, le=500, description="Max messages to return"),
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
) -> ConversationDetailResponse:
    """Get a conversation with its messages."""
    conversation = await conversation_repo.get_conversation(
        conversation_id, message_limit=message_limit
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return ConversationDetailResponse(
        id=conversation.id,
        agent_id=conversation.agent_id,
        agent_name=conversation.agent_name,
        agent_type=conversation.agent_type,
        title=conversation.title,
        is_auto_title=conversation.is_auto_title,
        message_count=conversation.message_count,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                workflow_id=m.workflow_id,
                execution_id=m.execution_id,
                metadata=m.metadata,
                created_at=m.created_at,
            )
            for m in conversation.messages
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.patch("/{conversation_id}", response_model=ConversationSummaryResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: CurrentUser,
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
) -> ConversationSummaryResponse:
    """Update a conversation (rename)."""
    updated = await conversation_repo.update_conversation(
        conversation_id, request.title
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Fetch updated conversation to return
    conversation = await conversation_repo.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return ConversationSummaryResponse(
        id=conversation.id,
        agent_id=conversation.agent_id,
        agent_name=conversation.agent_name,
        agent_type=conversation.agent_type,
        title=conversation.title,
        message_count=conversation.message_count,
        last_message_preview=conversation.messages[-1].content[:100]
        if conversation.messages
        else None,
        last_message_at=conversation.messages[-1].created_at
        if conversation.messages
        else None,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser,
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
) -> None:
    """Delete a conversation and all its messages."""
    deleted = await conversation_repo.delete_conversation(conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )


@router.post("/{conversation_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_conversation(
    conversation_id: str,
    current_user: CurrentUser,
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
) -> None:
    """Archive a conversation (soft delete)."""
    archived = await conversation_repo.archive_conversation(conversation_id)

    if not archived:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )


# ==================== Messages ====================


@router.post("/{conversation_id}/messages", response_model=AddMessageResponse)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    current_user: CurrentUser,
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
) -> AddMessageResponse:
    """Add a message to a conversation.

    This is primarily for internal use. For chat interactions,
    use the streaming endpoint or execute workflow endpoint.
    """
    message_id = await conversation_repo.add_message(
        conversation_id=conversation_id,
        role=request.role,
        content=request.content,
        workflow_id=request.workflow_id,
        execution_id=request.execution_id,
        metadata=request.metadata,
    )

    if message_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Get the created message to return created_at
    messages = await conversation_repo.get_conversation_messages(
        conversation_id, limit=1, offset=0
    )
    # The newest message should be the last one in the list
    all_messages = await conversation_repo.get_conversation_messages(
        conversation_id, limit=1000
    )
    created_message = next((m for m in all_messages if m.id == message_id), None)

    return AddMessageResponse(
        id=message_id,
        role=request.role,
        content=request.content,
        created_at=created_message.created_at if created_message else None,
    )


# ==================== Streaming Chat ====================


@router.post("/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: str,
    request: SendMessageRequest,
    current_user: CurrentUser,
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
):
    """Stream agent response with progress events.

    This endpoint uses Server-Sent Events (SSE) to stream:
    - Progress events (thinking, retrieving, tool calls, etc.)
    - Content chunks as the response is generated
    - Completion event with final message ID

    Events are formatted as SSE with event type and JSON data.
    """
    # Verify conversation exists
    conversation = await conversation_repo.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    agent_id = conversation.agent_id

    # Build conversation history from existing messages
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in conversation.messages
    ]

    async def event_generator():
        """Generate SSE events during execution."""
        accumulated_content = ""
        message_id = None

        try:
            # Save user message first
            user_message_id = await conversation_repo.add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.content,
            )

            # Yield user message saved event
            yield {
                "event": "message_saved",
                "data": json.dumps({"role": "user", "message_id": user_message_id}),
            }

            # Execute with streaming
            async for event in execute_with_streaming(
                agent_id=agent_id,
                user_input=request.content,
                user_id=current_user.id,
                conversation_id=conversation_id,
                conversation_history=conversation_history,
            ):
                # Accumulate content chunks
                if event.type == StreamEventType.CHUNK:
                    accumulated_content += event.data.get("content", "")

                # Yield SSE event
                yield {
                    "event": event.type.value,
                    "data": json.dumps(event.data),
                }

                # On complete, save assistant message
                if event.type == StreamEventType.COMPLETE:
                    if accumulated_content:
                        message_id = await conversation_repo.add_message(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=accumulated_content,
                            execution_id=event.data.get("execution_id"),
                        )

                        # Yield final message saved event
                        yield {
                            "event": "assistant_message_saved",
                            "data": json.dumps({
                                "message_id": message_id,
                                "content_length": len(accumulated_content),
                            }),
                        }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "error_type": type(e).__name__,
                }),
            }

    return EventSourceResponse(event_generator())


# ==================== Agent-Specific Conversations ====================


agents_router = APIRouter(prefix="/agents", tags=["agents", "conversations"])


@agents_router.get("/{agent_id}/conversations", response_model=ConversationListResponse)
async def list_agent_conversations(
    agent_id: str,
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=100, description="Max conversations to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    include_archived: bool = Query(False, description="Include archived conversations"),
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
) -> ConversationListResponse:
    """List conversations for a specific agent.

    Used for the agent detail page chat tab.
    """
    conversations, total = await conversation_repo.list_agent_conversations(
        agent_id=agent_id,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
    )

    return ConversationListResponse(
        conversations=[
            ConversationSummaryResponse(
                id=c.id,
                agent_id=c.agent_id,
                agent_name=c.agent_name,
                agent_type=c.agent_type,
                title=c.title,
                message_count=c.message_count,
                last_message_preview=c.last_message_preview,
                last_message_at=c.last_message_at,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in conversations
        ],
        total=total,
    )


@agents_router.post(
    "/{agent_id}/conversations", response_model=CreateConversationResponse
)
async def create_conversation(
    agent_id: str,
    request: CreateConversationRequest,
    current_user: CurrentUser,
    conversation_repo: PostgresConversationRepository = Depends(
        get_conversation_repository
    ),
) -> CreateConversationResponse:
    """Create a new conversation for an agent."""
    from datetime import datetime, timezone

    conversation_id = await conversation_repo.create_conversation(
        agent_id=agent_id,
        title=request.title,
    )

    return CreateConversationResponse(
        id=conversation_id,
        agent_id=agent_id,
        title=request.title or "New Conversation",
        created_at=datetime.now(timezone.utc),
    )
