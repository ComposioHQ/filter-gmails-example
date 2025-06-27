"""Pydantic models for the Gmail Labeller application."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
import base64
import binascii
import logging

logger = logging.getLogger(__name__)


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
    status: str = Field(
        ..., description="The current status of the connection (INITIATED, ACTIVE, FAILED, EXPIRED, REVOKED)"
    )


class ConnectionStatusResponse(BaseModel):
    """Response model for connection status check"""

    user_id: str = Field(..., description="The user ID associated with the connection")
    status: str = Field(
        ..., description="The current status of the connection (INITIATED, ACTIVE, FAILED, EXPIRED, REVOKED)"
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