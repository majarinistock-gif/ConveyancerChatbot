"""
WhatsApp webhook handlers for Meta Cloud API
Handles incoming messages and verification requests
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import Response
from typing import Dict, Any
import logging
from app.config import settings
from app.state_machine import process_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def webhook_verify(request: Request):
    """
    Meta webhook verification endpoint
    Called by Meta when setting up the webhook
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return Response(content=challenge, status_code=200)
        else:
            logger.warning(f"Webhook verification failed. Token mismatch: {token}")
            raise HTTPException(status_code=403, detail="Verification failed")
    
    raise HTTPException(status_code=400, detail="Invalid request")


@router.post("/")
async def webhook_receive(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint for receiving WhatsApp messages
    Processes incoming messages in the background
    """
    try:
        # Parse incoming webhook data
        data = await request.json()
        logger.info(f"Received webhook: {data}")
        
        # Extract message data
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        messages = change.get("value", {}).get("messages", [])
                        for message in messages:
                            # Process message in background
                            background_tasks.add_task(
                                process_message,
                                message,
                                change.get("value", {})
                            )
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def webhook_health():
    """
    Health check endpoint for webhook
    """
    return {
        "status": "healthy",
        "service": "whatsapp-webhook",
        "environment": settings.ENVIRONMENT
    }


def extract_message_data(message: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant data from WhatsApp message
    """
    phone_number = message.get("from")
    message_id = message.get("id")
    message_type = message.get("type")
    
    # Extract timestamp
    timestamp = message.get("timestamp")
    
    # Extract message content based on type
    content = {}
    if message_type == "text":
        content["text"] = message.get("text", {}).get("body")
    elif message_type == "image":
        content["image"] = message.get("image", {})
    elif message_type == "document":
        content["document"] = message.get("document", {})
    elif message_type == "audio":
        content["audio"] = message.get("audio", {})
    elif message_type == "video":
        content["video"] = message.get("video", {})
    
    # Extract metadata
    display_phone_number = metadata.get("metadata", {}).get("display_phone_number")
    phone_number_id = metadata.get("metadata", {}).get("phone_number_id")
    
    return {
        "phone_number": phone_number,
        "message_id": message_id,
        "message_type": message_type,
        "timestamp": timestamp,
        "content": content,
        "display_phone_number": display_phone_number,
        "phone_number_id": phone_number_id
    }