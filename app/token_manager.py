"""
Meta token management for WhatsApp Cloud API
Handles token refresh and rotation for sandbox and production modes
"""
import logging
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class MetaTokenManager:
    """Manages Meta access tokens for WhatsApp Cloud API"""
    
    def __init__(self):
        self.current_token = settings.META_ACCESS_TOKEN
        self.token_expiry = None
        self.last_refresh = None
        self.environment = settings.ENVIRONMENT
        
        # Set token expiry for sandbox (24 hours from now)
        if self.environment == "sandbox":
            self.token_expiry = datetime.utcnow() + timedelta(hours=24)
            logger.info("Sandbox mode: Token will expire in 24 hours")
        else:
            # Production tokens are longer-lived but should be rotated
            self.token_expiry = datetime.utcnow() + timedelta(days=90)
            logger.info("Production mode: Token rotation every 90 days")
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid"""
        if not self.current_token:
            return False
        
        if self.token_expiry and datetime.utcnow() >= self.token_expiry:
            logger.warning("Token has expired")
            return False
        
        return True
    
    def is_token_near_expiry(self, hours_threshold: int = 6) -> bool:
        """Check if token is near expiry"""
        if not self.token_expiry:
            return False
        
        time_until_expiry = self.token_expiry - datetime.utcnow()
        return time_until_expiry <= timedelta(hours=hours_threshold)
    
    async def test_token(self) -> bool:
        """
        Test if current token is valid by making a test API call
        """
        try:
            async with httpx.AsyncClient() as client:
                # Test token with a simple WhatsApp API call
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{settings.META_PHONE_NUMBER_ID}",
                    headers={"Authorization": f"Bearer {self.current_token}"}
                )
                
                if response.status_code == 200:
                    logger.info("Token test successful")
                    return True
                elif response.status_code in [401, 403]:
                    logger.error(f"Token test failed: {response.status_code} - Token may be expired")
                    return False
                else:
                    logger.warning(f"Token test returned status {response.status_code}")
                    return response.status_code == 200
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token test: {e}")
            return False
        except Exception as e:
            logger.error(f"Error testing token: {e}")
            return False
    
    async def refresh_token(self) -> Dict[str, Any]:
        """
        Refresh access token
        For sandbox: Manual refresh required
        For production: Automated token rotation
        """
        if self.environment == "sandbox":
            return await self._manual_token_refresh()
        else:
            return await self._automated_token_rotation()
    
    async def _manual_token_refresh(self) -> Dict[str, Any]:
        """
        Manual token refresh for sandbox mode
        Requires user to update META_ACCESS_TOKEN in environment
        """
        logger.warning("Sandbox mode: Manual token refresh required")
        
        return {
            "success": False,
            "error": "Manual token refresh required for sandbox mode",
            "message": "Please update META_ACCESS_TOKEN in your environment variables",
            "instructions": "1. Go to Meta Developer Dashboard\n2. Get new temporary access token\n3. Update .env file with new token\n4. Restart the application"
        }
    
    async def _automated_token_rotation(self) -> Dict[str, Any]:
        """
        Automated token rotation for production mode
        This would use Meta's System User token rotation API
        """
        logger.info("Production mode: Attempting automated token rotation")
        
        try:
            # In production, this would call Meta's token rotation endpoint
            # For now, this is a placeholder implementation
            
            # Example implementation (requires proper Meta Business setup):
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "https://graph.facebook.com/v18.0/oauth/access_token",
            #         params={
            #             "grant_type": "fb_exchange_token",
            #             "client_id": settings.META_BUSINESS_ID,
            #             "client_secret": settings.META_APP_SECRET,
            #             "fb_exchange_token": self.current_token
            #         }
            #     )
            #     
            #     if response.status_code == 200:
            #         token_data = response.json()
            #         self.current_token = token_data["access_token"]
            #         self.token_expiry = datetime.utcnow() + timedelta(days=90)
            #         self.last_refresh = datetime.utcnow()
            #         return {"success": True, "new_token": self.current_token}
            
            logger.warning("Automated token rotation not fully implemented")
            return {
                "success": False,
                "error": "Automated token rotation requires full Meta Business setup",
                "message": "Please implement Meta System User token rotation"
            }
            
        except Exception as e:
            logger.error(f"Error during automated token rotation: {e}")
            return {
                "success": False,
                "error": f"Token rotation failed: {str(e)}"
            }
    
    def get_token(self) -> str:
        """Get current access token"""
        if not self.is_token_valid():
            logger.error("Attempting to use invalid token")
            raise RuntimeError("Token is expired or invalid")
        
        return self.current_token
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get information about current token"""
        return {
            "environment": self.environment,
            "is_valid": self.is_token_valid(),
            "is_near_expiry": self.is_token_near_expiry(),
            "expiry_date": self.token_expiry.isoformat() if self.token_expiry else None,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "hours_until_expiry": (
                (self.token_expiry - datetime.utcnow()).total_seconds() / 3600
                if self.token_expiry else None
            )
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on token
        """
        token_info = self.get_token_info()
        is_valid = await self.test_token()
        
        return {
            "token_status": "valid" if is_valid else "invalid",
            "token_info": token_info,
            "recommendation": self._get_health_recommendation()
        }
    
    def _get_health_recommendation(self) -> str:
        """Get recommendation based on token health"""
        if not self.is_token_valid():
            return "Token is expired. Please refresh immediately."
        elif self.is_token_near_expiry(hours_threshold=6):
            return "Token is near expiry. Please refresh soon."
        elif self.environment == "sandbox":
            return "Sandbox token expires in 24 hours. Plan for manual refresh."
        else:
            return "Token is healthy. No action required."


class TokenRefreshAlert:
    """Handles token expiry alerts and notifications"""
    
    @staticmethod
    async def send_expiry_alert(recipient_phone: str, hours_remaining: int):
        """
        Send alert about token expiry
        This would integrate with WhatsApp service to send notification
        """
        logger.warning(f"Token expiry alert: {hours_remaining} hours remaining")
        
        # Placeholder: Send WhatsApp message to admin
        # from app.whatsapp_service import send_message
        # await send_message(
        #     recipient_phone,
        #     f"⚠️ Token Expiry Alert: WhatsApp API token will expire in {hours_remaining} hours. Please refresh."
        # )
    
    @staticmethod
    async def send_expiry_notification(recipient_phone: str):
        """
        Send notification that token has expired
        """
        logger.error("Token has expired")
        
        # Placeholder: Send WhatsApp message to admin
        # from app.whatsapp_service import send_message
        # await send_message(
        #     recipient_phone,
        #     "🚨 Token Expired: WhatsApp API token has expired. Please refresh immediately."
        # )


# Global token manager instance
token_manager = MetaTokenManager()


async def get_valid_token() -> str:
    """
    Convenience function to get a valid token
    Raises exception if token is invalid
    """
    if not token_manager.is_token_valid():
        logger.error("Token is invalid, attempting refresh")
        refresh_result = await token_manager.refresh_token()
        if not refresh_result["success"]:
            raise RuntimeError(f"Token refresh failed: {refresh_result['error']}")
    
    return token_manager.get_token()


async def check_token_health() -> Dict[str, Any]:
    """
    Convenience function to check token health
    """
    return await token_manager.health_check()