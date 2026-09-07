"""
Ledger and Escrow Vault Service
Handles payment splits, escrow management, and ledger accounting
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.models import (
    PlatformLedgerModel, EscrowVaultModel, LedgerAllocationType,
    LedgerDirection, LedgerState, EscrowStatus, CaseStatus
)
from app.database import get_database

logger = logging.getLogger(__name__)

# Fixed fee amounts from documentation
ADMIN_FEE_TOTAL = 5.00
SYSTEM_ADMIN_SPLIT = 3.00  # 60%
ESCROW_SPLIT = 2.00  # 40%


class LedgerService:
    """Service for managing platform ledgers and payment splits"""
    
    def __init__(self):
        self.admin_fee_total = ADMIN_FEE_TOTAL
        self.system_admin_split = SYSTEM_ADMIN_SPLIT
        self.escrow_split = ESCROW_SPLIT
    
    async def create_ledger_entry(
        self,
        case_id: str,
        payment_request_id: str,
        allocation_type: LedgerAllocationType,
        direction: LedgerDirection,
        amount_usd: float,
        paynow_transaction_ref: Optional[str] = None,
        escrow_recipient_id: Optional[str] = None
    ) -> PlatformLedgerModel:
        """
        Create a ledger entry
        
        Args:
            case_id: Case ID
            payment_request_id: Paynow payment request ID
            allocation_type: Type of allocation
            direction: Credit or debit
            amount_usd: Amount in USD
            paynow_transaction_ref: Optional Paynow transaction reference
            escrow_recipient_id: Optional recipient ID for escrow
            
        Returns:
            Created ledger model
        """
        ledger_id = str(uuid.uuid4())
        idempotency_key = f"{payment_request_id}_{allocation_type}_{amount_usd}"
        
        ledger = PlatformLedgerModel(
            ledger_id=ledger_id,
            case_id=case_id,
            payment_request_id=payment_request_id,
            paynow_transaction_ref=paynow_transaction_ref,
            allocation_type=allocation_type,
            direction=direction,
            amount_usd=amount_usd,
            state=LedgerState.PENDING,
            escrow_recipient_id=escrow_recipient_id,
            idempotency_key=idempotency_key
        )
        
        database = get_database()
        
        # Check for idempotency - don't create duplicate
        existing = await database.platform_ledgers.find_one({
            "idempotency_key": idempotency_key
        })
        
        if existing:
            logger.info(f"Ledger entry already exists with idempotency key: {idempotency_key}")
            return PlatformLedgerModel(**existing)
        
        await database.platform_ledgers.insert_one(ledger.model_dump(by_alias=True))
        
        logger.info(f"Created ledger entry: {ledger_id} for case {case_id}")
        
        return ledger
    
    async def execute_payment_split(
        self,
        case_id: str,
        payment_request_id: str,
        paynow_transaction_ref: Optional[str] = None,
        firm_id: Optional[str] = None,
        practitioner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the payment split on Paynow confirmation
        USD$3.00 to system admin, USD$2.00 to escrow vault
        
        Args:
            case_id: Case ID
            payment_request_id: Paynow payment request ID
            paynow_transaction_ref: Paynow transaction reference
            firm_id: Firm ID for escrow recipient
            practitioner_id: Practitioner ID for escrow recipient
            
        Returns:
            Result dictionary with ledger entries
        """
        try:
            # Create system admin allocation entry
            admin_ledger = await self.create_ledger_entry(
                case_id=case_id,
                payment_request_id=payment_request_id,
                allocation_type=LedgerAllocationType.SYSTEM_ADMIN_COSTS,
                direction=LedgerDirection.CREDIT,
                amount_usd=self.system_admin_split,
                paynow_transaction_ref=paynow_transaction_ref
            )
            
            # Mark as allocated
            await self.update_ledger_state(admin_ledger.ledger_id, LedgerState.ALLOCATED)
            
            # Create escrow vault allocation entry
            escrow_ledger = await self.create_ledger_entry(
                case_id=case_id,
                payment_request_id=payment_request_id,
                allocation_type=LedgerAllocationType.ATTENDING_ESCROW_VAULT,
                direction=LedgerDirection.CREDIT,
                amount_usd=self.escrow_split,
                paynow_transaction_ref=paynow_transaction_ref,
                escrow_recipient_id=firm_id if firm_id else practitioner_id
            )
            
            # Mark as allocated
            await self.update_ledger_state(escrow_ledger.ledger_id, LedgerState.ALLOCATED)
            
            # Create escrow vault entry
            await self.create_escrow_vault(
                case_id=case_id,
                firm_id=firm_id,
                practitioner_id=practitioner_id,
                amount_usd=self.escrow_split
            )
            
            logger.info(f"Executed payment split for case {case_id}: ${self.system_admin_split} admin, ${self.escrow_split} escrow")
            
            return {
                "success": True,
                "admin_ledger_id": admin_ledger.ledger_id,
                "escrow_ledger_id": escrow_ledger.ledger_id,
                "admin_amount": self.system_admin_split,
                "escrow_amount": self.escrow_split,
                "message": "Payment split executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error executing payment split for case {case_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute payment split"
            }
    
    async def update_ledger_state(
        self,
        ledger_id: str,
        new_state: LedgerState,
        reconciliation_note: Optional[str] = None
    ) -> bool:
        """
        Update ledger state
        
        Args:
            ledger_id: Ledger entry ID
            new_state: New state
            reconciliation_note: Optional reconciliation note
            
        Returns:
            True if successful
        """
        try:
            database = get_database()
            
            update_data = {
                "state": new_state
            }
            
            if reconciliation_note:
                update_data["reconciliation_note"] = reconciliation_note
            
            result = await database.platform_ledgers.update_one(
                {"ledger_id": ledger_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated ledger {ledger_id} to state {new_state}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating ledger state: {e}")
            return False
    
    async def reverse_ledger_entries(
        self,
        case_id: str,
        payment_request_id: str
    ) -> Dict[str, Any]:
        """
        Reverse ledger entries for a case (on refund/default)
        
        Args:
            case_id: Case ID
            payment_request_id: Payment request ID
            
        Returns:
            Result dictionary
        """
        try:
            database = get_database()
            
            # Get all ledger entries for this case
            ledgers = await database.platform_ledgers.find({
                "case_id": case_id,
                "payment_request_id": payment_request_id
            }).to_list(length=10)
            
            reversed_count = 0
            
            for ledger in ledgers:
                if ledger.get("state") in [LedgerState.ALLOCATED, LedgerState.HELD]:
                    # Create reversal entry
                    await self.create_ledger_entry(
                        case_id=case_id,
                        payment_request_id=payment_request_id,
                        allocation_type=LedgerAllocationType.REVERSAL_ADJUSTMENT,
                        direction=LedgerDirection.DEBIT,
                        amount_usd=ledger.get("amount_usd"),
                        paynow_transaction_ref=ledger.get("paynow_transaction_ref")
                    )
                    
                    # Mark original as reversed
                    await self.update_ledger_state(
                        ledger.get("ledger_id"),
                        LedgerState.REVERSED,
                        f"Reversed on default/refund for case {case_id}"
                    )
                    
                    reversed_count += 1
            
            logger.info(f"Reversed {reversed_count} ledger entries for case {case_id}")
            
            return {
                "success": True,
                "reversed_count": reversed_count,
                "message": f"Reversed {reversed_count} ledger entries"
            }
            
        except Exception as e:
            logger.error(f"Error reversing ledger entries: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_case_ledgers(self, case_id: str) -> list[PlatformLedgerModel]:
        """
        Get all ledger entries for a case
        
        Args:
            case_id: Case ID
            
        Returns:
            List of ledger models
        """
        database = get_database()
        cursor = database.platform_ledgers.find({"case_id": case_id})
        
        ledgers = []
        async for ledger_data in cursor:
            ledgers.append(PlatformLedgerModel(**ledger_data))
        
        return ledgers


class EscrowVaultService:
    """Service for managing escrow vaults"""
    
    async def create_escrow_vault(
        self,
        case_id: str,
        firm_id: Optional[str] = None,
        practitioner_id: Optional[str] = None,
        amount_usd: float = ESCROW_SPLIT
    ) -> EscrowVaultModel:
        """
        Create escrow vault entry
        
        Args:
            case_id: Case ID
            firm_id: Firm ID
            practitioner_id: Practitioner ID
            amount_usd: Amount to hold in escrow
            
        Returns:
            Created escrow vault model
        """
        escrow_vault_id = str(uuid.uuid4())
        
        escrow = EscrowVaultModel(
            escrow_vault_id=escrow_vault_id,
            firm_id=firm_id,
            practitioner_id=practitioner_id,
            case_id=case_id,
            escrow_amount_usd=amount_usd,
            status=EscrowStatus.ALLOCATED
        )
        
        database = get_database()
        
        # Check for existing escrow for this case
        existing = await database.escrow_vaults.find_one({"case_id": case_id})
        
        if existing:
            logger.info(f"Escrow vault already exists for case {case_id}")
            return EscrowVaultModel(**existing)
        
        await database.escrow_vaults.insert_one(escrow.model_dump(by_alias=True))
        
        logger.info(f"Created escrow vault {escrow_vault_id} for case {case_id}")
        
        return escrow
    
    async def release_escrow(self, case_id: str) -> bool:
        """
        Release escrow to firm on successful completion
        
        Args:
            case_id: Case ID
            
        Returns:
            True if successful
        """
        try:
            database = get_database()
            
            result = await database.escrow_vaults.update_one(
                {"case_id": case_id, "status": EscrowStatus.HELD},
                {
                    "$set": {
                        "status": EscrowStatus.RELEASED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Released escrow for case {case_id}")
                
                # Update corresponding ledger entry
                ledgers = await database.platform_ledgers.find({
                    "case_id": case_id,
                    "allocation_type": LedgerAllocationType.ATTENDING_ESCROW_VAULT,
                    "state": LedgerState.ALLOCATED
                }).to_list(length=1)
                
                if ledgers:
                    await ledger_service.update_ledger_state(
                        ledgers[0].get("ledger_id"),
                        LedgerState.RELEASED,
                        "Escrow released on case completion"
                    )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error releasing escrow: {e}")
            return False
    
    async def reverse_escrow(self, case_id: str) -> bool:
        """
        Reverse escrow on default/refund
        
        Args:
            case_id: Case ID
            
        Returns:
            True if successful
        """
        try:
            database = get_database()
            
            result = await database.escrow_vaults.update_one(
                {"case_id": case_id},
                {
                    "$set": {
                        "status": EscrowStatus.REVERSED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Reversed escrow for case {case_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error reversing escrow: {e}")
            return False
    
    async def get_escrow(self, case_id: str) -> Optional[EscrowVaultModel]:
        """
        Get escrow vault for a case
        
        Args:
            case_id: Case ID
            
        Returns:
            Escrow vault model or None
        """
        database = get_database()
        escrow_data = await database.escrow_vaults.find_one({"case_id": case_id})
        
        if escrow_data:
            return EscrowVaultModel(**escrow_data)
        return None


# Global service instances
ledger_service = LedgerService()
escrow_vault_service = EscrowVaultService()


async def execute_payment_split_on_confirmation(
    case_id: str,
    payment_request_id: str,
    paynow_transaction_ref: Optional[str] = None,
    firm_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute payment split when Paynow payment is confirmed
    This is called from the payment callback webhook
    
    Args:
        case_id: Case ID
        payment_request_id: Paynow payment request ID
        paynow_transaction_ref: Paynow transaction reference
        firm_id: Firm ID for escrow
        
    Returns:
        Result dictionary
    """
    return await ledger_service.execute_payment_split(
        case_id=case_id,
        payment_request_id=payment_request_id,
        paynow_transaction_ref=paynow_transaction_ref,
        firm_id=firm_id
    )


async def release_escrow_on_completion(case_id: str) -> Dict[str, Any]:
    """
    Release escrow when case is completed successfully
    
    Args:
        case_id: Case ID
        
    Returns:
        Result dictionary
    """
    success = await escrow_vault_service.release_escrow(case_id)
    
    return {
        "success": success,
        "message": "Escrow released successfully" if success else "Failed to release escrow"
    }


async def reverse_payment_on_default(case_id: str, payment_request_id: str) -> Dict[str, Any]:
    """
    Reverse payment split when practitioner defaults
    
    Args:
        case_id: Case ID
        payment_request_id: Payment request ID
        
    Returns:
        Result dictionary
    """
    # Reverse ledger entries
    ledger_result = await ledger_service.reverse_ledger_entries(case_id, payment_request_id)
    
    # Reverse escrow
    escrow_result = await escrow_vault_service.reverse_escrow(case_id)
    
    return {
        "success": ledger_result.get("success", False) and escrow_result,
        "ledger_reversed": ledger_result.get("reversed_count", 0),
        "escrow_reversed": escrow_result,
        "message": "Payment reversed successfully" if (ledger_result.get("success") and escrow_result) else "Failed to reverse payment"
    }
