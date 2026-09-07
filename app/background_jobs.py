"""
Background Jobs Service
Handles scheduled background tasks including SLA timeout checking
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
from app.sla_timer_service import sla_timer_service
from app.refund_service import handle_practitioner_default
from app.reassignment_service import activate_reassignment_after_default
from app.audit_service import log_access_revocation
from app.database import get_database
from app.models import CaseStatus

logger = logging.getLogger(__name__)


class BackgroundJobsService:
    """Service for managing background scheduled jobs"""
    
    def __init__(self):
        self.is_running = False
    
    async def check_sla_timeouts(self) -> Dict[str, Any]:
        """
        Check for SLA timeouts and trigger default workflow
        This should be run periodically (e.g., every 5 minutes)
        
        Returns:
            Result dictionary with timeout processing results
        """
        try:
            logger.info("Checking for SLA timeouts...")
            
            # Get all expired timers
            expired_timers = await sla_timer_service.get_expired_timers()
            
            if not expired_timers:
                logger.info("No expired SLA timers found")
                return {
                    "success": True,
                    "expired_count": 0,
                    "processed_count": 0,
                    "message": "No expired timers to process"
                }
            
            logger.info(f"Found {len(expired_timers)} expired SLA timers")
            
            processed_count = 0
            errors = []
            
            for timer in expired_timers:
                try:
                    case_id = timer.case_id
                    
                    # Get the case details
                    database = get_database()
                    case = await database.applications.find_one({"_id": case_id})
                    
                    if not case:
                        logger.warning(f"Case {case_id} not found for expired timer")
                        continue
                    
                    # Check if already processed
                    if case.get("case_status") == CaseStatus.PRACTITIONER_DEFAULT:
                        logger.info(f"Case {case_id} already in default state, skipping")
                        continue
                    
                    # Get payment details
                    paynow_transaction_ref = case.get("payment", {}).get("transaction_id")
                    payment_request_id = case.get("paynow_payment_request_id")
                    
                    if not paynow_transaction_ref or not payment_request_id:
                        logger.error(f"Case {case_id} missing payment details for refund")
                        errors.append({
                            "case_id": case_id,
                            "error": "Missing payment details"
                        })
                        continue
                    
                    # Step 1: Trigger default state in timer
                    await sla_timer_service.trigger_default_state(case_id, datetime.utcnow())
                    
                    # Step 2: Update case status to default
                    await database.applications.update_one(
                        {"_id": case_id},
                        {
                            "$set": {
                                "case_status": CaseStatus.PRACTITIONER_DEFAULT,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    # Step 3: Process refund (reverse ledger, reverse escrow, initiate Paynow refund)
                    refund_result = await handle_practitioner_default(
                        case_id=case_id,
                        paynow_transaction_ref=paynow_transaction_ref,
                        payment_request_id=payment_request_id
                    )
                    
                    # Step 4: Log access revocation
                    conveyancer = case.get("selected_conveyancer")
                    if conveyancer:
                        await log_access_revocation(
                            case_id=case_id,
                            firm_id=conveyancer.get("company_name"),
                            revoked_by="system"
                        )
                    
                    # Step 5: Activate reassignment matrix
                    reassignment_result = await activate_reassignment_after_default(case_id)
                    
                    processed_count += 1
                    
                    logger.info(f"Processed default workflow for case {case_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing timeout for case {timer.case_id}: {e}")
                    errors.append({
                        "case_id": timer.case_id,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "expired_count": len(expired_timers),
                "processed_count": processed_count,
                "errors": errors,
                "message": f"Processed {processed_count} expired timers"
            }
            
        except Exception as e:
            logger.error(f"Error in SLA timeout check: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check SLA timeouts"
            }
    
    async def start_background_worker(self, interval_seconds: int = 300):
        """
        Start background worker to check SLA timeouts periodically
        
        Args:
            interval_seconds: Interval between checks (default: 300 seconds = 5 minutes)
        """
        if self.is_running:
            logger.warning("Background worker already running")
            return
        
        self.is_running = True
        logger.info(f"Starting background worker with {interval_seconds}s interval")
        
        while self.is_running:
            try:
                await self.check_sla_timeouts()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in background worker: {e}")
                await asyncio.sleep(interval_seconds)
    
    def stop_background_worker(self):
        """Stop the background worker"""
        self.is_running = False
        logger.info("Background worker stopped")
    
    async def run_single_check(self) -> Dict[str, Any]:
        """
        Run a single SLA timeout check (for manual triggering or testing)
        
        Returns:
            Result dictionary
        """
        return await self.check_sla_timeouts()


# Global background jobs service instance
background_jobs_service = BackgroundJobsService()


async def run_sla_timeout_check() -> Dict[str, Any]:
    """
    Convenience function to run a single SLA timeout check
    This can be called from an API endpoint or cron job
    
    Returns:
        Result dictionary
    """
    return await background_jobs_service.run_single_check()
