"""
Dynamic Reassignment Matrix Service
Handles dynamic reassignment of cases when practitioner defaults
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models import (
    ConveyancerModel, ApplicationModel, CaseStatus, ConflictCheckStatus
)
from app.database import get_database
from app.conflict_engine import conflict_engine
from app.whatsapp_service import send_message

logger = logging.getLogger(__name__)


class ReassignmentMatrixService:
    """Service for managing dynamic case reassignment"""
    
    def __init__(self):
        pass
    
    async def get_available_firms_for_reassignment(
        self,
        case_id: str
    ) -> Dict[str, Any]:
        """
        Get list of available firms for reassignment
        Excludes firms with conflicts and the defaulting firm
        
        Args:
            case_id: Case ID
            
        Returns:
            Dictionary with available firms
        """
        try:
            # Get the case
            database = get_database()
            case = await database.applications.find_one({"_id": case_id})
            
            if not case:
                return {
                    "success": False,
                    "error": "Case not found"
                }
            
            client_phone = case.get("owner_phone")
            
            # Get all active conveyancers
            all_conveyancers = await database.conveyancers.find({}).to_list(length=None)
            
            available_firms = []
            excluded_firms = []
            
            for conveyancer in all_conveyancers:
                firm_name = conveyancer.get("company_name")
                
                # Check for conflict
                conflict_check = await conflict_engine.check_firm_client_history(
                    firm_id=firm_name,
                    client_phone=client_phone
                )
                
                if conflict_check.get("has_history"):
                    excluded_firms.append({
                        "firm_id": firm_name,
                        "company_name": firm_name,
                        "reason": "existing_client_conflict",
                        "case_count": conflict_check.get("case_count")
                    })
                else:
                    available_firms.append({
                        "firm_id": firm_name,
                        "company_name": firm_name,
                        "contact_person": conveyancer.get("contact_person"),
                        "email": conveyancer.get("email"),
                        "phone_number": conveyancer.get("phone_number"),
                        "province": conveyancer.get("province")
                    })
            
            return {
                "success": True,
                "available_firms": available_firms,
                "excluded_firms": excluded_firms,
                "total_available": len(available_firms),
                "total_excluded": len(excluded_firms)
            }
            
        except Exception as e:
            logger.error(f"Error getting available firms for reassignment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def reassign_case_to_firm(
        self,
        case_id: str,
        target_firm_id: str
    ) -> Dict[str, Any]:
        """
        Reassign a case to a new firm
        
        Args:
            case_id: Case ID
            target_firm_id: Target firm ID (company name)
            
        Returns:
            Result dictionary
        """
        try:
            database = get_database()
            
            # Get the case
            case = await database.applications.find_one({"_id": case_id})
            if not case:
                return {
                    "success": False,
                    "error": "Case not found"
                }
            
            # Check conflict with target firm
            conflict_check = await conflict_engine.check_conflict_for_reassignment(
                case_id=case_id,
                target_firm_id=target_firm_id
            )
            
            if conflict_check.get("has_conflict"):
                return {
                    "success": False,
                    "error": "Conflict detected with target firm",
                    "conflicts": conflict_check.get("conflicts")
                }
            
            # Get target firm details
            target_firm = await database.conveyancers.find_one({
                "company_name": target_firm_id
            })
            
            if not target_firm:
                return {
                    "success": False,
                    "error": "Target firm not found"
                }
            
            # Update case with new conveyancer
            new_conveyancer = {
                "company_name": target_firm.get("company_name"),
                "contact_person": target_firm.get("contact_person"),
                "email": target_firm.get("email"),
                "phone_number": target_firm.get("phone_number"),
                "tin_number": target_firm.get("tin_number")
            }
            
            await database.applications.update_one(
                {"_id": case_id},
                {
                    "$set": {
                        "selected_conveyancer": new_conveyancer,
                        "case_status": CaseStatus.ASSIGNED,
                        "conflict_check_status": ConflictCheckStatus.PASSED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Log the reassignment in audit trail
            await self._log_reassignment_event(
                case_id=case_id,
                old_firm=None,  # Previous firm was revoked
                new_firm=target_firm_id
            )
            
            logger.info(f"Reassigned case {case_id} to firm {target_firm_id}")
            
            return {
                "success": True,
                "new_firm": target_firm_id,
                "new_conveyancer": new_conveyancer,
                "message": "Case reassigned successfully"
            }
            
        except Exception as e:
            logger.error(f"Error reassigning case: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def activate_reassignment_matrix(
        self,
        case_id: str
    ) -> Dict[str, Any]:
        """
        Activate the reassignment matrix for a case
        This is called when a practitioner defaults
        
        Args:
            case_id: Case ID
            
        Returns:
            Result dictionary with available firms
        """
        try:
            # Get available firms
            result = await self.get_available_firms_for_reassignment(case_id)
            
            if not result.get("success"):
                return result
            
            # Update case status to indicate reassignment is available
            database = get_database()
            await database.applications.update_one(
                {"_id": case_id},
                {
                    "$set": {
                        "case_status": CaseStatus.ASSIGNED,  # Ready for reassignment
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Notify client via WhatsApp that reassignment is available
            case = await database.applications.find_one({"_id": case_id})
            if case:
                client_phone = case.get("owner_phone")
                await self._send_reassignment_notification(
                    phone_number=client_phone,
                    available_count=result.get("total_available", 0)
                )
            
            return {
                "success": True,
                "available_firms": result.get("available_firms"),
                "excluded_firms": result.get("excluded_firms"),
                "message": "Reassignment matrix activated"
            }
            
        except Exception as e:
            logger.error(f"Error activating reassignment matrix: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _log_reassignment_event(
        self,
        case_id: str,
        old_firm: Optional[str],
        new_firm: str
    ) -> bool:
        """
        Log reassignment event for audit trail
        
        Args:
            case_id: Case ID
            old_firm: Previous firm ID
            new_firm: New firm ID
            
        Returns:
            True if successful
        """
        try:
            # This would integrate with the audit trail service
            # For now, we'll add a simple log entry
            database = get_database()
            
            # Add to application metadata
            await database.applications.update_one(
                {"_id": case_id},
                {
                    "$push": {
                        "metadata.reassignment_history": {
                            "timestamp": datetime.utcnow(),
                            "old_firm": old_firm,
                            "new_firm": new_firm,
                            "event_type": "reassignment"
                        }
                    }
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging reassignment event: {e}")
            return False
    
    async def _send_reassignment_notification(
        self,
        phone_number: str,
        available_count: int
    ) -> bool:
        """
        Send WhatsApp notification to client about reassignment availability
        
        Args:
            phone_number: Client phone number
            available_count: Number of available firms
            
        Returns:
            True if successful
        """
        try:
            message = (
                f"⚠️ Your previous conveyancer did not respond within 72 hours.\n\n"
                f"Your case is now available for reassignment.\n"
                f"There are {available_count} qualified firms available to handle your case.\n\n"
                f"Please select a new firm to continue with your conveyancing matter."
            )
            
            await send_message(phone_number, message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending reassignment notification: {e}")
            return False
    
    async def get_reassignment_options(
        self,
        case_id: str
    ) -> Dict[str, Any]:
        """
        Get formatted reassignment options for client
        
        Args:
            case_id: Case ID
            
        Returns:
            Dictionary with formatted options
        """
        result = await self.get_available_firms_for_reassignment(case_id)
        
        if not result.get("success"):
            return result
        
        available_firms = result.get("available_firms", [])
        
        # Format as numbered list for WhatsApp
        options = []
        for i, firm in enumerate(available_firms, 1):
            options.append(
                f"{i}. {firm['company_name']}\n"
                f"   Contact: {firm['contact_person']}\n"
                f"   Phone: {firm['phone_number']}\n"
                f"   Province: {firm['province']}"
            )
        
        return {
            "success": True,
            "options": options,
            "total_options": len(options),
            "message": "\n\n".join(options) if options else "No firms available for reassignment"
        }


# Global reassignment service instance
reassignment_service = ReassignmentMatrixService()


async def activate_reassignment_after_default(case_id: str) -> Dict[str, Any]:
    """
    Activate reassignment matrix after practitioner default
    This is called from the default handling workflow
    
    Args:
        case_id: Case ID
        
    Returns:
        Result dictionary
    """
    return await reassignment_service.activate_reassignment_matrix(case_id)


async def process_client_reassignment_selection(
    case_id: str,
    selection: str
) -> Dict[str, Any]:
    """
    Process client's selection of new firm for reassignment
    
    Args:
        case_id: Case ID
        selection: Client selection (number or firm name)
        
    Returns:
        Result dictionary
    """
    # Get available firms
    result = await reassignment_service.get_available_firms_for_reassignment(case_id)
    
    if not result.get("success"):
        return result
    
    available_firms = result.get("available_firms", [])
    
    # Parse selection
    try:
        selection_index = int(selection) - 1
        if 0 <= selection_index < len(available_firms):
            target_firm = available_firms[selection_index]["firm_id"]
            return await reassignment_service.reassign_case_to_firm(case_id, target_firm)
        else:
            return {
                "success": False,
                "error": "Invalid selection"
            }
    except ValueError:
        # Try to match by firm name
        for firm in available_firms:
            if selection.lower() in firm["company_name"].lower():
                return await reassignment_service.reassign_case_to_firm(case_id, firm["firm_id"])
        
        return {
            "success": False,
            "error": "Firm not found"
        }
