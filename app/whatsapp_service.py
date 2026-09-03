"""
WhatsApp API helpers for Meta Cloud API
Handles sending messages to WhatsApp users
"""
import logging
import httpx
from typing import Dict, Any, Optional, List
from app.config import settings
from app.token_manager import get_valid_token

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp messages via Meta Cloud API"""
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.phone_number_id = settings.META_PHONE_NUMBER_ID
    
    async def send_text_message(
        self,
        phone_number: str,
        message: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """
        Send text message to WhatsApp user
        
        Args:
            phone_number: Recipient phone number
            message: Message content
            preview_url: Whether to generate link previews
            
        Returns:
            Dictionary with API response
        """
        try:
            # Get valid access token
            token = await get_valid_token()
            
            # Prepare message payload
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {
                    "body": message,
                    "preview_url": preview_url
                }
            }
            
            # Send message
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            logger.info(f"Text message sent to {phone_number}: {result.get('messages', [{}])[0].get('id')}")
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending WhatsApp message: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send template message to WhatsApp user
        
        Args:
            phone_number: Recipient phone number
            template_name: Name of the template
            language_code: Language code for the template
            components: Template components for dynamic content
            
        Returns:
            Dictionary with API response
        """
        try:
            # Get valid access token
            token = await get_valid_token()
            
            # Prepare template payload
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code}
                }
            }
            
            # Add components if provided
            if components:
                payload["template"]["components"] = components
            
            # Send message
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            logger.info(f"Template message sent to {phone_number}: {template_name}")
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending template message: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error sending template message: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_list_message(
        self,
        phone_number: str,
        header_text: str,
        body_text: str,
        footer_text: Optional[str],
        button_text: str,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send list message (interactive message with menu options)
        
        Args:
            phone_number: Recipient phone number
            header_text: Header text for the list
            body_text: Body text for the list
            footer_text: Optional footer text
            button_text: Button text
            sections: List of sections with rows/options
            
        Returns:
            Dictionary with API response
        """
        try:
            # Get valid access token
            token = await get_valid_token()
            
            # Prepare list message payload
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "header": {"type": "text", "text": header_text},
                    "body": {"text": body_text},
                    "action": {
                        "button": button_text,
                        "sections": sections
                    }
                }
            }
            
            # Add footer if provided
            if footer_text:
                payload["interactive"]["footer"] = {"text": footer_text}
            
            # Send message
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            logger.info(f"List message sent to {phone_number}")
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending list message: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error sending list message: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_button_message(
        self,
        phone_number: str,
        header_text: Optional[str],
        body_text: str,
        footer_text: Optional[str],
        buttons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send button message (interactive message with buttons)
        
        Args:
            phone_number: Recipient phone number
            header_text: Optional header text
            body_text: Body text
            footer_text: Optional footer text
            buttons: List of buttons (max 3)
            
        Returns:
            Dictionary with API response
        """
        try:
            # Get valid access token
            token = await get_valid_token()
            
            # Prepare button message payload
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body_text},
                    "action": {"buttons": buttons}
                }
            }
            
            # Add header if provided
            if header_text:
                payload["interactive"]["header"] = {"type": "text", "text": header_text}
            
            # Add footer if provided
            if footer_text:
                payload["interactive"]["footer"] = {"text": footer_text}
            
            # Send message
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            logger.info(f"Button message sent to {phone_number}")
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending button message: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error sending button message: {e}")
            return {"success": False, "error": str(e)}
    
    async def download_media(self, media_id: str) -> bytes:
        """
        Download media file from WhatsApp CDN
        
        Args:
            media_id: Media ID from WhatsApp message
            
        Returns:
            Media content as bytes
        """
        try:
            # Get valid access token
            token = await get_valid_token()
            
            # Get media URL
            url = f"{self.base_url}/{media_id}"
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                media_data = response.json()
            
            media_url = media_data.get("url")
            
            # Download media content
            async with httpx.AsyncClient() as client:
                response = await client.get(media_url, headers=headers)
                response.raise_for_status()
                content = response.read()
            
            logger.info(f"Media downloaded: {media_id}")
            return content
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading media: {e}")
            raise
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            raise
    
    def format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for WhatsApp API
        Ensures international format without + or spaces
        """
        # Remove any non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Remove leading + if present
        if clean_number.startswith(''):
            clean_number = clean_number[1:]
        
        return clean_number


# Global WhatsApp service instance
whatsapp_service = WhatsAppService()


async def send_message(phone_number: str, message: str) -> Dict[str, Any]:
    """
    Convenience function to send text message
    """
    # Format phone number
    formatted_phone = whatsapp_service.format_phone_number(phone_number)
    
    # Send message
    return await whatsapp_service.send_text_message(formatted_phone, message)


async def send_interactive_list(
    phone_number: str,
    header: str,
    body: str,
    button: str,
    options: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Convenience function to send interactive list message
    """
    # Format phone number
    formatted_phone = whatsapp_service.format_phone_number(phone_number)
    
    # Create sections from options
    sections = [{
        "title": "Options",
        "rows": [
            {
                "id": option.get("id", str(i)),
                "title": option.get("title", ""),
                "description": option.get("description", "")
            }
            for i, option in enumerate(options)
        ]
    }]
    
    # Send list message
    return await whatsapp_service.send_list_message(
        formatted_phone, header, body, None, button, sections
    )


async def send_interactive_buttons(
    phone_number: str,
    body: str,
    buttons: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Convenience function to send interactive button message
    """
    # Format phone number
    formatted_phone = whatsapp_service.format_phone_number(phone_number)
    
    # Format buttons for API
    formatted_buttons = [
        {
            "type": "reply",
            "reply": {
                "id": button.get("id", str(i)),
                "title": button.get("title", "")
            }
        }
        for i, button in enumerate(buttons[:3])  # Max 3 buttons
    ]
    
    # Send button message
    return await whatsapp_service.send_button_message(
        formatted_phone, None, body, None, formatted_buttons
    )