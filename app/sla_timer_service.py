"""
SLA Timer Service for 72-Hour Rule
Manages the deterministic 72-hour timer for practitioner response SLA
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.models import (
    SLATimerModel, SLATimerState, CaseStatus, ApplicationModel
)
from app.database import get_database

logger = logging.getLogger(__name__)

# 72 hours in seconds
SEVENTY_TWO_HOURS_SECONDS = 259200


class SLATimerService:
    """Service for managing 72-hour SLA timers"""
    
    def __init__(self):
        self.timer_duration_seconds = SEVENTY_TWO_HOURS_SECONDS
    
    async def create_timer(self, case_id: str, start_time: datetime) -> SLATimerModel:
        """
        Create and start SLA timer for a case
        
        Args:
            case_id: Application/case ID
            start_time: Time when timer should start (usually Paynow confirmation time)
            
        Returns:
            Created SLA timer model
        """
        timer_id = str(uuid.uuid4())
        deadline_at = start_time + timedelta(seconds=self.timer_duration_seconds)
        
        timer = SLATimerModel(
            timer_id=timer_id,
            case_id=case_id,
            state=SLATimerState.RUNNING,
            started_at=start_time,
            deadline_at=deadline_at
        )
        
        database = get_database()
        await database.sla_timers.insert_one(timer.model_dump(by_alias=True))
        
        logger.info(f"Created SLA timer for case {case_id}, deadline: {deadline_at}")
        
        return timer
    
    async def get_timer(self, case_id: str) -> Optional[SLATimerModel]:
        """
        Get SLA timer for a case
        
        Args:
            case_id: Application/case ID
            
        Returns:
            SLA timer model or None
        """
        database = get_database()
        timer_data = await database.sla_timers.find_one({"case_id": case_id})
        
        if timer_data:
            return SLATimerModel(**timer_data)
        return None
    
    async def record_acknowledgment(self, case_id: str, acknowledged_at: datetime) -> bool:
        """
        Record practitioner acknowledgment - successful state
        
        Args:
            case_id: Application/case ID
            acknowledged_at: Time of
            
        Returns:
            True if successful
        """
        database = get_database()
        
        result = await database.sla_timers.update_one(
            {"case_id": case_id, "state": SLATimerState.RUNNING},
            {
                "$set": {
                    "state": SLATimerState.COMPLETE,
                    "acknowledgment_received_at": acknowledged_at,
                    "ended_at": acknowledged_at
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Recorded acknowledgment for case {case_id}")
            return True
        
        return False
    
    async def record_response(self, case_id: str, responded_at: datetime) -> bool:
        """
        Record practitioner response - successful state
        
        Args:
            case_id: Application/case ID
            responded_at: Time of response
            
        Returns:
            True if successful
        """
        database = get_database()
        
        result = await database.sla_timers.update_one(
            {"case_id": case_id, "state": SLATimerState.RUNNING},
            {
                "$set": {
                    "state": SLATimerState.COMPLETE,
                    "response_received_at": responded_at,
                    "ended_at": responded_at
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Recorded response for case {case_id}")
            return True
        
        return False
    
    async def trigger_default_state(self, case_id: str, default_time: datetime) -> bool:
        """
        Trigger practitioner default state - 72-hour timeout
        
        Args:
            case_id: Application/case ID
            default_time: Time when default occurred
            
        Returns:
            True if successful
        """
        database = get_database()
        
        result = await database.sla_timers.update_one(
            {"case_id": case_id, "state": SLATimerState.RUNNING},
            {
                "$set": {
                    "state": SLATimerState.PRACTITIONER_DEFAULT,
                    "ended_at": default_time
                }
            }
        )
        
        if result.modified_count > 0:
            logger.warning(f"Triggered default state for case {case_id}")
            return True
        
        return False
    
    async def trigger_refund(self, case_id: str, refund_time: datetime) -> bool:
        """
        Mark timer as refund triggered
        
        Args:
            case_id: Application/case ID
            refund_time: Time when refund was triggered
            
        Returns:
            True if successful
        """
        database = get_database()
        
        result = await database.sla_timers.update_one(
            {"case_id": case_id},
            {
                "$set": {
                    "state": SLATimerState.REFUND_TRIGGERED,
                    "ended_at": refund_time
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Marked timer as refund triggered for case {case_id}")
            return True
        
        return False
    
    async def check_timeout(self, case_id: str) -> Dict[str, Any]:
        """
        Check if timer has exceeded 72-hour deadline
        
        Args:
            case_id: Application/case ID
            
        Returns:
            Dictionary with timeout status and time remaining
        """
        timer = await self.get_timer(case_id)
        
        if not timer:
            return {"error": "Timer not found"}
        
        if timer.state != SLATimerState.RUNNING:
            return {
                "case_id": case_id,
                "state": timer.state,
                "is_timeout": False,
                "message": f"Timer is not running (state: {timer.state})"
            }
        
        now = datetime.utcnow()
        time_remaining = timer.deadline_at - now if timer.deadline_at > now else timedelta(0)
        
        is_timeout = time_remaining.total_seconds() <= 0
        
        return {
            "case_id": case_id,
            "state": timer.state,
            "deadline_at": timer.deadline_at,
            "time_remaining_seconds": time_remaining.total_seconds(),
            "is_timeout": is_timeout,
            "started_at": timer.started_at
        }
    
    async def get_all_active_timers(self) -> list[SLATimerModel]:
        """
        Get all currently running SLA timers
        
        Returns:
            List of running SLA timer models
        """
        database = get_database()
        cursor = database.sla_timers.find({"state": SLATimerState.RUNNING})
        
        timers = []
        async for timer_data in cursor:
            timers.append(SLATimerModel(**timer_data))
        
        return timers
    
    async def get_expired_timers(self) -> list[SLATimerModel]:
        """
        Get all timers that have exceeded their deadline
        
        Returns:
            List of expired SLA timer models
        """
        database = get_database()
        now = datetime.utcnow()
        
        cursor = database.sla_timers.find({
            "state": SLATimerState.RUNNING,
            "deadline_at": {"$lte": now}
        })
        
        timers = []
        async for timer_data in cursor:
            timers.append(SLATimerModel(**timer_data))
        
        return timers
    
    async def update_case_status(self, case_id: str, new_status: CaseStatus) -> bool:
        """
        Update case status in application document
        
        Args:
            case_id: Application/case ID
            new_status: New case status
            
        Returns:
            True if successful
        """
        database = get_database()
        
        result = await database.applications.update_one(
            {"_id": case_id},
            {
                "$set": {
                    "case_status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated case {case_id} status to {new_status}")
            return True
        
        return False


# Global SLA timer service instance
sla_timer_service = SLATimerService()


async def start_sla_timer_on_payment_confirmation(case_id: str, confirmed_at: datetime) -> Dict[str, Any]:
    """
    Start SLA timer when Paynow payment is confirmed
    This is called from the payment callback webhook
    
    Args:
        case_id: Application/case ID
        confirmed_at: Payment confirmation timestamp
        
    Returns:
        Result dictionary
    """
    try:
        # Create timer
        timer = await sla_timer_service.create_timer(case_id, confirmed_at)
        
        # Update application status
        await sla_timer_service.update_case_status(case_id, CaseStatus.WAITING_RESPONSE)
        
        # Update application with timer deadline
        database = get_database()
        await database.applications.update_one(
            {"_id": case_id},
            {
                "$set": {
                    "paynow_confirmed_at": confirmed_at,
                    "timer_deadline_at": timer.deadline_at,
                    "sla_timer.deadline_at": timer.deadline_at,
                    "sla_timer.started_at": timer.started_at,
                    "sla_timer.state": SLATimerState.RUNNING,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "timer_id": timer.timer_id,
            "deadline_at": timer.deadline_at,
            "message": "SLA timer started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting SLA timer for case {case_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start SLA timer"
        }


async def handle_practitioner_acknowledgment(case_id: str) -> Dict[str, Any]:
    """
    Handle practitioner acknowledgment - successful completion
    This would be called when a practitioner acknowledges a case
    
    Args:
        case_id: Application/case ID
        
    Returns:
        Result dictionary
    """
    try:
        now = datetime.utcnow()
        
        # Record acknowledgment in timer
        await sla_timer_service.record_acknowledgment(case_id, now)
        
        # Update case status to complete
        await sla_timer_service.update_case_status(case_id, CaseStatus.COMPLETE)
        
        # Update application
        database = get_database()
        await database.applications.update_one(
            {"_id": case_id},
            {
                "$set": {
                    "sla_timer.state": SLATimerState.COMPLETE,
                    "sla_timer.acknowledgment_received_at": now,
                    "sla_timer.ended_at": now,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Practitioner acknowledgment recorded"
        }
        
    except Exception as e:
        logger.error(f"Error handling acknowledgment for case {case_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def handle_practitioner_response(case_id: str) -> Dict[str, Any]:
    """
    Handle practitioner response - successful completion
    This would be called when a practitioner responds to a case
    
    Args:
        case_id: Application/case ID
        
    Returns:
        Result dictionary
    """
    try:
        now = datetime.utcnow()
        
        # Record response in timer
        await sla_timer_service.record_response(case_id, now)
        
        # Update case status to complete
        await sla_timer_service.update_case_status(case_id, CaseStatus.COMPLETE)
        
        # Update application
        database = get_database()
        await database.applications.update_one(
            {"_id": case_id},
            {
                "$set": {
                    "sla_timer.state": SLATimerState.COMPLETE,
                    "sla_timer.response_received_at": now,
                    "sla_timer.ended_at": now,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Practitioner response recorded"
        }
        
    except Exception as e:
        logger.error(f"Error handling response for case {case_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }
