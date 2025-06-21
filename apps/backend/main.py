import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from config import ALLOWED_ORIGINS, initial_prompt
from models import GmailMessage
from webhook import verify_webhook_signature
from email_processor import process_gmail_message, get_user_prompt
from routes import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.post("/composio/webhook")
async def listen_webhooks(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint for processing Gmail new message events.
    This is the core webhook labeling functionality.
    """
    # Verify webhook signature
    body, webhook_id = await verify_webhook_signature(request)
    
    # Parse the JSON body
    webhook_data = await request.json()
    
    # Log webhook receipt
    logger.info(f"Webhook received: {webhook_data.get('type', 'unknown')}")
    
    # Check if this is a Gmail new message event
    if (
        webhook_data.get("type") == "gmail_new_message"
        or "gmail" in webhook_data.get("type", "").lower()
    ):
        try:
            # Parse the Gmail message
            gmail_message = GmailMessage.from_composio_payload(webhook_data)
            
            # Get the user's custom prompt or use default
            default_prompt = initial_prompt or "Default email processing prompt"
            user_prompt = get_user_prompt(gmail_message.user_id, default_prompt)
            
            # Add email processing to background tasks
            background_tasks.add_task(process_gmail_message, gmail_message, user_prompt)
            
            logger.info(f"Queued email {gmail_message.id} for processing")
            
        except ValidationError as e:
            logger.error(f"Validation error parsing Gmail webhook: {e}")
            # Still return success to avoid webhook retries
        except Exception as e:
            logger.error(f"Error parsing Gmail webhook: {e}")
            # Still return success to avoid webhook retries
    
    return {"status": "received", "webhook_id": webhook_id}
