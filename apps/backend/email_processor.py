"""Email processing logic with AI for Gmail labelling."""

import logging
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
    """
    try:
        logger.info(f"Processing email: {message.subject} from {message.sender}")
        logger.info(f"User: {message.user_id}, Connection: {message.connection_id}")
        
        logger.info(f"Email body preview: {(message.text_body or '')[:200]}...")
        
        # Get Gmail tools for the specific user
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
        
        # Create the Gmail Reaper agent
        reaper = Agent(
            name="Gmail Reaper",
            instructions=REAPER_SYSTEM_PROMPT,
            tools=tools,
        )
        
        # Prepare the prompt with user filter and email details
        prompt_details = f"{user_filter}\n\n## Email\n{message.text_body or message.html_body}\n## Message ID\n{message.id}"
        
        # Run the agent to process and label the email
        await Runner.run(reaper, prompt_details)
        
        logger.info(f"Successfully processed email {message.id}")
        
    except Exception as e:
        logger.error(f"Error processing email {message.id}: {e}")
        # Could implement retry logic or dead letter queue here


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
            supabase.table("prompts")
            .select("*")
            .eq("user_id", user_id)
            .execute()
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