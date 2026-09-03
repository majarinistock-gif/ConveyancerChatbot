"""
Payment callback handler for Paynow
Handles payment status callbacks from Paynow
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging
from app.database import get_database
from app.models import PaymentStatus
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/callback")
async def payment_callback(request: Request):
    """
    Handle payment status callback from Paynow
    """
    try:
        # Parse callback data
        callback_data = await request.json()
        logger.info(f"Payment callback received: {callback_data}")
        
        # Extract payment reference and status
        reference = callback_data.get("reference")
        status = callback_data.get("status")
        
        if not reference or not status:
            logger.warning("Invalid callback data: missing reference or status")
            raise HTTPException(status_code=400, detail="Invalid callback data")
        
        # Parse reference to get application ID (format: APP-XXXXXXXX)
        if reference.startswith("APP-"):
            application_id = reference[4:]  # Remove "APP-" prefix
        else:
            application_id = reference
        
        # Map Paynow status to our PaymentStatus
        status_mapping = {
            "paid": PaymentStatus.COMPLETED,
            "awaiting delivery": PaymentStatus.PROCESSING,
            "delivered": PaymentStatus.COMPLETED,
            "cancelled": PaymentStatus.FAILED,
            "disputed": PaymentStatus.FAILED,
            "failed": PaymentStatus.FAILED
        }
        
        payment_status = status_mapping.get(status.lower(), PaymentStatus.PENDING)
        
        # Update application payment status
        database = get_database()
        
        update_data = {
            "payment.status": payment_status,
            "updated_at": datetime.utcnow()
        }
        
        if payment_status == PaymentStatus.COMPLETED:
            update_data["payment.completed_at"] = datetime.utcnow()
        
        result = await database.applications.update_one(
            {"_id": application_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Payment status updated for application {application_id}: {payment_status}")
            
            # Send notification to user about payment status
            # This would be implemented with WhatsApp service
            # await send_payment_status_notification(application_id, payment_status)
            
            return {"status": "success", "message": "Payment status updated"}
        else:
            logger.warning(f"Application {application_id} not found for payment callback")
            return {"status": "error", "message": "Application not found"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing payment callback: {e}")
        raise HTTPException(status_code=500, detail="Failed to process payment callback")


@router.get("/return/{application_id}")
async def payment_return(application_id: str):
    """
    Handle return from Paynow payment page
    This is the URL the user is redirected to after payment
    """
    try:
        database = get_database()
        
        application = await database.applications.find_one({"_id": application_id})
        
        if not application:
            return {"error": "Application not found"}
        
        payment_status = application.get("payment", {}).get("status")
        
        return {
            "application_id": application_id,
            "payment_status": payment_status,
            "message": _get_return_message(payment_status)
        }
        
    except Exception as e:
        logger.error(f"Error handling payment return: {e}")
        return {"error": "Failed to process return"}


def _get_return_message(payment_status: str) -> str:
        """Get user-friendly message based on payment status"""
        messages = {
            PaymentStatus.COMPLETED: "Payment successful! Your application is being processed.",
            PaymentStatus.PROCESSING: "Payment is being processed. Please wait for confirmation.",
            PaymentStatus.FAILED: "Payment failed. Please try again or contact support.",
            PaymentStatus.PENDING: "Payment is pending. Please complete the payment process."
        }
        
        return messages.get(payment_status, "Payment status unknown.")