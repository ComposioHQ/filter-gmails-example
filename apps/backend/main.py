from composio import Composio
from composio.types import auth_scheme
from composio_openai_agents import OpenAIAgentsProvider
import os
from dotenv import load_dotenv
from supabase import create_client, Client

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import hmac
import hashlib
import base64
import binascii
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
import logging
from agents import Agent, Runner
from enum import Enum

from prompts import REAPER_SYSTEM_PROMPT

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_KEY", "")
GMAIL_AUTH_CONFIG_ID: str = os.environ.get("GMAIL_AUTH_CONFIG_ID", "")
COMPOSIO_WEBHOOK_SECRET: str = os.environ.get("COMPOSIO_WEBHOOK_SECRET", "")

composio = Composio(provider=OpenAIAgentsProvider())
supabase: Client = create_client(url, key)


# Pydantic Models
class GmailMessage(BaseModel):
    """
    A comprehensive and clean model for Gmail message data from a Composio webhook,
    including both email content and essential event metadata.
    """

    # Event Metadata
    connection_id: str = Field(
        ..., description="The ID of the connection that triggered the event."
    )
    connection_nano_id: str = Field(..., description="The nano ID of the connection.")
    trigger_id: str = Field(..., description="The ID of the trigger.")
    trigger_nano_id: str = Field(..., description="The nano ID of the trigger.")
    user_id: str = Field(
        ..., description="The ID of the user associated with the event."
    )

    # Email Content
    id: str = Field(..., description="The unique ID of the message.")
    thread_id: str = Field(..., description="The ID of the email thread.")
    sender: str = Field(..., description="The sender's name and email address.")
    to: str = Field(..., description="The recipient's email address.")
    subject: str = Field(..., description="The subject of the email.")
    timestamp: datetime = Field(
        ..., alias="message_timestamp", description="When the message was received."
    )
    labels: List[str] = Field(
        ...,
        alias="label_ids",
        description="A list of labels on the message (e.g., 'INBOX').",
    )

    # Decoded Email Body
    text_body: Optional[str] = Field(
        None, description="The decoded plain text body of the email."
    )
    html_body: Optional[str] = Field(
        None, description="The decoded HTML body of the email."
    )

    class Config:
        # Allows creating the model using the alias names from the raw JSON
        allow_population_by_field_name = True

    @classmethod
    def from_composio_payload(cls, payload: Dict[str, Any]) -> "GmailMessage":
        """
        Parses a raw Composio webhook payload into a clean, validated GmailMessage object.
        This method handles data extraction, decoding, and cleaning.
        """
        message_data = payload.get("data")
        if not message_data:
            raise ValueError("Webhook payload must contain a 'data' key.")

        # --- Body Parsing Logic ---
        text_body = None
        html_body = None

        # The message content is in the 'parts' list of the payload
        parts = message_data.get("payload", {}).get("parts", [])
        if parts:
            for part in parts:
                mime_type = part.get("mimeType")
                body_data = part.get("body", {}).get("data")

                if body_data:
                    try:
                        # The body data is base64 encoded, so we must decode it
                        decoded = base64.urlsafe_b64decode(body_data).decode(
                            "utf-8", errors="replace"
                        )
                        if mime_type == "text/plain":
                            text_body = decoded
                        elif mime_type == "text/html":
                            html_body = decoded
                    except (binascii.Error, UnicodeDecodeError) as e:
                        logger.error(
                            f"Error decoding body for part {part.get('partId')}: {e}"
                        )
        else:
            # Check for single part messages (body might be at the top level)
            body_data = message_data.get("payload", {}).get("body", {}).get("data")
            if body_data:
                try:
                    decoded = base64.urlsafe_b64decode(body_data).decode(
                        "utf-8", errors="replace"
                    )
                    # Assume plain text if no parts
                    text_body = decoded
                except (binascii.Error, UnicodeDecodeError) as e:
                    logger.error(f"Error decoding single-part body: {e}")

        # Extract headers for sender, to, subject
        headers = message_data.get("payload", {}).get("headers", [])
        sender = ""
        to = ""
        subject = ""

        for header in headers:
            name = header.get("name", "").lower()
            value = header.get("value", "")
            if name == "from":
                sender = value
            elif name == "to":
                to = value
            elif name == "subject":
                subject = value

        # Extract timestamp properly
        internal_date = message_data.get("internalDate", 0)
        if internal_date:
            timestamp = datetime.fromtimestamp(int(internal_date) / 1000)
        else:
            timestamp = datetime.utcnow()

        # Pydantic will automatically handle mapping the keys from message_data
        # to the fields in our model, including the aliases.
        try:
            return cls(
                # Event metadata
                connection_id=message_data.get("connection_id", ""),
                connection_nano_id=message_data.get("connection_nano_id", ""),
                trigger_id=message_data.get("trigger_id", ""),
                trigger_nano_id=message_data.get("trigger_nano_id", ""),
                user_id=message_data.get("user_id", ""),
                # Email data
                id=message_data.get("id", ""),
                thread_id=message_data.get("threadId", ""),
                sender=sender,
                to=to,
                subject=subject,
                message_timestamp=timestamp,
                label_ids=message_data.get("labelIds", []),
                text_body=text_body,
                html_body=html_body,
            )
        except ValidationError as e:
            logger.error(f"Pydantic validation failed: {e}")
            # Re-raise to be handled by the calling function (e.g., in a FastAPI endpoint)
            raise e


class ComposioWebhook(BaseModel):
    """Model for Composio webhook payload"""

    type: str
    timestamp: str
    data: Dict[str, Any]


class ConnectionStatus(str, Enum):
    """Enum for connection status values"""

    ACTIVE = "active"
    INITIATED = "initiated"
    FAILED = "failed"
    EXPIRED = "expired"
    DELETED = "deleted"


class ConnectionRequest(BaseModel):
    """Request model for creating a new connection"""

    user_id: str = Field(..., description="The unique identifier for the user")
    redirect_url: Optional[str] = Field(
        None, description="Optional custom redirect URL after OAuth completion"
    )


class ConnectionResponse(BaseModel):
    """Response model for connection creation"""

    connection_id: str = Field(..., description="The ID of the initiated connection")
    redirect_url: str = Field(
        ..., description="The OAuth redirect URL for user authentication"
    )
    status: ConnectionStatus = Field(
        ..., description="The current status of the connection"
    )


class ConnectionStatusResponse(BaseModel):
    """Response model for connection status check"""

    user_id: str = Field(..., description="The user ID associated with the connection")
    status: ConnectionStatus = Field(
        ..., description="The current status of the connection"
    )
    connected: bool = Field(..., description="Whether the connection is active")
    connection_id: Optional[str] = Field(
        None, description="The connection ID if it exists"
    )
    account_id: Optional[str] = Field(
        None, description="The connected account ID if available"
    )
    app_name: Optional[str] = Field(None, description="The connected app name")
    created_at: Optional[datetime] = Field(
        None, description="When the connection was created"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if connection failed"
    )


# Load initial data
try:
    response = supabase.table("prompts").select("*").execute()
    if response.data:
        user_id = response.data[0]["user_id"]
        prompt = response.data[0]["prompt"]
    else:
        user_id = None
        prompt = None
        logger.warning("No prompts found in database")
except Exception as e:
    logger.error(f"Error loading prompts: {e}")
    user_id = None
    prompt = None


# Email processing function
async def process_gmail_message(message: GmailMessage, user_filter: str):
    """Process Gmail message with AI and apply labels"""
    try:
        logger.info(f"Processing email: {message.subject} from {message.sender}")
        logger.info(f"User: {message.user_id}, Connection: {message.connection_id}")

        logger.info(f"Email body preview: {(message.text_body or '')[:200]}...")
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

        reaper = Agent(
            name="Gmail Reaper", instructions=REAPER_SYSTEM_PROMPT, tools=tools
        )
        prompt_details = f"{user_filter}\n\n## Email\n{message.text_body or message.html_body}\n## Message ID\n{message.id}"
        await Runner.run(reaper, prompt_details)
        logger.info(f"Successfully processed email {message.id}")

        # Store processing result in Supabase

    except Exception as e:
        logger.error(f"Error processing email {message.id}: {e}")
        # Could implement retry logic or dead letter queue here


@app.get("/")
async def root():
    return {"message": prompt if prompt else "Gmail Labeller API"}


@app.post("/api/connection", response_model=ConnectionResponse)
async def create_connection(request: ConnectionRequest):
    """
    Create a new Gmail connection for a user using Composio OAuth flow.

    This endpoint initiates the OAuth connection process and returns a redirect URL
    that the user should be directed to for authentication.
    """
    try:
        logger.info(f"Initiating Gmail connection for user: {request.user_id}")

        # Initiate connection with Composio
        connection_request = composio.connected_accounts.initiate(
            user_id=request.user_id,
            auth_config_id=GMAIL_AUTH_CONFIG_ID,
            config=auth_scheme.oauth2(options={}),
        )

        # Map the connection status
        status_map = {
            "initiated": ConnectionStatus.INITIATED,
            "active": ConnectionStatus.ACTIVE,
            "failed": ConnectionStatus.FAILED,
            "expired": ConnectionStatus.EXPIRED,
            "deleted": ConnectionStatus.DELETED,
        }

        connection_status = status_map.get(
            getattr(connection_request, "status", "initiated").lower(),
            ConnectionStatus.INITIATED,
        )

        return ConnectionResponse(
            connection_id=str(connection_request.id),
            redirect_url=str(connection_request.redirect_url),
            status=connection_status,
        )

    except Exception as e:
        logger.error(f"Error creating connection for user {request.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create connection: {str(e)}"
        )


@app.get("/api/connection/", response_model=ConnectionStatusResponse)
async def get_connection(nano_id: str):
    """
    Check the connection status for a specific user.

    This endpoint returns the current status of a user's Gmail connection,
    including whether it's active, expired, or needs to be re-established.
    """
    try:
        logger.info(f"Checking connection status for connection ID: {nano_id}")

        # Get connected accounts for the user
        connected_account = composio.connected_accounts.get(nano_id)

        # Map the connection status from Composio to our enum
        status_map = {
            "active": ConnectionStatus.ACTIVE,
            "initiated": ConnectionStatus.INITIATED,
            "failed": ConnectionStatus.FAILED,
            "expired": ConnectionStatus.EXPIRED,
            "deleted": ConnectionStatus.DELETED,
        }

        # Extract status from the connected account object
        composio_status = getattr(connected_account, "status", "unknown").lower()
        mapped_status = status_map.get(composio_status, ConnectionStatus.FAILED)

        # Build the response
        return ConnectionStatusResponse(
            user_id=getattr(connected_account, "user_id", ""),
            status=mapped_status,
            connected=mapped_status == ConnectionStatus.ACTIVE,
            connection_id=getattr(connected_account, "id", None),
            account_id=getattr(connected_account, "account_id", None),
            app_name=getattr(connected_account, "app_name", None),
            created_at=getattr(connected_account, "created_at", None),
            error_message=getattr(connected_account, "error_message", None)
            if mapped_status == ConnectionStatus.FAILED
            else None,
        )

    except Exception as e:
        logger.error(f"Error retrieving connection status for {nano_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve connection status: {str(e)}"
        )


@app.post("/composio/webhook")
async def listen_webhooks(request: Request, background_tasks: BackgroundTasks):
    # Get the raw body for signature verification
    body = await request.body()

    # Get the signature and timestamp from headers
    signature_header = request.headers.get("webhook-signature", "")
    timestamp = request.headers.get("webhook-timestamp", "")
    webhook_id = request.headers.get("webhook-id", "")

    # Verify webhook authenticity
    if COMPOSIO_WEBHOOK_SECRET and signature_header:
        # Extract the signature (format: "v1,signature")
        if "," in signature_header:
            version, signature = signature_header.split(",", 1)
        else:
            raise HTTPException(status_code=401, detail="Invalid signature format")

        # Create the signed content (webhook_id.timestamp.body)
        signed_content = f"{webhook_id}.{timestamp}.{body.decode('utf-8')}"

        # Generate expected signature
        expected_signature = hmac.new(
            COMPOSIO_WEBHOOK_SECRET.encode(), signed_content.encode(), hashlib.sha256
        ).digest()

        # Encode to base64
        expected_signature_b64 = base64.b64encode(expected_signature).decode()

        # Compare signatures
        if not hmac.compare_digest(signature, expected_signature_b64):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

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
            # Get the latest prompt for this user
            user_prompt = prompt or "Default email processing prompt"  # Default prompt
            if gmail_message.user_id:
                try:
                    prompt_response = (
                        supabase.table("prompts")
                        .select("*")
                        .eq("user_id", gmail_message.user_id)
                        .execute()
                    )
                    if prompt_response.data:
                        user_prompt = prompt_response.data[0]["prompt"]
                        logger.info(
                            f"Using custom prompt for user {gmail_message.user_id}"
                        )
                except Exception as e:
                    logger.error(f"Error fetching user prompt: {e}")

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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "gmail-labeller",
        "supabase_connected": bool(supabase),
        "composio_connected": bool(composio),
    }
