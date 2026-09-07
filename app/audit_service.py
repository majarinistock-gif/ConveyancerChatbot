"""
Audit Trail and Evidence Integrity Service
Maintains tamper-evident audit logs for legal evidence chain of custody
"""
import logging
import uuid
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models import DossierAccessEventModel, AccessEventType
from app.database import get_database

logger = logging.getLogger(__name__)


class AuditTrailService:
    """Service for managing audit trails and evidence integrity"""
    
    def __init__(self):
        pass
    
    async def log_access_event(
        self,
        case_id: str,
        actor_id: str,
        actor_role: str,
        event_type: AccessEventType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DossierAccessEventModel:
        """
        Log an access event for a dossier
        
        Args:
            case_id: Case ID
            actor_id: Actor user ID
            actor_role: Actor role (practitioner, client, admin, etc.)
            event_type: Type of access event
            metadata: Optional metadata about the event
            
        Returns:
            Created audit event model
        """
        event_id = str(uuid.uuid4())
        
        # Get previous hash for chain integrity
        previous_hash = await self._get_previous_hash(case_id)
        
        # Create hash for this event
        event_data = {
            "event_id": event_id,
            "case_id": case_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "event_type": event_type,
            "occurred_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        current_hash = self._compute_hash(event_data, previous_hash)
        
        event = DossierAccessEventModel(
            event_id=event_id,
            case_id=case_id,
            actor_id=actor_id,
            actor_role=actor_role,
            event_type=event_type,
            hash_chain_prev=previous_hash,
            hash_chain_curr=current_hash,
            metadata=metadata or {}
        )
        
        database = get_database()
        await database.dossier_access_events.insert_one(event.model_dump(by_alias=True))
        
        logger.info(f"Logged access event {event_id} for case {case_id}: {event_type}")
        
        return event
    
    async def get_case_audit_trail(
        self,
        case_id: str,
        limit: int = 100
    ) -> List[DossierAccessEventModel]:
        """
        Get audit trail for a case
        
        Args:
            case_id: Case ID
            limit: Maximum number of events to return
            
        Returns:
            List of audit event models
        """
        database = get_database()
        cursor = database.dossier_access_events.find(
            {"case_id": case_id}
        ).sort("occurred_at", -1).limit(limit)
        
        events = []
        async for event_data in cursor:
            events.append(DossierAccessEventModel(**event_data))
        
        return events
    
    async def verify_integrity(
        self,
        case_id: str
    ) -> Dict[str, Any]:
        """
        Verify the integrity of the audit trail hash chain
        
        Args:
            case_id: Case ID
            
        Returns:
            Dictionary with integrity verification result
        """
        try:
            events = await self.get_case_audit_trail(case_id, limit=1000)
            
            if not events:
                return {
                    "valid": True,
                    "message": "No audit events to verify"
                }
            
            # Sort by occurrence time to verify chain
            events_sorted = sorted(events, key=lambda e: e.occurred_at)
            
            valid = True
            broken_at = None
            
            for i, event in enumerate(events_sorted):
                if i == 0:
                    # First event should have no previous hash
                    if event.hash_chain_prev is not None:
                        valid = False
                        broken_at = event.event_id
                        break
                else:
                    # Verify hash chain
                    prev_event = events_sorted[i - 1]
                    expected_hash = self._compute_hash(
                        {
                            "event_id": prev_event.event_id,
                            "case_id": prev_event.case_id,
                            "actor_id": prev_event.actor_id,
                            "actor_role": prev_event.actor_role,
                            "event_type": prev_event.event_type,
                            "occurred_at": prev_event.occurred_at,
                            "metadata": prev_event.metadata
                        },
                        prev_event.hash_chain_prev
                    )
                    
                    if event.hash_chain_prev != expected_hash:
                        valid = False
                        broken_at = event.event_id
                        break
            
            return {
                "valid": valid,
                "total_events": len(events),
                "broken_at": broken_at,
                "message": "Audit trail integrity verified" if valid else "Audit trail integrity compromised"
            }
            
        except Exception as e:
            logger.error(f"Error verifying audit trail integrity: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def export_evidence_bundle(
        self,
        case_id: str
    ) -> Dict[str, Any]:
        """
        Export evidence bundle for legal proceedings
        Includes audit trail, documents, and integrity verification
        
        Args:
            case_id: Case ID
            
        Returns:
            Dictionary with evidence bundle
        """
        try:
            # Get audit trail
            audit_trail = await self.get_case_audit_trail(case_id)
            
            # Verify integrity
            integrity = await self.verify_integrity(case_id)
            
            # Get case details
            database = get_database()
            case = await database.applications.find_one({"_id": case_id})
            
            return {
                "case_id": case_id,
                "export_timestamp": datetime.utcnow(),
                "audit_trail": [
                    {
                        "event_id": e.event_id,
                        "actor_id": e.actor_id,
                        "actor_role": e.actor_role,
                        "event_type": e.event_type,
                        "occurred_at": e.occurred_at,
                        "hash": e.hash_chain_curr
                    }
                    for e in audit_trail
                ],
                "integrity_verification": integrity,
                "case_details": {
                    "service_type": case.get("service_type") if case else None,
                    "created_at": case.get("created_at") if case else None,
                    "owner_phone": case.get("owner_phone") if case else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error exporting evidence bundle: {e}")
            return {
                "error": str(e)
            }
    
    async def _get_previous_hash(self, case_id: str) -> Optional[str]:
        """
        Get the hash of the most recent event for a case
        
        Args:
            case_id: Case ID
            
        Returns:
            Previous hash or None
        """
        database = get_database()
        latest_event = await database.dossier_access_events.find_one(
            {"case_id": case_id},
            sort=[("occurred_at", -1)]
        )
        
        if latest_event:
            return latest_event.get("hash_chain_curr")
        
        return None
    
    def _compute_hash(self, data: Dict[str, Any], previous_hash: Optional[str] = None) -> str:
        """
        Compute hash for audit event
        
        Args:
            data: Event data
            previous_hash: Previous hash in chain
            
        Returns:
            Computed hash
        """
        # Convert data to string
        data_str = str(data)
        
        # Include previous hash if exists
        if previous_hash:
            data_str += previous_hash
        
        # Compute SHA-256 hash
        return hashlib.sha256(data_str.encode()).hexdigest()


# Global audit service instance
audit_service = AuditTrailService()


async def log_case_view(case_id: str, actor_id: str, actor_role: str) -> Dict[str, Any]:
    """
    Log a case view event
    
    Args:
        case_id: Case ID
        actor_id: Actor ID
        actor_role: Actor role
        
    Returns:
        Result dictionary
    """
    event = await audit_service.log_access_event(
        case_id=case_id,
        actor_id=actor_id,
        actor_role=actor_role,
        event_type=AccessEventType.VIEW
    )
    
    return {
        "success": True,
        "event_id": event.event_id
    }


async def log_case_edit(case_id: str, actor_id: str, actor_role: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Log a case edit event
    
    Args:
        case_id: Case ID
        actor_id: Actor ID
        actor_role: Actor role
        metadata: Optional metadata about the edit
        
    Returns:
        Result dictionary
    """
    event = await audit_service.log_access_event(
        case_id=case_id,
        actor_id=actor_id,
        actor_role=actor_role,
        event_type=AccessEventType.EDIT,
        metadata=metadata
    )
    
    return {
        "success": True,
        "event_id": event.event_id
    }


async def log_practitioner_acknowledgment(case_id: str, practitioner_id: str) -> Dict[str, Any]:
    """
    Log practitioner acknowledgment event
    
    Args:
        case_id: Case ID
        practitioner_id: Practitioner ID
        
    Returns:
        Result dictionary
    """
    event = await audit_service.log_access_event(
        case_id=case_id,
        actor_id=practitioner_id,
        actor_role="practitioner",
        event_type=AccessEventType.ACKNOWLEDGE
    )
    
    return {
        "success": True,
        "event_id": event.event_id
    }


async def log_practitioner_response(case_id: str, practitioner_id: str) -> Dict[str, Any]:
    """
    Log practitioner response event
    
    Args:
        case_id: Case ID
        practitioner_id: Practitioner ID
        
    Returns:
        Result dictionary
    """
    event = await audit_service.log_access_event(
        case_id=case_id,
        actor_id=practitioner_id,
        actor_role="practitioner",
        event_type=AccessEventType.RESPOND
    )
    
    return {
        "success": True,
        "event_id": event.event_id
    }


async def log_case_assignment(case_id: str, firm_id: str, assigned_by: str) -> Dict[str, Any]:
    """
    Log case assignment event
    
    Args:
        case_id: Case ID
        firm_id: Firm ID
        assigned_by: Who made the assignment
        
    Returns:
        Result dictionary
    """
    event = await audit_service.log_access_event(
        case_id=case_id,
        actor_id=assigned_by,
        actor_role="system",
        event_type=AccessEventType.ASSIGN,
        metadata={"firm_id": firm_id}
    )
    
    return {
        "success": True,
        "event_id": event.event_id
    }


async def log_access_revocation(case_id: str, firm_id: str, revoked_by: str) -> Dict[str, Any]:
    """
    Log access revocation event
    
    Args:
        case_id: Case ID
        firm_id: Firm ID being revoked
        revoked_by: Who revoked access
        
    Returns:
        Result dictionary
    """
    event = await audit_service.log_access_event(
        case_id=case_id,
        actor_id=revoked_by,
        actor_role="system",
        event_type=AccessEventType.REVOKE,
        metadata={"firm_id": firm_id}
    )
    
    return {
        "success": True,
        "event_id": event.event_id
    }
