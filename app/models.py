"""
Database models for WhatsApp Conveyancing Bot
Pydantic models for MongoDB documents
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class ServiceType(str, Enum):
    """Available conveyancing service types"""
    DEED_OF_TRANSFER = "Deed of Transfer"
    DEEDS_OFFICE_SEARCH = "Deeds Office Search"
    CERTIFICATE_OF_REGISTERED_TITLE = "Certificate of Registered Title (CRT)"
    DEED_OF_PARTITION = "Deed of Partition"
    DEED_OF_EXCHANGE = "Deed of Exchange"
    DEED_OF_RECTIFICATION = "Deed of Rectification"
    DEED_OF_GRANT = "Deed of Grant"


class ConversationState(str, Enum):
    """Conversation flow states"""
    GREETING = "GREETING"
    AWAITING_SERVICE_SELECTION = "AWAITING_SERVICE_SELECTION"
    AWAITING_FIRM_SELECTION = "AWAITING_FIRM_SELECTION"
    AWAITING_PAYMENT_METHOD = "AWAITING_PAYMENT_METHOD"
    AWAITING_PAYMENT_DETAILS = "AWAITING_PAYMENT_DETAILS"
    AWAITING_DOCUMENT_UPLOAD = "AWAITING_DOCUMENT_UPLOAD"
    AWAITING_OCR_CONFIRMATION = "AWAITING_OCR_CONFIRMATION"
    AWAITING_TEXT_INPUT = "AWAITING_TEXT_INPUT"
    COMPLETED = "COMPLETED"


class PaymentStatus(str, Enum):
    """Payment status types"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


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


# MongoDB Document Models
class SessionModel(BaseModel):
    """User session document"""
    phone_number: str = Field(..., alias="_id")
    active_application_id: Optional[str] = None
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
    """Property conveyancing application document"""
    owner_phone: str
    service_type: ServiceType
    extracted_profile: Optional[ExtractedProfile] = None
    documents: DocumentUrls = Field(default_factory=DocumentUrls)
    selected_conveyancer: Optional[SelectedConveyancer] = None
    payment: PaymentInfo = Field(default_factory=PaymentInfo)
    verification: VerificationInfo = Field(default_factory=VerificationInfo)
    
    # Document upload tracking
    current_document_index: int = 0
    document_sequence: List[str] = Field(default_factory=list)
    uploaded_documents: List[str] = Field(default_factory=list)
    conditional_documents: Dict[str, bool] = Field(default_factory=dict)
    
    # Additional metadata
    text_inputs: Dict[str, str] = Field(default_factory=dict)
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