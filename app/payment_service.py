"""
Paynow payment integration for Zimbabwe
Handles payment processing for admin fees via EcoCash, InnBucks, and OneMoney
"""
import logging
import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from app.config import settings
from app.models import PaymentMethod, PaymentStatus
from app.database import get_database

logger = logging.getLogger(__name__)


class PaynowPaymentService:
    """Service for processing payments via Paynow Zimbabwe API"""
    
    def __init__(self):
        self.integration_id = settings.PAYNOW_INTEGRATION_ID
        self.integration_key = settings.PAYNOW_INTEGRATION_KEY
        self.result_url = settings.PAYNOW_RESULT_URL
        self.base_url = "https://www.paynow.co.zw/transaction"
        self.initiate_url = f"{self.base_url}/initiate"
        self.poll_url = f"{self.base_url}/poll"
        
        # Payment amount configuration
        self.admin_fee = settings.ADMIN_FEE_AMOUNT
        self.currency = settings.ADMIN_FEE_CURRENCY
    
    async def initiate_payment(
        self,
        phone_number: str,
        payment_method: PaymentMethod,
        application_id: str,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate payment transaction via Paynow
        
        Args:
            phone_number: Customer phone number
            payment_method: Payment method (ecocash, innbucks, onemoney)
            application_id: Application ID for reference
            reference: Optional custom reference
            
        Returns:
            Dictionary with payment initiation result
        """
        try:
            # Generate reference if not provided
            if not reference:
                reference = f"APP-{application_id[:8]}"
            
            # Prepare payment details
            payment_details = {
                "id": self.integration_id,
                "key": self.integration_key,
                "amount": self.admin_fee,
                "currency": self.currency,
                "reference": reference,
                "resulturl": self.result_url,
                "returnurl": f"{self.result_url}/return/{application_id}",
                "authemail": "payments@conveyancingbot.co.zw",  # Generic auth email
                "status": "Message"
            }
            
            # Add phone number based on payment method
            if payment_method == PaymentMethod.ECOCASH:
                payment_details["phone"] = phone_number
                payment_details["method"] = "ecocash"
            elif payment_method == PaymentMethod.INNBUCKS:
                payment_details["phone"] = phone_number
                payment_details["method"] = "innbucks"
            elif payment_method == PaymentMethod.ONEMONEY:
                payment_details["phone"] = phone_number
                payment_details["method"] = "onemoney"
            
            # Send payment initiation request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.initiate_url,
                    data=payment_details,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                result = response.json()
            
            # Process response
            if result.get("status") == "Ok":
                poll_url = result.get("pollurl")
                logger.info(f"Payment initiated successfully. Poll URL: {poll_url}")
                
                # Update application with payment info
                await self._update_application_payment(
                    application_id,
                    poll_url,
                    payment_method,
                    PaymentStatus.PROCESSING
                )
                
                return {
                    "success": True,
                    "poll_url": poll_url,
                    "reference": reference,
                    "amount": self.admin_fee,
                    "currency": self.currency,
                    "message": "Payment initiated. Please complete payment on your phone."
                }
            else:
                error_message = result.get("error", "Unknown error")
                logger.error(f"Payment initiation failed: {error_message}")
                return {
                    "success": False,
                    "error": error_message,
                    "message": "Failed to initiate payment. Please try again."
                }
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during payment initiation: {e}")
            return {
                "success": False,
                "error": "Payment service unavailable",
                "message": "Unable to connect to payment service. Please try again later."
            }
        except Exception as e:
            logger.error(f"Error during payment initiation: {e}")
            return {
                "success": False,
                "error": "Payment processing failed",
                "message": "An error occurred while processing payment."
            }
    
    async def poll_payment_status(self, poll_url: str) -> Dict[str, Any]:
        """
        Poll payment status from Paynow
        
        Args:
            poll_url: URL to poll for payment status
            
        Returns:
            Dictionary with payment status information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(poll_url)
                response.raise_for_status()
                result = response.json()
            
            # Parse Paynow status
            paynow_status = result.get("status", "").lower()
            
            # Map Paynow status to our PaymentStatus
            status_mapping = {
                "paid": PaymentStatus.COMPLETED,
                "awaiting delivery": PaymentStatus.PROCESSING,
                "delivered": PaymentStatus.COMPLETED,
                "cancelled": PaymentStatus.FAILED,
                "disputed": PaymentStatus.FAILED,
                "failed": PaymentStatus.FAILED
            }
            
            payment_status = status_mapping.get(paynow_status, PaymentStatus.PENDING)
            
            return {
                "success": True,
                "status": payment_status,
                "paynow_status": paynow_status,
                "amount": result.get("amount"),
                "reference": result.get("reference")
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during payment poll: {e}")
            return {
                "success": False,
                "error": "Unable to check payment status"
            }
        except Exception as e:
            logger.error(f"Error during payment poll: {e}")
            return {
                "success": False,
                "error": "Payment status check failed"
            }
    
    async def monitor_payment(
        self,
        application_id: str,
        poll_url: str,
        max_attempts: int = 20,
        interval_seconds: int = 15
    ) -> Dict[str, Any]:
        """
        Monitor payment status with background polling
        
        Args:
            application_id: Application ID
            poll_url: URL to poll for payment status
            max_attempts: Maximum number of polling attempts
            interval_seconds: Interval between polls
            
        Returns:
            Dictionary with final payment status
        """
        logger.info(f"Starting payment monitoring for application {application_id}")
        
        for attempt in range(max_attempts):
            try:
                # Poll payment status
                status_result = await self.poll_payment_status(poll_url)
                
                if not status_result["success"]:
                    logger.warning(f"Payment poll attempt {attempt + 1} failed")
                    await asyncio.sleep(interval_seconds)
                    continue
                
                payment_status = status_result["status"]
                logger.info(f"Payment status: {payment_status} (attempt {attempt + 1})")
                
                # Update application with current status
                await self._update_application_payment_status(
                    application_id, payment_status
                )
                
                # Check if payment is complete
                if payment_status == PaymentStatus.COMPLETED:
                    logger.info(f"Payment completed for application {application_id}")
                    await self._finalize_payment(application_id)
                    return {
                        "success": True,
                        "status": PaymentStatus.COMPLETED,
                        "message": "Payment successful"
                    }
                
                # Check if payment failed
                elif payment_status == PaymentStatus.FAILED:
                    logger.error(f"Payment failed for application {application_id}")
                    return {
                        "success": False,
                        "status": PaymentStatus.FAILED,
                        "message": "Payment failed or was cancelled"
                    }
                
                # Continue polling if still processing
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error during payment monitoring: {e}")
                await asyncio.sleep(interval_seconds)
        
        # Max attempts reached
        logger.warning(f"Payment monitoring timed out for application {application_id}")
        return {
            "success": False,
            "status": PaymentStatus.PROCESSING,
            "message": "Payment verification timed out. Please check manually."
        }
    
    async def _update_application_payment(
        self,
        application_id: str,
        poll_url: str,
        payment_method: PaymentMethod,
        status: PaymentStatus
    ):
        """Update application with payment initiation details"""
        database = get_database()
        
        await database.applications.update_one(
            {"_id": application_id},
            {
                "$set": {
                    "payment.poll_url": poll_url,
                    "payment.method": payment_method,
                    "payment.status": status,
                    "payment.amount": self.admin_fee,
                    "payment.currency": self.currency,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def _update_application_payment_status(
        self,
        application_id: str,
        status: PaymentStatus
    ):
        """Update application payment status"""
        database = get_database()
        
        update_data = {
            "payment.status": status,
            "updated_at": datetime.utcnow()
        }
        
        if status == PaymentStatus.COMPLETED:
            update_data["payment.completed_at"] = datetime.utcnow()
        
        await database.applications.update_one(
            {"_id": application_id},
            {"$set": update_data}
        )
    
    async def _finalize_payment(self, application_id: str):
        """Finalize successful payment"""
        database = get_database()
        
        await database.applications.update_one(
            {"_id": application_id},
            {
                "$set": {
                    "payment.status": PaymentStatus.COMPLETED,
                    "payment.completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    def format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for Paynow
        Ensures Zimbabwe format (263XXXXXXXXX)
        """
        # Remove any non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Remove leading + if present
        if clean_number.startswith('263'):
            return clean_number
        
        # If starts with 0, replace with 263
        if clean_number.startswith('0'):
            return '263' + clean_number[1:]
        
        # If already in correct format
        if len(clean_number) == 12 and clean_number.startswith('263'):
            return clean_number
        
        # Default: assume Zimbabwe number and add prefix
        return '263' + clean_number[-9:] if len(clean_number) >= 9 else clean_number


# Global payment service instance
payment_service = PaynowPaymentService()


async def initiate_application_payment(
    phone_number: str,
    payment_method: PaymentMethod,
    application_id: str
) -> Dict[str, Any]:
    """
    Convenience function to initiate payment for an application
    """
    # Format phone number
    formatted_phone = payment_service.format_phone_number(phone_number)
    
    # Initiate payment
    result = await payment_service.initiate_payment(
        formatted_phone,
        payment_method,
        application_id
    )
    
    # If successful, start background monitoring
    if result["success"]:
        asyncio.create_task(
            payment_service.monitor_payment(
                application_id,
                result["poll_url"]
            )
        )
    
    return result


async def get_payment_status(application_id: str) -> Dict[str, Any]:
    """
    Get current payment status for an application
    """
    database = get_database()
    application = await database.applications.find_one({"_id": application_id})
    
    if not application:
        return {"error": "Application not found"}
    
    payment_info = application.get("payment", {})
    
    return {
        "status": payment_info.get("status"),
        "amount": payment_info.get("amount"),
        "currency": payment_info.get("currency"),
        "method": payment_info.get("method"),
        "completed_at": payment_info.get("completed_at")
    }