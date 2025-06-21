"""Webhook verification logic for Composio webhooks."""

import hmac
import hashlib
import base64
from fastapi import HTTPException, Request
from config import COMPOSIO_WEBHOOK_SECRET


async def verify_webhook_signature(request: Request) -> tuple[bytes, str]:
    """
    Verify the authenticity of a Composio webhook request.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        tuple: (body bytes, webhook_id)
        
    Raises:
        HTTPException: If signature verification fails
    """
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
            COMPOSIO_WEBHOOK_SECRET.encode(), 
            signed_content.encode(), 
            hashlib.sha256
        ).digest()
        
        # Encode to base64
        expected_signature_b64 = base64.b64encode(expected_signature).decode()
        
        # Compare signatures
        if not hmac.compare_digest(signature, expected_signature_b64):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    return body, webhook_id