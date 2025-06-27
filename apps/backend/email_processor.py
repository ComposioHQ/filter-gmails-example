"""Email processing logic with AI for Gmail labelling."""

import logging

from composio.core.models.connected_accounts import ConnectionRequest
from models import GmailMessage
from config import composio, supabase
from agents import Agent, Runner
from prompts import REAPER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def process_gmail_message(message: GmailMessage, user_filter: str):
    """
    Process Gmail message with AI and apply labels.

    Args:
        message: The Gmail message to process
        user_filter: The user's custom prompt/filter for email categorization

    Returns:
        bool: True if processing succeeded, False otherwise
    """
    email_id = getattr(message, "id", "unknown")

    try:
        # Validate message has required fields
        if not message.user_id:
            logger.error(f"Email {email_id} missing user_id")
            return False

        if not message.connection_id:
            logger.error(f"Email {email_id} missing connection_id")
            return False

        logger.info(f"Processing email: {message.subject} from {message.sender}")
        logger.info(f"User: {message.user_id}, Connection: {message.connection_id}")
        logger.debug(f"Email labels: {message.labels}")

        # Log email content preview for debugging
        body_preview = (message.text_body or message.html_body or "")[:10000]
        if body_preview:
            logger.debug(f"Email body preview: {body_preview}...")
        else:
            logger.warning(f"Email {email_id} has no text or HTML body")

        # Get Gmail tools for the specific user
        logger.debug(f"Fetching Gmail tools for user {message.user_id}")
        tools = composio.tools.get(
            message.user_id,
            tools=[
                "GMAIL_ADD_LABEL_TO_EMAIL",
                "GMAIL_MODIFY_THREAD_LABELS",
                "GMAIL_PATCH_LABEL",
                "GMAIL_REMOVE_LABEL",
                "GMAIL_CREATE_LABEL",
                "GMAIL_LIST_LABELS",
            ],
        )

        if not tools:
            logger.error(f"No Gmail tools available for user {message.user_id}")
            return False

        # Create the Gmail Reaper agent
        logger.debug("Creating Gmail Reaper agent")
        reaper = Agent(
            name="Gmail Reaper",
            instructions=REAPER_SYSTEM_PROMPT,
            tools=tools,
        )

        # Prepare the prompt with user filter and email details
        email_content = message.text_body or message.html_body or "No content available"
        prompt_details = (
            f"{user_filter}\n\n## Email\n{email_content}\n## Message ID\n{message.id}"
        )

        logger.debug(
            f"Running agent with prompt length: {len(prompt_details)} characters"
        )

        # Run the agent to process and label the email
        result = await Runner.run(reaper, prompt_details)

        logger.info(f"Successfully processed email {message.id}")
        logger.debug(f"Agent result: {result}")

        return True

    except Exception as e:
        logger.error(f"Error processing email {email_id}: {e}")
        logger.exception("Full error traceback:")

        # Log additional context for debugging
        logger.error(
            f"Failed email details - Subject: {getattr(message, 'subject', 'N/A')}, "
            f"Sender: {getattr(message, 'sender', 'N/A')}, "
            f"User: {getattr(message, 'user_id', 'N/A')}"
        )

        return False


def get_user_prompt(user_id: str, default_prompt: str) -> str:
    """
    Get the user's custom prompt from the database.

    Args:
        user_id: The user ID to fetch the prompt for
        default_prompt: The default prompt to use if no custom prompt is found

    Returns:
        str: The user's custom prompt or the default prompt
    """
    try:
        prompt_response = (
            supabase.table("prompts").select("*").eq("user_id", user_id).execute()
        )

        if prompt_response.data:
            prompt = prompt_response.data[0]["prompt"]
            logger.info(f"Using custom prompt for user {user_id}")
            return prompt
        else:
            logger.info(f"No custom prompt found for user {user_id}, using default")
            return default_prompt

    except Exception as e:
        logger.error(f"Error fetching user prompt: {e}")
        return default_prompt


def create_trigger(
    user_id: str,
    connection_request: ConnectionRequest,
    trigger_config: dict | None = None,
):
    """
    Create a Gmail trigger for new messages.

    Args:
        user_id: The user ID to create the trigger for
        trigger_config: Optional trigger configuration, defaults to monitoring INBOX

    Returns:
        The trigger creation response or None if failed
    """
    connection_request.wait_for_connection(timeout=30)
    if trigger_config is None:
        trigger_config = {
            "interval": 1,  # Check every minute
            "labelids": "INBOX",  # Monitor inbox only
            "userId": "me",  # Current authenticated user
        }

    try:
        logger.info(f"Creating Gmail trigger for user: {user_id}")
        logger.info(f"Trigger config: {trigger_config}")

        # Create the trigger
        response = composio.triggers.create(
            user_id=user_id,
            slug="GMAIL_NEW_GMAIL_MESSAGE",
            trigger_config=trigger_config,
        )

        logger.info(f"Successfully created trigger for user {user_id}: {response}")
        return response

    except Exception as e:
        logger.error(f"Failed to create trigger for user {user_id}: {e}")
        logger.exception("Trigger creation error details:")
        return None
