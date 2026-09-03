"""
State machine for WhatsApp conversation flow
Manages conversation states and transitions
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.models import (
    ConversationState, ServiceType, ApplicationModel, SessionModel,
    ExtractedProfile, PaymentMethod, PaymentStatus, VerificationStatus
)
from app.database import get_database
from app.whatsapp_service import send_message
from app.document_sequences import get_document_sequence
from app.conditional_logic import evaluate_conditional_documents

logger = logging.getLogger(__name__)


async def process_message(message: Dict[str, Any], metadata: Dict[str, Any]):
    """
    Process incoming WhatsApp message through state machine
    """
    try:
        # Extract message data
        phone_number = message.get("from")
        message_type = message.get("type")
        content = message.get(message_type, {})
        
        logger.info(f"Processing message from {phone_number}: {message_type}")
        
        # Get or create user session
        session = await get_or_create_session(phone_number)
        
        # Process based on current state
        response = await handle_state_transition(session, message_type, content, metadata)
        
        # Send response
        if response:
            await send_message(phone_number, response)
        
        # Update session
        await update_session(phone_number, session)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Send error message to user
        await send_message(phone_number, "Sorry, I encountered an error. Please try again.")


async def get_or_create_session(phone_number: str) -> SessionModel:
    """
    Get existing session or create new one
    """
    database = get_database()
    session_data = await database.sessions.find_one({"_id": phone_number})
    
    if session_data:
        return SessionModel(**session_data)
    else:
        # Create new session
        new_session = SessionModel(
            phone_number=phone_number,
            current_step=ConversationState.GREETING
        )
        await database.sessions.insert_one(new_session.model_dump(by_alias=True))
        return new_session


async def update_session(phone_number: str, session: SessionModel):
    """
    Update session in database
    """
    database = get_database()
    session.updated_at = datetime.utcnow()
    await database.sessions.update_one(
        {"_id": phone_number},
        {"$set": session.model_dump(by_alias=True, exclude={"_id"})}
    )


async def handle_state_transition(
    session: SessionModel,
    message_type: str,
    content: Dict[str, Any],
    metadata: Dict[str, Any]
) -> str:
    """
    Handle state transition based on current step and message
    """
    current_state = session.current_step
    
    # Handle command messages (like "back", "menu", etc.)
    if message_type == "text":
        text_content = content.get("body", "").lower().strip()
        
        if text_content in ["menu", "start", "restart"]:
            session.current_step = ConversationState.GREETING
            return get_greeting_message()
        
        if text_content == "back":
            return await handle_back_navigation(session)
        
        if text_content == "status":
            return await handle_status_check(session)
    
    # State-specific handling
    if current_state == ConversationState.GREETING:
        return await handle_greeting(session, message_type, content)
    
    elif current_state == ConversationState.AWAITING_SERVICE_SELECTION:
        return await handle_service_selection(session, message_type, content)
    
    elif current_state == ConversationState.AWAITING_FIRM_SELECTION:
        return await handle_firm_selection(session, message_type, content)
    
    elif current_state == ConversationState.AWAITING_PAYMENT_METHOD:
        return await handle_payment_method_selection(session, message_type, content)
    
    elif current_state == ConversationState.AWAITING_PAYMENT_DETAILS:
        return await handle_payment_details(session, message_type, content)
    
    elif current_state == ConversationState.AWAITING_DOCUMENT_UPLOAD:
        return await handle_document_upload(session, message_type, content, metadata)
    
    elif current_state == ConversationState.AWAITING_OCR_CONFIRMATION:
        return await handle_ocr_confirmation(session, message_type, content)
    
    elif current_state == ConversationState.AWAITING_TEXT_INPUT:
        return await handle_text_input(session, message_type, content)
    
    elif current_state == ConversationState.COMPLETED:
        return await handle_completed_state(session, message_type, content)
    
    else:
        return "I'm not sure what you need. Type 'menu' to see available options."


async def handle_greeting(session: SessionModel, message_type: str, content: Dict[str, Any]) -> str:
    """
    Handle greeting state - show main menu
    """
    session.current_step = ConversationState.AWAITING_SERVICE_SELECTION
    
    return get_service_selection_message()


async def handle_service_selection(session: SessionModel, message_type: str, content: Dict[str, Any]) -> str:
    """
    Handle service selection
    """
    if message_type != "text":
        return "Please select a service by typing the number or name."
    
    selection = content.get("body", "").strip()
    
    # Map selection to service type
    service_type = map_selection_to_service(selection)
    
    if not service_type:
        return "Invalid selection. Please choose a number from 1-7 or type the service name."
    
    # Create new application
    application = await create_application(session.phone_number, service_type)
    session.active_application_id = str(application.inserted_id)
    
    # Set document sequence
    await set_application_document_sequence(session.active_application_id, service_type)
    
    # Move to next step
    session.current_step = ConversationState.AWAITING_DOCUMENT_UPLOAD
    
    return get_requirements_message(service_type) + "\n\n" + get_document_upload_prompt(service_type, 0)


async def handle_firm_selection(session: SessionModel, message_type: str, content: Dict[str, Any]) -> str:
    """
    Handle law firm selection with pagination
    """
    if message_type != "text":
        return "Please select a firm by typing the number or 'next' for more options."
    
    selection = content.get("body", "").strip().lower()
    
    if selection == "next":
        # Handle pagination
        return await get_paginated_firms(session, 1)  # Next page
    elif selection == "prev":
        # Handle pagination
        return await get_paginated_firms(session, -1)  # Previous page
    else:
        # Handle firm selection
        return await process_firm_selection(session, selection)


async def handle_payment_method_selection(session: SessionModel, message_type: str, content: Dict[str, Any]) -> str:
    """
    Handle payment method selection
    """
    if message_type != "text":
        return "Please select a payment method by typing the number."
    
    selection = content.get("body", "").strip().lower()
    
    payment_method = map_selection_to_payment_method(selection)
    
    if not payment_method:
        return "Invalid selection. Please choose 1 for EcoCash, 2 for InnBucks, or 3 for OneMoney."
    
    # Store payment method in application
    await update_application_payment_method(session.active_application_id, payment_method)
    
    session.current_step = ConversationState.AWAITING_PAYMENT_DETAILS
    
    return get_payment_details_prompt(payment_method)


async def handle_payment_details(session: SessionModel, message_type: str, content: Dict[str, Any]) -> str:
    """
    Handle payment details input
    """
    if message_type != "text":
        return "Please provide your payment details (phone number or wallet ID)."
    
    payment_details = content.get("body", "").strip()
    
    # Process payment
    payment_result = await process_payment(session.active_application_id, payment_details)
    
    if payment_result["success"]:
        session.current_step = ConversationState.COMPLETED
        return f"Payment successful! Your application has been submitted.\n\n{get_completion_message(session.active_application_id)}"
    else:
        return f"Payment failed: {payment_result['error']}. Please try again or type 'back' to select a different payment method."


async def handle_document_upload(
    session: SessionModel,
    message_type: str,
    content: Dict[str, Any],
    metadata: Dict[str, Any]
) -> str:
    """
    Handle document upload with OCR processing
    """
    application = await get_application(session.active_application_id)
    
    if not application:
        return "Application not found. Please start over."
    
    # Check if current document requires OCR
    current_doc = application.document_sequence[application.current_document_index]
    
    if current_doc.endswith("_id") and message_type in ["image", "document"]:
        # Process with OCR
        return await process_document_with_ocr(session, message_type, content, metadata, current_doc)
    elif message_type == "text":
        # Handle text input for non-ID documents
        return await process_text_document(session, content.get("body", ""), current_doc)
    else:
        # Handle regular document upload
        return await process_regular_document(session, message_type, content, metadata, current_doc)


async def handle_ocr_confirmation(session: SessionModel, message_type: str, content: Dict[str, Any]) -> str:
    """
    Handle OCR data confirmation
    """
    if message_type != "text":
        return "Please type 'confirm' to accept the extracted data or 'retry' to upload again."
    
    response = content.get("body", "").strip().lower()
    
    if response == "confirm":
        # Store confirmed OCR data
        await confirm_ocr_data(session.active_application_id)
        
        # Move to next document
        await advance_to_next_document(session)
        
        return "Data confirmed. " + await get_next_document_prompt(session)
    
    elif response == "retry":
        # Allow re-upload
        session.current_step = ConversationState.AWAITING_DOCUMENT_UPLOAD
        return "Please upload the document again."
    
    else:
        return "Please type 'confirm' to accept the data or 'retry' to upload again."


async def handle_text_input(session: SessionModel, message_type: str, content: Dict[str, Any]) -> str:
    """
    Handle text input fields
    """
    if message_type != "text":
        return "Please provide the requested information as text."
    
    text_input = content.get("body", "").strip()
    
    # Store text input
    await store_text_input(session.active_application_id, text_input)
    
    # Move to next document
    await advance_to_next_document(session)
    
    return "Information received. " + await get_next_document_prompt(session)


async def handle_completed_state(session: SessionModel, message_type: str, content: Dict[str, Any]) -> str:
    """
    Handle completed state - show application status
    """
    return await handle_status_check(session)


async def handle_back_navigation(session: SessionModel) -> str:
    """
    Handle back navigation
    """
    # Implement back navigation logic based on current state
    # This would revert to the previous step in the flow
    return "Back navigation not yet implemented. Type 'menu' to restart."


async def handle_status_check(session: SessionModel) -> str:
    """
    Handle status check command
    """
    if not session.active_application_id:
        return "You don't have an active application. Type 'menu' to start a new application."
    
    application = await get_application(session.active_application_id)
    
    if not application:
        return "Application not found. Type 'menu' to start a new application."
    
    return get_application_status_message(application)


# Helper functions

def get_greeting_message() -> str:
    """Get initial greeting message"""
    return ("🏠 Welcome to the Zimbabwe Property Conveyancing Bot!\n\n"
            "I can help you with:\n"
            "1. Deed of Transfer\n"
            "2. Deeds Office Search\n"
            "3. Certificate of Registered Title (CRT)\n"
            "4. Deed of Partition\n"
            "5. Deed of Exchange\n"
            "6. Deed of Rectification\n"
            "7. Deed of Grant\n\n"
            "Please select a service by typing the number or name.")


def get_service_selection_message() -> str:
    """Get service selection message"""
    return get_greeting_message()


def get_requirements_message(service_type: ServiceType) -> str:
    """Get requirements message for selected service"""
    requirements = {
        ServiceType.DEED_OF_TRANSFER: "For Deed of Transfer, you'll need:\n"
                                       "• Seller & Buyer IDs\n"
                                       "• Original Title Deed\n"
                                       "• Agreement of Sale\n"
                                       "• Power of Attorney\n"
                                       "• Declarations\n"
                                       "• CGT Clearance\n"
                                       "• Rates Clearance\n"
                                       "• Levy Clearance (if applicable)\n"
                                       "• Marital Status Proof",
        
        ServiceType.DEEDS_OFFICE_SEARCH: "For Deeds Office Search, you'll need:\n"
                                         "• Property Description\n"
                                         "• Your ID\n"
                                         "• Prior Deed Number (optional)",
        
        ServiceType.CERTIFICATE_OF_REGISTERED_TITLE: "For Certificate of Registered Title, you'll need:\n"
                                                     "• Owner ID\n"
                                                     "• Parent Title Deed\n"
                                                     "• Subdivision Permit\n"
                                                     "• Surveyor General Diagram\n"
                                                     "• Certificate of Compliance\n"
                                                     "• Section 40 Form",
        
        ServiceType.DEED_OF_PARTITION: "For Deed of Partition, you'll need:\n"
                                       "• All Joint Owners' IDs\n"
                                       "• Joint Title Deed\n"
                                       "• Partition Agreement\n"
                                       "• Subdivision Permit & SG Diagrams\n"
                                       "• CGT Assessment/Clearance\n"
                                       "• Rates Clearance",
        
        ServiceType.DEED_OF_EXCHANGE: "For Deed of Exchange, you'll need:\n"
                                      "• Both Owners' IDs\n"
                                      "• Both Title Deeds\n"
                                      "• Exchange Agreement\n"
                                      "• Two CGT Clearances\n"
                                      "• Two Rates Clearances",
        
        ServiceType.DEED_OF_RECTIFICATION: "For Deed of Rectification, you'll need:\n"
                                           "• Owner ID\n"
                                           "• Erroneous Title Deed\n"
                                           "• Affidavit\n"
                                           "• Corrected SG Diagram (if applicable)\n"
                                           "• Rectification Form",
        
        ServiceType.DEED_OF_GRANT: "For Deed of Grant, you'll need:\n"
                                   "• Grantee ID\n"
                                   "• Allocation/Offer Letter\n"
                                   "• Surveyor General Diagram\n"
                                   "• Ministry Clearance/Payment Proof\n"
                                   "• Draft Deed of Grant"
    }
    
    return requirements.get(service_type, "Requirements information not available.")


def get_document_upload_prompt(service_type: ServiceType, document_index: int) -> str:
    """Get prompt for next document upload"""
    return f"Please upload the first document for {service_type}."


def get_application_status_message(application: ApplicationModel) -> str:
    """Get application status message"""
    status_messages = {
        VerificationStatus.AWAITING_REVIEW: "Your application is awaiting review.",
        VerificationStatus.UNDER_REVIEW: "Your application is under review.",
        VerificationStatus.APPROVED: "Your application has been approved!",
        VerificationStatus.REJECTED: f"Your application was rejected. Reason: {application.verification.rejection_reason}",
        VerificationStatus.RESUBMISSION_REQUIRED: "Your application requires resubmission."
    }
    
    return (f"Application Status: {application.verification.status}\n"
            f"Service: {application.service_type}\n"
            f"Payment Status: {application.payment.status}\n"
            f"{status_messages.get(application.verification.status, '')}")


def get_completion_message(application_id: str) -> str:
    """Get completion message"""
    return (f"Your application ID: {application_id}\n"
            "You will receive a WhatsApp message when your application is reviewed.\n"
            "Type 'status' to check your application status at any time.")


# Placeholder functions to be implemented in other modules
async def create_application(phone_number: str, service_type: ServiceType):
    """Create new application"""
    database = get_database()
    application = ApplicationModel(
        owner_phone=phone_number,
        service_type=service_type
    )
    result = await database.applications.insert_one(application.model_dump(by_alias=True))
    return result


async def set_application_document_sequence(application_id: str, service_type: ServiceType):
    """Set document sequence for application"""
    database = get_database()
    document_sequence = get_document_sequence(service_type)
    await database.applications.update_one(
        {"_id": application_id},
        {"$set": {"document_sequence": document_sequence}}
    )


async def get_application(application_id: str) -> Optional[ApplicationModel]:
    """Get application by ID"""
    database = get_database()
    application_data = await database.applications.find_one({"_id": application_id})
    if application_data:
        return ApplicationModel(**application_data)
    return None


async def update_application_payment_method(application_id: str, payment_method: PaymentMethod):
    """Update application payment method"""
    database = get_database()
    await database.applications.update_one(
        {"_id": application_id},
        {"$set": {"payment.method": payment_method}}
    )


async def process_payment(application_id: str, payment_details: str) -> Dict[str, Any]:
    """Process payment (placeholder)"""
    # This will be implemented in payment_service.py
    return {"success": False, "error": "Payment processing not yet implemented"}


async def process_document_with_ocr(session, message_type, content, metadata, current_doc):
    """Process document with OCR (placeholder)"""
    # This will be implemented with OCR service
    return "OCR processing not yet implemented."


async def process_regular_document(session, message_type, content, metadata, current_doc):
    """Process regular document upload (placeholder)"""
    # This will be implemented with file service
    return "Document upload not yet implemented."


async def process_text_document(session, text_content, current_doc):
    """Process text document input (placeholder)"""
    # This will be implemented
    return "Text document processing not yet implemented."


async def confirm_ocr_data(application_id: str):
    """Confirm OCR data (placeholder)"""
    # This will be implemented
    pass


async def advance_to_next_document(session: SessionModel):
    """Advance to next document in sequence (placeholder)"""
    # This will be implemented
    pass


async def get_next_document_prompt(session: SessionModel) -> str:
    """Get prompt for next document (placeholder)"""
    # This will be implemented
    return "Next document prompt not yet implemented."


async def store_text_input(application_id: str, text_input: str):
    """Store text input (placeholder)"""
    # This will be implemented
    pass


async def get_paginated_firms(session: SessionModel, page_change: int) -> str:
    """Get paginated firms (placeholder)"""
    # This will be implemented
    return "Firm pagination not yet implemented."


async def process_firm_selection(session: SessionModel, selection: str) -> str:
    """Process firm selection (placeholder)"""
    # This will be implemented
    return "Firm selection not yet implemented."


def map_selection_to_service(selection: str) -> Optional[ServiceType]:
    """Map user selection to service type"""
    service_map = {
        "1": ServiceType.DEED_OF_TRANSFER,
        "deed of transfer": ServiceType.DEED_OF_TRANSFER,
        "transfer": ServiceType.DEED_OF_TRANSFER,
        
        "2": ServiceType.DEEDS_OFFICE_SEARCH,
        "deeds office search": ServiceType.DEEDS_OFFICE_SEARCH,
        "search": ServiceType.DEEDS_OFFICE_SEARCH,
        
        "3": ServiceType.CERTIFICATE_OF_REGISTERED_TITLE,
        "certificate of registered title": ServiceType.CERTIFICATE_OF_REGISTERED_TITLE,
        "crt": ServiceType.CERTIFICATE_OF_REGISTERED_TITLE,
        "registered title": ServiceType.CERTIFICATE_OF_REGISTERED_TITLE,
        
        "4": ServiceType.DEED_OF_PARTITION,
        "deed of partition": ServiceType.DEED_OF_PARTITION,
        "partition": ServiceType.DEED_OF_PARTITION,
        
        "5": ServiceType.DEED_OF_EXCHANGE,
        "deed of exchange": ServiceType.DEED_OF_EXCHANGE,
        "exchange": ServiceType.DEED_OF_EXCHANGE,
        
        "6": ServiceType.DEED_OF_RECTIFICATION,
        "deed of rectification": ServiceType.DEED_OF_RECTIFICATION,
        "rectification": ServiceType.DEED_OF_RECTIFICATION,
        
        "7": ServiceType.DEED_OF_GRANT,
        "deed of grant": ServiceType.DEED_OF_GRANT,
        "grant": ServiceType.DEED_OF_GRANT
    }
    
    return service_map.get(selection.lower())


def map_selection_to_payment_method(selection: str) -> Optional[PaymentMethod]:
    """Map user selection to payment method"""
    payment_map = {
        "1": PaymentMethod.ECOCASH,
        "ecocash": PaymentMethod.ECOCASH,
        
        "2": PaymentMethod.INNBUCKS,
        "innbucks": PaymentMethod.INNBUCKS,
        
        "3": PaymentMethod.ONEMONEY,
        "onemoney": PaymentMethod.ONEMONEY
    }
    
    return payment_map.get(selection.lower())


def get_payment_details_prompt(payment_method: PaymentMethod) -> str:
    """Get payment details prompt"""
    prompts = {
        PaymentMethod.ECOCASH: "Please provide your EcoCash phone number (format: 2637XXXXXXXXX)",
        PaymentMethod.INNBUCKS: "Please provide your InnBucks wallet ID",
        PaymentMethod.ONEMONEY: "Please provide your OneMoney phone number"
    }
    
    return prompts.get(payment_method, "Please provide your payment details.")