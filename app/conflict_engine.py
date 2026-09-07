"""
Conflict of Interest Engine
Checks for conflicts before case assignment and reassignment
"""
import logging
from typing import Dict, Any, List, Optional
from app.models import ConflictCheckStatus, ApplicationModel, ConveyancerModel
from app.database import get_database

logger = logging.getLogger(__name__)


class ConflictOfInterestEngine:
    """Engine for detecting conflicts of interest"""
    
    def __init__(self):
        pass
    
    async def check_conflict_for_new_case(
        self,
        client_phone: str,
        client_name: Optional[str] = None,
        client_id_number: Optional[str] = None,
        parties: Optional[List[Dict[str, Any]]] = None,
        entities: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Check for conflicts when creating a new case
        
        Args:
            client_phone: Client phone number
            client_name: Optional client full name
            client_id_number: Optional client ID number
            parties: List of other parties involved in the case
            entities: List of companies/entities involved
            
        Returns:
            Dictionary with conflict check result
        """
        try:
            database = get_database()
            
            # Check if client has existing cases with any firm
            existing_cases = await database.applications.find({
                "owner_phone": client_phone,
                "case_status": {"$in": ["NEW", "ASSIGNED", "WAITING_RESPONSE", "COMPLETE"]}
            }).to_list(length=100)
            
            conflicts = []
            
            # Check for conflicts with existing cases
            for case in existing_cases:
                conveyancer = case.get("selected_conveyancer")
                if conveyancer:
                    conflict = {
                        "type": "existing_client",
                        "firm_id": conveyancer.get("company_name"),
                        "case_id": str(case.get("_id")),
                        "service_type": case.get("service_type"),
                        "created_at": case.get("created_at")
                    }
                    conflicts.append(conflict)
            
            # Check party conflicts if provided
            if parties:
                for party in parties:
                    party_name = party.get("name")
                    party_id = party.get("id_number")
                    
                    # Search for cases with matching parties
                    party_conflicts = await database.applications.find({
                        "extracted_profile.full_name": party_name
                    }).to_list(length=50)
                    
                    for conflict_case in party_conflicts:
                        conveyancer = conflict_case.get("selected_conveyancer")
                        if conveyancer:
                            conflicts.append({
                                "type": "party_conflict",
                                "party_name": party_name,
                                "firm_id": conveyancer.get("company_name"),
                                "case_id": str(conflict_case.get("_id"))
                            })
            
            # Check entity conflicts if provided
            if entities:
                for entity in entities:
                    entity_name = entity.get("name")
                    
                    # Search for cases with matching entities
                    entity_conflicts = await database.applications.find({
                        "text_inputs": entity_name
                    }).to_list(length=50)
                    
                    for conflict_case in entity_conflicts:
                        conveyancer = conflict_case.get("selected_conveyancer")
                        if conveyancer:
                            conflicts.append({
                                "type": "entity_conflict",
                                "entity_name": entity_name,
                                "firm_id": conveyancer.get("company_name"),
                                "case_id": str(conflict_case.get("_id"))
                            })
            
            has_conflict = len(conflicts) > 0
            
            return {
                "has_conflict": has_conflict,
                "conflicts": conflicts,
                "status": ConflictCheckStatus.FAILED if has_conflict else ConflictCheckStatus.PASSED,
                "message": "Conflict detected" if has_conflict else "No conflicts found"
            }
            
        except Exception as e:
            logger.error(f"Error checking conflict for new case: {e}")
            return {
                "has_conflict": False,
                "status": ConflictCheckStatus.NOT_RUN,
                "error": str(e)
            }
    
    async def check_conflict_for_reassignment(
        self,
        case_id: str,
        target_firm_id: str
    ) -> Dict[str, Any]:
        """
        Check for conflicts before reassigning a case to a different firm
        
        Args:
            case_id: Current case ID
            target_firm_id: Target firm ID to check against
            
        Returns:
            Dictionary with conflict check result
        """
        try:
            database = get_database()
            
            # Get the case details
            case = await database.applications.find_one({"_id": case_id})
            if not case:
                return {
                    "has_conflict": True,
                    "status": ConflictCheckStatus.FAILED,
                    "error": "Case not found"
                }
            
            # Get client information
            client_phone = case.get("owner_phone")
            client_profile = case.get("extracted_profile", {})
            client_name = client_profile.get("full_name")
            client_id = client_profile.get("id_number")
            
            # Check if target firm has existing cases with this client
            existing_cases = await database.applications.find({
                "owner_phone": client_phone,
                "selected_conveyancer.company_name": target_firm_id,
                "_id": {"$ne": case_id}
            }).to_list(length=100)
            
            conflicts = []
            
            if existing_cases:
                for conflict_case in existing_cases:
                    conflicts.append({
                        "type": "existing_client",
                        "firm_id": target_firm_id,
                        "case_id": str(conflict_case.get("_id")),
                        "service_type": conflict_case.get("service_type")
                    })
            
            # Check for party conflicts in current case against target firm's other cases
            # This would require extracting parties from the current case
            # and checking against the target firm's case history
            
            has_conflict = len(conflicts) > 0
            
            return {
                "has_conflict": has_conflict,
                "conflicts": conflicts,
                "status": ConflictCheckStatus.FAILED if has_conflict else ConflictCheckStatus.PASSED,
                "message": "Conflict detected with target firm" if has_conflict else "No conflicts with target firm"
            }
            
        except Exception as e:
            logger.error(f"Error checking conflict for reassignment: {e}")
            return {
                "has_conflict": False,
                "status": ConflictCheckStatus.NOT_RUN,
                "error": str(e)
            }
    
    async def check_firm_client_history(
        self,
        firm_id: str,
        client_phone: str
    ) -> Dict[str, Any]:
        """
        Check if a firm has history with a client
        
        Args:
            firm_id: Law firm ID/name
            client_phone: Client phone number
            
        Returns:
            Dictionary with client history
        """
        try:
            database = get_database()
            
            cases = await database.applications.find({
                "owner_phone": client_phone,
                "selected_conveyancer.company_name": firm_id
            }).to_list(length=100)
            
            return {
                "has_history": len(cases) > 0,
                "case_count": len(cases),
                "cases": [
                    {
                        "case_id": str(case.get("_id")),
                        "service_type": case.get("service_type"),
                        "created_at": case.get("created_at"),
                        "case_status": case.get("case_status")
                    }
                    for case in cases
                ]
            }
            
        except Exception as e:
            logger.error(f"Error checking firm client history: {e}")
            return {
                "has_history": False,
                "case_count": 0,
                "error": str(e)
            }
    
    async def get_available_firms_for_reassignment(
        self,
        case_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of firms available for reassignment (excluding conflicted firms)
        
        Args:
            case_id: Current case ID
            
        Returns:
            List of available firms without conflicts
        """
        try:
            database = get_database()
            
            # Get the case
            case = await database.applications.find_one({"_id": case_id})
            if not case:
                return []
            
            client_phone = case.get("owner_phone")
            
            # Get all active conveyancers
            all_conveyancers = await database.conveyancers.find({}).to_list(length=None)
            
            available_firms = []
            
            for conveyancer in all_conveyancers:
                firm_name = conveyancer.get("company_name")
                
                # Check for conflict
                conflict_check = await self.check_firm_client_history(firm_name, client_phone)
                
                if not conflict_check.get("has_history"):
                    available_firms.append({
                        "firm_id": firm_name,
                        "company_name": firm_name,
                        "contact_person": conveyancer.get("contact_person"),
                        "email": conveyancer.get("email"),
                        "phone_number": conveyancer.get("phone_number"),
                        "province": conveyancer.get("province")
                    })
            
            return available_firms
            
        except Exception as e:
            logger.error(f"Error getting available firms for reassignment: {e}")
            return []
    
    async def update_case_conflict_status(
        self,
        case_id: str,
        status: ConflictCheckStatus,
        conflicts: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Update conflict check status on a case
        
        Args:
            case_id: Case ID
            status: Conflict check status
            conflicts: Optional list of conflicts found
            
        Returns:
            True if successful
        """
        try:
            database = get_database()
            
            update_data = {
                "conflict_check_status": status,
                "updated_at": datetime.utcnow()
            }
            
            if conflicts:
                update_data["conflicts"] = conflicts
            
            result = await database.applications.update_one(
                {"_id": case_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating case conflict status: {e}")
            return False


# Global conflict engine instance
conflict_engine = ConflictOfInterestEngine()


async def run_conflict_check_on_intake(
    client_phone: str,
    client_name: Optional[str] = None,
    client_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run conflict check when client submits a new case
    
    Args:
        client_phone: Client phone number
        client_name: Optional client name
        client_id: Optional client ID
        
    Returns:
        Conflict check result
    """
    return await conflict_engine.check_conflict_for_new_case(
        client_phone=client_phone,
        client_name=client_name,
        client_id_number=client_id
    )


async def run_conflict_check_for_reassignment(
    case_id: str,
    target_firm_id: str
) -> Dict[str, Any]:
    """
    Run conflict check before reassigning a case
    
    Args:
        case_id: Case ID
        target_firm_id: Target firm ID
        
    Returns:
        Conflict check result
    """
    return await conflict_engine.check_conflict_for_reassignment(
        case_id=case_id,
        target_firm_id=target_firm_id
    )
