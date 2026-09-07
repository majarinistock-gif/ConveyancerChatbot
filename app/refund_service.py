"""
Paynow Reversal and Refund Service
Handles automated refunds when practitioner defaults (72-hour timeout)
"""
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.config import settings
from app.models import PaymentStatus, CaseStatus
from app.database import get_database
from app.ledger_service import reverse_payment_on_default
from app.sla_timer_service import sla_timer_service

logger = logging.getLogger(__name__)


class PaynowRefundService:
    """Service for processing Paynow reversals and refunds"""
    
    def __init__(self):
        self.integration_id = settings.PAYNOW_INTEGRATION_ID
        self.integration_key = settings.PAYNOW_INTEGRATION_KEY
        self.base_url = "https://www.paynow.co.zw/transaction"
        self.refund_url = f"{self.base_url}/refund"
        self.admin_fee = settings.ADMIN_FEE_AMOUNT
    
    async def initiate_refund(
        self,
        paynow_transaction_ref: str,
        amount: float,
        reason: str = "Practitioner default - 72-hour SLA exceeded"
    ) -> Dict[str, Any]:
        """
        Initiate refund through Paynow API
        
        Args:
            paynow_transaction_ref: Original Paynow transaction reference
            amount: Amount to refund (should be full $5.00)
            reason: Reason for refund
            
        Returns:
            Dictionary with refund result
        """
        try:
            # Prepare refund request
            refund_data = {
                "id": self.integration_id,
                "key": self.integration_key,
                "reference": paynow_transaction_ref,
                "amount": amount,
                "reason": reason
            }
            
            # Send refund request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.refund_url,
                    data=refund_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                result = response.json()
            
            # Process response
            if result.get("status") == "Ok":
                logger.info(f"Refund initiated successfully for transaction {paynow_transaction_ref}")
                return {
                    "success": True,
                    "refund_reference": result.get("reference"),
                    "amount": amount,
                    "message": "Refund initiated successfully"
                }
            else:
                error_message = result.get("error", "Unknown error")
                logger.error(f"Refund initiation failed: {error_message}")
                return {
                    "success": False,
                    "error": error_message,
                    "message": "Failed to initiate refund"
                }
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during refund initiation: {e}")
            return {
                "success": False,
                "error": "Payment service unavailable",
                "message": "Unable to connect to payment service"
            }
        except Exception as e:
            logger.error(f"Error during refund initiation: {e}")
            return {
                "success": False,
                "error": "Refund processing failed",
                "message": "An error occurred while processing refund"
            }
    
    async def process_default_refund(
        self,
        case_id: str,
        paynow_transaction_ref: str,
        payment_request_id: str
    ) -> Dict[str, Any]:
        """
        Process complete refund workflow when practitioner defaults
        This includes:
        1. Reverse ledger entries
        2. Reverse escrow
        3. Initiate Paynow refund
        4. Update case status
        5. Revoke firm access
        
        Args:
            case_id: Case ID
            paynow_transaction_ref: Paynow transaction reference
            payment_request_id: Payment request ID
            
        Returns:
            Result dictionary
        """
        try:
            database = get_database()
            
            # Step 1: Reverse payment split (ledger + escrow)
            ledger_result = await reverse_payment_on_default(case_id, payment_request_id)
            
            # Step 2: Initiate Paynow refund (full $5.00)
            refund_result = await self.initiate_refund(
                paynow_transaction_ref=paynow_transaction_ref,
                amount=self.admin_fee,
                reason="Practitioner default - 72-hour SLA exceeded"
            )
            
            # Step 3: Update case status to REFUNDED
            await database.applications.update_one(
                {"_id": case_id},
                {
                    "$set": {
                        "case_status": CaseStatus.REFUNDED,
                        "payment.status": PaymentStatus.REFUNDED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Step 4: Revoke firm access to dossier
            await self._revoke_firm_access(case_id)
            
            # Step 5: Mark SLA timer as refund triggered
            await sla_timer_service.trigger_refund(case_id, datetime.utcnow())
            
            logger.info(f"Processed default refund for case {case_id}")
            
            return {
                "success": True,
                "ledger_reversed": ledger_result.get("success", False),
                "refund_initiated": refund_result.get("success", False),
                "refund_reference": refund_result.get("refund_reference"),
                "message": "Default refund processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error processing default refund for case {case_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process default refund"
            }
    
    async def _revoke_firm_access(self, case_id: str) -> bool:
        """
        Revoke defaulting firm's access to client dossier
        
        Args:
            case_id: Case ID
            
        Returns:
            True if successful
        """
        try:
            database = get_database()
            
            # Get the case to find the assigned firm
            case = await database.applications.find_one({"_id": case_id})
            if not case:
                return False
            
            # Clear the conveyancer assignment to revoke access
            await database.applications.update_one(
                {"_id": case_id},
                {
                    "$set": {
                        "selected_conveyancer": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Revoked firm access for case {case_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking firm access: {e}")
            return False
    
    async def check_refund_status(self, refund_reference: str) -> Dict[str, Any]:
        """
        Check status of a refund
        
        Args:
            refund_reference: Refund reference from Paynow
            
        Returns:
            Dictionary with refund status
        """
        try:
            # This would call Paynow's refund status endpoint
            # For now, return a placeholder
            return {
                "success": True,
                "status": "PROCESSING",
                "message": "Refund status check not fully implemented"
            }
            
        except Exception as e:
            logger.error(f"Error checking refund status: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global refund service instance
refund_service = PaynowRefundService()


async def handle_practitioner_default(
    case_id: str,
    paynow_transaction_ref: str,
    payment_request_id: str
) -> Dict[str, Any]:
    """
    Handle practitioner default (72-hour timeout)
    This is the main entry point for the default workflow
    
    Args:
        case_id: Case ID
        paynow_transaction_ref: Paynow transaction reference
        payment_request_id: Payment request ID
        
    Returns:
        Result dictionary
    """
    return await refund_service.process_default_refund(
        case_id=case_id,
        paynow_transaction_ref=paynow_transaction_ref,
        payment_request_id=payment_request_id
    )
