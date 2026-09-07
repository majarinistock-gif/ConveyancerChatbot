"""
Database models for WhatsApp Conveyancing Bot
Pydantic models for MongoDB documents
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class ServiceType(str, Enum):
    """Available legal service types across all categories"""
    
    # Conveyancing & Property Functions
    DEED_OF_TRANSFER = "Deed of Transfer"
    DEEDS_OFFICE_SEARCH = "Deeds Office Search"
    CERTIFICATE_OF_REGISTERED_TITLE = "Certificate of Registered Title (CRT)"
    DEED_OF_PARTITION = "Deed of Partition"
    DEED_OF_EXCHANGE = "Deed of Exchange"
    DEED_OF_RECTIFICATION = "Deed of Rectification"
    DEED_OF_GRANT = "Deed of Grant"
    SECURITIES_REGISTRATION = "Securities Registration (Mortgage/Notarial Bond)"
    PROPERTY_DUE_DILIGENCE = "Property Due Diligence"
    
    # Advisory & Consultative Functions
    LEGAL_OPINION = "Legal Opinion Provision"
    REGULATORY_COMPLIANCE = "Regulatory Compliance Advice"
    RISK_ASSESSMENT = "Risk Assessment"
    
    # Representative & Advocacy Functions (Litigation)
    CIVIL_REPRESENTATION = "Civil Representation"
    CRIMINAL_DEFENCE = "Criminal Defence"
    ADMINISTRATIVE_ADVOCACY = "Administrative Advocacy"
    
    # Notarial & Transactional Functions
    DOCUMENT_AUTHENTICATION = "Document Authentication (Notary Public)"
    ANTENUPTIAL_CONTRACT = "Antenuptial Contract (ANC)"
    PROTESTS = "Protests (Bills of Exchange)"
    
    # Document Drafting & Commercial Functions
    COMMERCIAL_AGREEMENTS = "Commercial Agreements Drafting"
    ESTATE_PLANNING = "Estate Planning (Will & Testament)"
    ESTATE_ADMINISTRATION = "Estate Administration"
    
    # Alternative Dispute Resolution (ADR)
    NEGOTIATION = "Negotiation Support"
    MEDIATION_ARBITRATION = "Mediation & Arbitration"


class ConversationState(str, Enum):
    """Conversation flow states"""
    GREETING = "GREETING"
    AWAITING_SERVICE_SELECTION = "AWAITING_SERVICE_SELECTION"
    AWAITING_TERMS_ACCEPTANCE = "AWAITING_TERMS_ACCEPTANCE"
    AWAITING_FIRM_SELECTION = "AWAITING_FIRM_SELECTION"
    AWAITING_PAYMENT_METHOD = "AWAITING_PAYMENT_METHOD"
    AWAITING_PAYMENT_DETAILS = "AWAITING_PAYMENT_DETAILS"
    AWAITING_DOCUMENT_UPLOAD = "AWAITING_DOCUMENT_UPLOAD"
    AWAITING_OCR_CONFIRMATION = "AWAITING_OCR_CONFIRMATION"
    AWAITING_TEXT_INPUT = "AWAITING_TEXT_INPUT"
    AWAITING_CASE_DETAILS = "AWAITING_CASE_DETAILS"
    COMPLETED = "COMPLETED"


class PaymentStatus(str, Enum):
    """Payment status types"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class CaseStatus(str, Enum):
    """Case status types for SLA state machine"""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    WAITING_RESPONSE = "WAITING_RESPONSE"
    COMPLETE = "COMPLETE"
    PRACTITIONER_DEFAULT = "PRACTITIONER_DEFAULT"
    REFUNDED = "REFUNDED"
    CLOSED = "CLOSED"


class SLATimerState(str, Enum):
    """SLA timer state types"""
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    PRACTITIONER_DEFAULT = "PRACTITIONER_DEFAULT"
    REFUND_TRIGGERED = "REFUND_TRIGGERED"


class LedgerAllocationType(str, Enum):
    """Ledger allocation types"""
    SYSTEM_ADMIN_COSTS = "SYSTEM_ADMIN_COSTS"
    ATTENDING_ESCROW_VAULT = "ATTENDING_ESCROW_VAULT"
    REFUND_SETTLEMENT = "REFUND_SETTLEMENT"
    REVERSAL_ADJUSTMENT = "REVERSAL_ADJUSTMENT"


class LedgerDirection(str, Enum):
    """Ledger direction types"""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class LedgerState(str, Enum):
    """Ledger state types"""
    PENDING = "PENDING"
    ALLOCATED = "ALLOCATED"
    RELEASED = "RELEASED"
    REVERSED = "REVERSED"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class EscrowStatus(str, Enum):
    """Escrow vault status types"""
    ALLOCATED = "ALLOCATED"
    HELD = "HELD"
    RELEASED = "RELEASED"
    REVERSED = "REVERSED"
    REFUNDED = "REFUNDED"


class ConflictCheckStatus(str, Enum):
    """Conflict of interest check status"""
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"


class FirmStatus(str, Enum):
    """Law firm status types"""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class PractitionerRole(str, Enum):
    """Practitioner role types"""
    LEGAL_PRACTITIONER = "LEGAL_PRACTITIONER"
    CONVEYANCER = "CONVEYANCER"
    NOTARY = "NOTARY"
    ASSOCIATE = "ASSOCIATE"
    PARTNER = "PARTNER"
    MANAGER = "MANAGER"


class SeatType(str, Enum):
    """Seat type for practitioners"""
    COMPLIMENTARY = "COMPLIMENTARY"
    PAID_EXTRA = "PAID_EXTRA"


class AccessEventType(str, Enum):
    """Access event types for audit trail"""
    VIEW = "VIEW"
    EDIT = "EDIT"
    EXPORT = "EXPORT"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    RESPOND = "RESPOND"
    ASSIGN = "ASSIGN"
    REVOKE = "REVOKE"


class VerificationStatus(str, Enum):
    """Application verification status"""
    AWAITING_REVIEW = "AWAITING_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESUBMISSION_REQUIRED = "RESUBMISSION_REQUIRED"


class PaymentMethod(str, Enum):
    """Available payment methods via Paynow"""
    ECOCASH = "ecocash"
    INNBUCKS = "innbucks"
    ONEMONEY = "onemoney"


# Extracted Profile from OCR
class ExtractedProfile(BaseModel):
    """Profile data extracted from ID document OCR"""
    full_name: Optional[str] = None
    id_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Lloyd Shingai",
                "id_number": "63-201948Z18",
                "gender": "Male",
                "date_of_birth": "1985-11-24"
            }
        }


# Document URLs for Application
class DocumentUrls(BaseModel):
    """Document URLs stored in GridFS"""
    id_document_url: Optional[str] = None
    deeds_document_url: Optional[str] = None
    agreement_of_sale_url: Optional[str] = None
    power_of_attorney_url: Optional[str] = None
    declarations_url: Optional[str] = None
    cgt_clearance_url: Optional[str] = None
    rates_clearance_url: Optional[str] = None
    levy_clearance_url: Optional[str] = None
    marital_status_proof_url: Optional[str] = None
    surveyor_general_diagram_url: Optional[str] = None
    subdivision_permit_url: Optional[str] = None
    certificate_of_compliance_url: Optional[str] = None
    section40_form_url: Optional[str] = None
    partition_agreement_url: Optional[str] = None
    exchange_agreement_url: Optional[str] = None
    affidavit_url: Optional[str] = None
    rectification_form_url: Optional[str] = None
    allocation_letter_url: Optional[str] = None
    draft_deed_of_grant_url: Optional[str] = None
    # New document URLs for additional services
    mortgage_agreement_url: Optional[str] = None
    property_valuation_url: Optional[str] = None
    case_documents_url: Optional[str] = None
    court_papers_url: Optional[str] = None
    evidence_documents_url: Optional[str] = None
    charge_sheet_url: Optional[str] = None
    bail_documents_url: Optional[str] = None
    tribunal_papers_url: Optional[str] = None
    document_to_authenticate_url: Optional[str] = None
    marriage_certificate_url: Optional[str] = None
    property_list_url: Optional[str] = None
    draft_anc_url: Optional[str] = None
    bill_of_exchange_url: Optional[str] = None
    draft_agreement_url: Optional[str] = None
    asset_list_url: Optional[str] = None
    draft_will_url: Optional[str] = None
    death_certificate_url: Optional[str] = None
    will_document_url: Optional[str] = None
    estate_inventory_url: Optional[str] = None
    master_of_high_court_documents_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_document_url": "gridfs://...",
                "deeds_document_url": "gridfs://...",
                "agreement_of_sale_url": None
            }
        }


# Selected Conveyancer for Application
class SelectedConveyancer(BaseModel):
    """Conveyancer selected for the application"""
    company_name: str
    contact_person: str
    email: EmailStr
    phone_number: str
    tin_number: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Muvhami Attorneys",
                "contact_person": "Lloyd Shingai Toendepi",
                "email": "ltoendepi@gmail.com",
                "phone_number": "+263773365742",
                "tin_number": "2001512841"
            }
        }


# Payment Information
class PaymentInfo(BaseModel):
    """Payment information for application"""
    status: PaymentStatus = PaymentStatus.PENDING
    amount: float = 5.00
    currency: str = "USD"
    poll_url: Optional[str] = None
    method: Optional[PaymentMethod] = None
    transaction_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "PENDING",
                "amount": 5.00,
                "currency": "USD",
                "poll_url": "https://paynow.co.zw/...",
                "method": "ecocash"
            }
        }


# Verification Information
class VerificationInfo(BaseModel):
    """Application verification information"""
    status: VerificationStatus = VerificationStatus.AWAITING_REVIEW
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "AWAITING_REVIEW",
                "rejection_reason": None
            }
        }


class SLATimerInfo(BaseModel):
    """SLA timer information for 72-hour rule"""
    state: SLATimerState = SLATimerState.NOT_STARTED
    started_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    acknowledgment_received_at: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "state": "RUNNING",
                "started_at": "2026-09-03T10:00:00.000Z",
                "deadline_at": "2026-09-06T10:00:00.000Z"
            }
        }


# MongoDB Document Models
class SessionModel(BaseModel):
    """User session document"""
    phone_number: str = Field(..., alias="_id")
    active_application_id: Optional[str] = None
    selected_service: Optional[ServiceType] = None
    current_step: ConversationState = ConversationState.GREETING
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "sessions"
        json_schema_extra = {
            "example": {
                "_id": "+263771112222",
                "active_application_id": "507f1f77bcf86cd799439011",
                "current_step": "GREETING",
                "updated_at": "2026-09-03T10:32:00.000Z"
            }
        }


class ConveyancerModel(BaseModel):
    """Conveyancer (law firm) document"""
    company_name: str
    contact_person: str
    email: EmailStr
    phone_number: str
    tin_number: str
    province: str
    
    class Config:
        collection = "conveyancers"
        json_schema_extra = {
            "example": {
                "company_name": "Muvhami Attorneys",
                "contact_person": "Lloyd Shingai Toendepi",
                "email": "ltoendepi@gmail.com",
                "phone_number": "+263773365742",
                "tin_number": "2001512841",
                "province": "Harare"
            }
        }


class ApplicationModel(BaseModel):
    """Property conveyancing application document (Case/Dossier)"""
    owner_phone: str
    service_type: ServiceType
    extracted_profile: Optional[ExtractedProfile] = None
    documents: DocumentUrls = Field(default_factory=DocumentUrls)
    selected_conveyancer: Optional[SelectedConveyancer] = None
    payment: PaymentInfo = Field(default_factory=PaymentInfo)
    verification: VerificationInfo = Field(default_factory=VerificationInfo)
    
    # SLA and case status fields
    case_status: CaseStatus = CaseStatus.NEW
    sla_timer: SLATimerInfo = Field(default_factory=SLATimerInfo)
    conflict_check_status: ConflictCheckStatus = ConflictCheckStatus.NOT_RUN
    future_crime_routing: bool = False
    
    # Paynow integration fields
    paynow_payment_request_id: Optional[str] = None
    paynow_confirmed_at: Optional[datetime] = None
    timer_deadline_at: Optional[datetime] = None
    
    # Document upload tracking
    current_document_index: int = 0
    document_sequence: List[str] = Field(default_factory=list)
    uploaded_documents: List[str] = Field(default_factory=list)
    conditional_documents: Dict[str, bool] = Field(default_factory=dict)
    
    # Additional metadata
    text_inputs: Dict[str, str] = Field(default_factory=dict)
    case_details: Optional[str] = None  # For advisory/consultative services
    terms_accepted: bool = False  # T&Cs acceptance status
    terms_accepted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "applications"
        json_schema_extra = {
            "example": {
                "owner_phone": "+263771112222",
                "service_type": "Deed of Transfer",
                "extracted_profile": {
                    "full_name": "Lloyd Shingai",
                    "id_number": "63-201948Z18",
                    "gender": "Male",
                    "date_of_birth": "1985-11-24"
                },
                "documents": {
                    "id_document_url": "gridfs://...",
                    "deeds_document_url": "gridfs://..."
                },
                "selected_conveyancer": {
                    "company_name": "Muvhami Attorneys",
                    "contact_person": "Lloyd Shingai Toendepi",
                    "email": "ltoendepi@gmail.com",
                    "phone_number": "+263773365742",
                    "tin_number": "2001512841"
                },
                "payment": {
                    "status": "PENDING",
                    "amount": 5.00,
                    "currency": "USD",
                    "method": "ecocash"
                },
                "verification": {
                    "status": "AWAITING_REVIEW",
                    "rejection_reason": None
                },
                "case_status": "NEW",
                "sla_timer": {
                    "state": "NOT_STARTED"
                },
                "conflict_check_status": "NOT_RUN",
                "created_at": "2026-09-03T10:32:00.000Z"
            }
        }


# API Request/Response Models
class WebhookMessage(BaseModel):
    """Incoming WhatsApp webhook message"""
    entry: List[Dict[str, Any]]
    object: str


class SendMessageRequest(BaseModel):
    """Request to send WhatsApp message"""
    phone_number: str
    message: str
    message_type: str = "text"


class ApplicationStatusUpdate(BaseModel):
    """Request to update application verification status"""
    status: VerificationStatus
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    """Application response for API"""
    application_id: str
    owner_phone: str
    service_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    verification_status: str
    case_status: CaseStatus
    sla_deadline: Optional[datetime] = None


# New models for documentation compliance

class LawFirmModel(BaseModel):
    """Law firm document for seat cap management"""
    firm_id: str
    firm_name: str
    lsz_registration_no: str
    status: FirmStatus = FirmStatus.ACTIVE
    seat_cap_complimentary: int = 2
    seat_fee_per_extra: float = 200.00
    billing_currency: str = "USD"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        collection = "law_firms"


class FirmPractitionerModel(BaseModel):
    """Practitioner enrollment in law firm"""
    practitioner_id: str
    firm_id: str
    full_name: str
    role_title: PractitionerRole
    is_active: bool = True
    seat_type: SeatType = SeatType.COMPLIMENTARY
    paid_extra_seat_amount: float = 0.00
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "firm_practitioners"


class PlatformLedgerModel(BaseModel):
    """Platform ledger for payment splits and reversals"""
    ledger_id: str
    case_id: str
    payment_request_id: str
    paynow_transaction_ref: Optional[str] = None
    allocation_type: LedgerAllocationType
    direction: LedgerDirection
    amount_usd: float
    currency: str = "USD"
    state: LedgerState = LedgerState.PENDING
    escrow_recipient_id: Optional[str] = None
    reconciliation_note: Optional[str] = None
    idempotency_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "platform_ledgers"


class EscrowVaultModel(BaseModel):
    """Escrow vault for practitioner payments"""
    escrow_vault_id: str
    firm_id: str
    practitioner_id: Optional[str] = None
    case_id: str
    escrow_amount_usd: float = 0.00
    status: EscrowStatus = EscrowStatus.ALLOCATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "escrow_vaults"


class SLATimerModel(BaseModel):
    """SLA timer for 72-hour rule"""
    timer_id: str
    case_id: str
    state: SLATimerState = SLATimerState.NOT_STARTED
    started_at: Optional[datetime] = None
    deadline_at: datetime
    ended_at: Optional[datetime] = None
    acknowledgment_received_at: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "sla_timers"


class DossierAccessEventModel(BaseModel):
    """Audit trail for dossier access events"""
    event_id: str
    case_id: str
    actor_id: str
    actor_role: str
    event_type: AccessEventType
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    hash_chain_prev: Optional[str] = None
    hash_chain_curr: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        collection = "dossier_access_events"