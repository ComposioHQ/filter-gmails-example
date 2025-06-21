"""API routes for Gmail Labeller application."""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from composio.types import auth_scheme
from config import composio, supabase, GMAIL_AUTH_CONFIG_ID, initial_prompt
from models import (
    ConnectionRequest,
    ConnectionResponse,
    ConnectionStatus,
    ConnectionStatusResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint that returns the initial prompt if available."""
    return {"message": initial_prompt if initial_prompt else "Gmail Labeller API"}


@router.post("/api/connection", response_model=ConnectionResponse)
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


@router.get("/api/connection/", response_model=ConnectionStatusResponse)
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


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "gmail-labeller",
        "supabase_connected": bool(supabase),
        "composio_connected": bool(composio),
    }