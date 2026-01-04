"""Microsoft Teams webhook handler.

This module handles incoming activities from Microsoft Teams
and routes them to appropriate agents.
"""
import structlog
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import (
    TeamsConfigurationModel,
    TeamsConversationModel,
    TeamsMessageModel,
)
from .client import TeamsClient

logger = structlog.get_logger(__name__)


class TeamsHandler:
    """Handler for Microsoft Teams Bot Framework activities.

    Processes incoming webhooks from Teams and routes messages to agents.
    """

    def __init__(self, session: AsyncSession, workflow_executor=None):
        """Initialize Teams handler.

        Args:
            session: Database session
            workflow_executor: Optional workflow executor for running agents
        """
        self.session = session
        self.workflow_executor = workflow_executor
        self._clients: Dict[str, TeamsClient] = {}

    async def get_client(self, config: TeamsConfigurationModel, app_password: str) -> TeamsClient:
        """Get or create a Teams client for a configuration.

        Args:
            config: Teams configuration
            app_password: Decrypted app password

        Returns:
            TeamsClient instance
        """
        if config.id not in self._clients:
            self._clients[config.id] = TeamsClient(
                app_id=config.app_id,
                app_password=app_password,
                tenant_id=config.tenant_id,
            )
        return self._clients[config.id]

    async def handle_activity(
        self,
        activity: Dict[str, Any],
        config: TeamsConfigurationModel,
        app_password: str,
    ) -> Optional[Dict[str, Any]]:
        """Handle an incoming activity from Teams.

        Args:
            activity: Bot Framework activity payload
            config: Teams configuration for this bot
            app_password: Decrypted app password

        Returns:
            Response to send back to Teams (if any)
        """
        activity_type = activity.get("type", "")

        logger.info(
            "teams_activity_received",
            activity_type=activity_type,
            conversation_id=activity.get("conversation", {}).get("id"),
        )

        if activity_type == "message":
            return await self._handle_message(activity, config, app_password)
        elif activity_type == "conversationUpdate":
            return await self._handle_conversation_update(activity, config, app_password)
        elif activity_type == "invoke":
            return await self._handle_invoke(activity, config, app_password)
        else:
            logger.debug("teams_activity_ignored", activity_type=activity_type)
            return None

    async def _handle_message(
        self,
        activity: Dict[str, Any],
        config: TeamsConfigurationModel,
        app_password: str,
    ) -> Optional[Dict[str, Any]]:
        """Handle a message activity.

        Args:
            activity: Message activity
            config: Teams configuration
            app_password: Decrypted app password

        Returns:
            Response activity
        """
        conversation_data = activity.get("conversation", {})
        conversation_id = conversation_data.get("id", "")
        service_url = activity.get("serviceUrl", "")
        sender = activity.get("from", {})
        text = activity.get("text", "").strip()

        # Remove bot mention from text if present
        text = self._remove_bot_mention(text, activity)

        if not text:
            logger.debug("teams_empty_message_ignored")
            return None

        # Get or create conversation record
        conversation = await self._get_or_create_conversation(
            config=config,
            conversation_id=conversation_id,
            conversation_data=conversation_data,
            service_url=service_url,
            activity=activity,
        )

        # Store incoming message
        incoming_message = TeamsMessageModel(
            conversation_id=conversation.id,
            teams_message_id=activity.get("id"),
            sender_id=sender.get("id", "unknown"),
            sender_name=sender.get("name"),
            is_from_bot=False,
            content=text,
            content_type="text",
            metadata_json={"activity_id": activity.get("id")},
        )
        self.session.add(incoming_message)

        # Update conversation last message time
        conversation.last_message_at = datetime.now(timezone.utc)
        await self.session.commit()

        # Get Teams client
        client = await self.get_client(config, app_password)

        # Send typing indicator
        await client.send_typing_indicator(
            service_url=service_url,
            conversation_id=conversation_id,
        )

        # Execute agent workflow
        response_text = await self._execute_agent(
            text=text,
            conversation=conversation,
            config=config,
        )

        # Send response back to Teams
        if response_text:
            result = await client.send_message(
                service_url=service_url,
                conversation_id=conversation_id,
                message=response_text,
                reply_to_id=activity.get("id"),
            )

            # Store outgoing message
            outgoing_message = TeamsMessageModel(
                conversation_id=conversation.id,
                teams_message_id=result.get("id"),
                sender_id=config.app_id,
                sender_name="MagoneAI Bot",
                is_from_bot=True,
                content=response_text,
                content_type="text",
                metadata_json={"activity_id": result.get("id")},
            )
            self.session.add(outgoing_message)
            await self.session.commit()

        return None

    async def _handle_conversation_update(
        self,
        activity: Dict[str, Any],
        config: TeamsConfigurationModel,
        app_password: str,
    ) -> Optional[Dict[str, Any]]:
        """Handle a conversation update activity (member added/removed).

        Args:
            activity: Conversation update activity
            config: Teams configuration
            app_password: Decrypted app password

        Returns:
            Response activity
        """
        members_added = activity.get("membersAdded", [])
        bot_id = activity.get("recipient", {}).get("id")

        # Check if bot was added to the conversation
        for member in members_added:
            if member.get("id") == bot_id:
                logger.info("teams_bot_added_to_conversation")

                # Store conversation reference
                conversation_data = activity.get("conversation", {})
                conversation_id = conversation_data.get("id", "")
                service_url = activity.get("serviceUrl", "")

                await self._get_or_create_conversation(
                    config=config,
                    conversation_id=conversation_id,
                    conversation_data=conversation_data,
                    service_url=service_url,
                    activity=activity,
                )

                # Send welcome message
                client = await self.get_client(config, app_password)
                await client.send_message(
                    service_url=service_url,
                    conversation_id=conversation_id,
                    message="Hello! I'm your MagoneAI assistant. How can I help you today?",
                )
                break

        return None

    async def _handle_invoke(
        self,
        activity: Dict[str, Any],
        config: TeamsConfigurationModel,
        app_password: str,
    ) -> Optional[Dict[str, Any]]:
        """Handle an invoke activity (actions, cards, etc.).

        Args:
            activity: Invoke activity
            config: Teams configuration
            app_password: Decrypted app password

        Returns:
            Response for invoke
        """
        invoke_name = activity.get("name", "")
        logger.info("teams_invoke_received", invoke_name=invoke_name)

        # For now, just acknowledge invokes
        return {"status": 200}

    async def _get_or_create_conversation(
        self,
        config: TeamsConfigurationModel,
        conversation_id: str,
        conversation_data: Dict[str, Any],
        service_url: str,
        activity: Dict[str, Any],
    ) -> TeamsConversationModel:
        """Get or create a conversation record.

        Args:
            config: Teams configuration
            conversation_id: Teams conversation ID
            conversation_data: Conversation data from activity
            service_url: Bot Framework service URL
            activity: Full activity for reference

        Returns:
            TeamsConversationModel
        """
        # Check if conversation exists
        stmt = select(TeamsConversationModel).where(
            TeamsConversationModel.config_id == config.id,
            TeamsConversationModel.conversation_id == conversation_id,
        )
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            # Update service URL if changed
            if conversation.service_url != service_url:
                conversation.service_url = service_url
                conversation.reference_json = self._build_reference(activity)
                await self.session.commit()
            return conversation

        # Create new conversation
        conversation = TeamsConversationModel(
            config_id=config.id,
            conversation_id=conversation_id,
            channel_id=conversation_data.get("channelId"),
            team_id=conversation_data.get("teamId"),
            service_url=service_url,
            conversation_type=conversation_data.get("conversationType", "personal"),
            reference_json=self._build_reference(activity),
            agent_id=config.default_agent_id,
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)

        logger.info(
            "teams_conversation_created",
            conversation_id=conversation.id,
            teams_conversation_id=conversation_id,
        )
        return conversation

    def _build_reference(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Build a conversation reference from an activity.

        Args:
            activity: Bot Framework activity

        Returns:
            Conversation reference for proactive messaging
        """
        return {
            "activityId": activity.get("id"),
            "user": activity.get("from"),
            "bot": activity.get("recipient"),
            "conversation": activity.get("conversation"),
            "channelId": activity.get("channelId"),
            "serviceUrl": activity.get("serviceUrl"),
        }

    def _remove_bot_mention(self, text: str, activity: Dict[str, Any]) -> str:
        """Remove bot @mention from message text.

        Args:
            text: Original message text
            activity: Full activity

        Returns:
            Text with bot mention removed
        """
        entities = activity.get("entities", [])
        bot_id = activity.get("recipient", {}).get("id", "")

        for entity in entities:
            if entity.get("type") == "mention":
                mentioned = entity.get("mentioned", {})
                if mentioned.get("id") == bot_id:
                    # Remove the mention text
                    mention_text = entity.get("text", "")
                    text = text.replace(mention_text, "").strip()

        return text

    async def _execute_agent(
        self,
        text: str,
        conversation: TeamsConversationModel,
        config: TeamsConfigurationModel,
    ) -> str:
        """Execute an agent workflow for the message.

        Args:
            text: User message text
            conversation: Conversation record
            config: Teams configuration

        Returns:
            Agent response text
        """
        agent_id = conversation.agent_id or config.default_agent_id

        if not agent_id:
            return "I'm not configured with an agent yet. Please contact your administrator."

        if not self.workflow_executor:
            logger.warning("teams_workflow_executor_not_configured")
            return "I received your message but workflow execution is not configured."

        try:
            # Execute the agent workflow
            result = await self.workflow_executor.execute(
                agent_id=agent_id,
                user_input=text,
                context={
                    "channel": "teams",
                    "conversation_id": conversation.id,
                    "conversation_type": conversation.conversation_type,
                },
            )

            return result.get("response", "I processed your request but have no response.")

        except Exception as e:
            logger.exception("teams_agent_execution_failed", error=str(e))
            return f"I encountered an error processing your request: {str(e)}"
