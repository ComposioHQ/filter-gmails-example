"""Configuration and environment setup for Gmail Labeller application."""

import os
import logging
from dotenv import load_dotenv
from composio import Composio
from composio_openai_agents import OpenAIAgentsProvider
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
GMAIL_AUTH_CONFIG_ID: str = os.environ.get("GMAIL_AUTH_CONFIG_ID", "")
COMPOSIO_WEBHOOK_SECRET: str = os.environ.get("COMPOSIO_WEBHOOK_SECRET", "")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

# Initialize clients
composio = Composio(provider=OpenAIAgentsProvider())
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Load initial data from database
def load_initial_prompts():
    """Load initial prompts from the database."""
    try:
        response = supabase.table("prompts").select("*").execute()
        if response.data:
            user_id = response.data[0]["user_id"]
            prompt = response.data[0]["prompt"]
            logger.info(f"Loaded prompt for user {user_id}")
            return user_id, prompt
        else:
            logger.warning("No prompts found in database")
            return None, None
    except Exception as e:
        logger.error(f"Error loading prompts: {e}")
        return None, None

# Load initial data
initial_user_id, initial_prompt = load_initial_prompts()