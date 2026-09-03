"""
Document sequences for each conveyancing service type
Defines the order and requirements for document uploads per service
"""
from typing import List, Dict, Any
from app.models import ServiceType


class DocumentSequences:
    """Defines document upload sequences for each service type"""
    
    @staticmethod
    def get_sequence(service_type: ServiceType) -> List[str]:
        """
        Get document upload sequence for a service type
        
        Args:
            service_type: The type of conveyancing service
            
        Returns:
            List of document identifiers in upload order
        """
        sequences = {
            ServiceType.DEED_OF_TRANSFER: DocumentSequences._deed_of_transfer(),
            ServiceType.DEEDS_OFFICE_SEARCH: DocumentSequences._deeds_office_search(),
            ServiceType.CERTIFICATE_OF_REGISTERED_TITLE: DocumentSequences._certificate_of_registered_title(),
            ServiceType.DEED_OF_PARTITION: DocumentSequences._deed_of_partition(),
            ServiceType.DEED_OF_EXCHANGE: DocumentSequences._deed_of_exchange(),
            ServiceType.DEED_OF_RECTIFICATION: DocumentSequences._deed_of_rectification(),
            ServiceType.DEED_OF_GRANT: DocumentSequences._deed_of_grant()
        }
        
        return sequences.get(service_type, [])
    
    @staticmethod
    def get_document_info(document_id: str) -> Dict[str, Any]:
        """
        Get information about a specific document type
        
        Args:
            document_id: Document identifier
            
        Returns:
            Dictionary with document information
        """
        document_info = {
            # ID Documents (OCR processed)
            "seller_id": {
                "name": "Seller's ID Document",
                "description": "National ID or passport of the property seller",
                "type": "id_document",
                "ocr_required": True,
                "formats": ["jpg", "jpeg", "png", "pdf"]
            },
            "buyer_id": {
                "name": "Buyer's ID Document",
                "description": "National ID or passport of the property buyer",
                "type": "id_document",
                "ocr_required": True,
                "formats": ["jpg", "jpeg", "png", "pdf"]
            },
            "owner_id": {
                "name": "Owner's ID Document",
                "description": "National ID or passport of the property owner",
                "type": "id_document",
                "ocr_required": True,
                "formats": ["jpg", "jpeg", "png", "pdf"]
            },
            "grantee_id": {
                "name": "Grantee's ID Document",
                "description": "National ID or passport of the grantee/beneficiary",
                "type": "id_document",
                "ocr_required": True,
                "formats": ["jpg", "jpeg", "png", "pdf"]
            },
            "joint_owner_ids": {
                "name": "Joint Owners' ID Documents",
                "description": "National IDs or passports of all joint property owners",
                "type": "id_document",
                "ocr_required": True,
                "multiple": True,
                "formats": ["jpg", "jpeg", "png", "pdf"]
            },
            "owner_a_id": {
                "name": "Owner A's ID Document",
                "description": "National ID or passport of the first property owner",
                "type": "id_document",
                "ocr_required": True,
                "formats": ["jpg", "jpeg", "png", "pdf"]
            },
            "owner_b_id": {
                "name": "Owner B's ID Document",
                "description": "National ID or passport of the second property owner",
                "type": "id_document",
                "ocr_required": True,
                "formats": ["jpg", "jpeg", "png", "pdf"]
            },
            
            # Title Deeds
            "title_deed": {
                "name": "Title Deed",
                "description": "Original or varied title deed document",
                "type": "title_deed",
                "ocr_required": False,
                "formats": ["pdf"]  # PDF only for title deeds
            },
            "parent_title_deed": {
                "name": "Parent Title Deed",
                "description": "Original parent title deed for subdivision",
                "type": "title_deed",
                "ocr_required": False,
                "formats": ["pdf"]
            },
            "joint_title_deed": {
                "name": "Joint Title Deed",
                "description": "Original title deed for jointly owned property",
                "type": "title_deed",
                "ocr_required": False,
                "formats": ["pdf"]
            },
            "title_deed_a": {
                "name": "Title Deed A",
                "description": "Title deed for the first property",
                "type": "title_deed",
                "ocr_required": False,
                "formats": ["pdf"]
            },
            "title_deed_b": {
                "name": "Title Deed B",
                "description": "Title deed for the second property",
                "type": "title_deed",
                "ocr_required": False,
                "formats": ["pdf"]
            },
            "erroneous_title_deed": {
                "name": "Erroneous Title Deed",
                "description": "Original title deed containing errors to be rectified",
                "type": "title_deed",
                "ocr_required": False,
                "formats": ["pdf"]
            },
            
            # Legal Documents
            "agreement_of_sale": {
                "name": "Agreement of Sale",
                "description": "Signed agreement of sale between buyer and seller",
                "type": "legal_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "power_of_attorney": {
                "name": "Power of Attorney",
                "description": "Conveyancer's power of attorney to pass transfer",
                "type": "legal_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "declarations": {
                "name": "Declarations",
                "description": "Signed declarations by seller and purchaser",
                "type": "legal_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "partition_agreement": {
                "name": "Partition Agreement",
                "description": "Formal partition agreement signed by all parties",
                "type": "legal_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "exchange_agreement": {
                "name": "Exchange Agreement",
                "description": "Formal exchange agreement between property owners",
                "type": "legal_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "affidavit": {
                "name": "Affidavit",
                "description": "Conveyancer's or owner's affidavit detailing the error",
                "type": "legal_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            
            # Government Certificates
            "cgt_clearance": {
                "name": "Capital Gains Tax Clearance",
                "description": "ZIMRA CGT clearance certificate",
                "type": "government_certificate",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "cgt_clearance_a": {
                "name": "CGT Clearance A",
                "description": "ZIMRA CGT clearance certificate for first property",
                "type": "government_certificate",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "cgt_clearance_b": {
                "name": "CGT Clearance B",
                "description": "ZIMRA CGT clearance certificate for second property",
                "type": "government_certificate",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "cgt_assessment": {
                "name": "CGT Assessment/Clearance",
                "description": "ZIMRA CGT assessment or exemption certificate",
                "type": "government_certificate",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "rates_clearance": {
                "name": "Rates Clearance Certificate",
                "description": "Municipal rates clearance certificate",
                "type": "government_certificate",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "rates_clearance_a": {
                "name": "Rates Clearance A",
                "description": "Municipal rates clearance for first property",
                "type": "government_certificate",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "rates_clearance_b": {
                "name": "Rates Clearance B",
                "description": "Municipal rates clearance for second property",
                "type": "government_certificate",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "levy_clearance": {
                "name": "Levy Clearance Certificate",
                "description": "Levy clearance certificate (for sectional title only)",
                "type": "government_certificate",
                "ocr_required": False,
                "conditional": True,
                "condition": "sectional_title",
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            
            # Planning Documents
            "subdivision_permit": {
                "name": "Subdivision Permit",
                "description": "Approved subdivision permit from town planning",
                "type": "planning_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "surveyor_general_diagram": {
                "name": "Surveyor General Diagram",
                "description": "Approved Surveyor General diagram",
                "type": "technical_drawing",
                "ocr_required": False,
                "formats": ["pdf"]  # PDF required for technical drawings
            },
            "sg_diagrams": {
                "name": "Surveyor General Diagrams",
                "description": "Approved SG diagrams for each portion",
                "type": "technical_drawing",
                "ocr_required": False,
                "multiple": True,
                "formats": ["pdf"]
            },
            "corrected_sg_diagram": {
                "name": "Corrected Surveyor General Diagram",
                "description": "Corrected SG diagram (if rectification is spatial)",
                "type": "technical_drawing",
                "ocr_required": False,
                "conditional": True,
                "condition": "spatial_rectification",
                "formats": ["pdf"]
            },
            
            # Compliance Documents
            "certificate_of_compliance": {
                "name": "Certificate of Compliance",
                "description": "Local authority certificate of compliance",
                "type": "compliance_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "section40_form": {
                "name": "Section 40 Application Form",
                "description": "Formal Section 40 application form",
                "type": "compliance_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "rectification_form": {
                "name": "Rectification Application Form",
                "description": "Deeds Registry form of application for rectification",
                "type": "compliance_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            
            # Personal Documents
            "marital_status_proof": {
                "name": "Marital Status Proof",
                "description": "Marriage certificate or single affidavit",
                "type": "personal_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            
            # State Land Documents
            "allocation_letter": {
                "name": "Allocation/Offer Letter",
                "description": "Official ministry allocation or offer letter",
                "type": "government_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "ministry_clearance": {
                "name": "Ministry Clearance/Payment Proof",
                "description": "Ministry clearance or proof of full purchase price to state",
                "type": "government_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            "draft_deed_of_grant": {
                "name": "Draft Deed of Grant",
                "description": "Draft deed of grant prepared for ministry signature",
                "type": "legal_document",
                "ocr_required": False,
                "formats": ["pdf", "jpg", "jpeg", "png"]
            },
            
            # Text Inputs (for Deeds Office Search)
            "property_description": {
                "name": "Property Description",
                "description": "Stand number, township/suburb, and district",
                "type": "text_input",
                "ocr_required": False,
                "input_required": True
            },
            "prior_deed_number": {
                "name": "Prior Deed Number",
                "description": "Prior deed number (if known)",
                "type": "text_input",
                "ocr_required": False,
                "input_required": False,
                "optional": True
            }
        }
        
        return document_info.get(document_id, {})
    
    # Service-specific document sequences
    @staticmethod
    def _deed_of_transfer() -> List[str]:
        """Document sequence for Deed of Transfer"""
        return [
            "seller_id",
            "buyer_id",
            "title_deed",
            "agreement_of_sale",
            "power_of_attorney",
            "declarations",
            "cgt_clearance",
            "rates_clearance",
            "levy_clearance",  # Conditional based on property type
            "marital_status_proof"
        ]
    
    @staticmethod
    def _deeds_office_search() -> List[str]:
        """Document sequence for Deeds Office Search (text inputs)"""
        return [
            "property_description",
            "owner_id",
            "prior_deed_number"  # Optional
        ]
    
    @staticmethod
    def _certificate_of_registered_title() -> List[str]:
        """Document sequence for Certificate of Registered Title (CRT)"""
        return [
            "owner_id",
            "parent_title_deed",
            "subdivision_permit",
            "surveyor_general_diagram",
            "certificate_of_compliance",
            "section40_form"
        ]
    
    @staticmethod
    def _deed_of_partition() -> List[str]:
        """Document sequence for Deed of Partition"""
        return [
            "joint_owner_ids",  # Multiple IDs
            "joint_title_deed",
            "partition_agreement",
            "subdivision_permit",
            "sg_diagrams",  # Multiple diagrams
            "cgt_assessment",
            "rates_clearance"
        ]
    
    @staticmethod
    def _deed_of_exchange() -> List[str]:
        """Document sequence for Deed of Exchange"""
        return [
            "owner_a_id",
            "owner_b_id",
            "title_deed_a",
            "title_deed_b",
            "exchange_agreement",
            "cgt_clearance_a",
            "cgt_clearance_b",
            "rates_clearance_a",
            "rates_clearance_b"
        ]
    
    @staticmethod
    def _deed_of_rectification() -> List[str]:
        """Document sequence for Deed of Rectification"""
        return [
            "owner_id",
            "erroneous_title_deed",
            "affidavit",
            "corrected_sg_diagram",  # Conditional based on spatial rectification
            "rectification_form"
        ]
    
    @staticmethod
    def _deed_of_grant() -> List[str]:
        """Document sequence for Deed of Grant"""
        return [
            "grantee_id",
            "allocation_letter",
            "surveyor_general_diagram",
            "ministry_clearance",
            "draft_deed_of_grant"
        ]


def get_document_sequence(service_type: ServiceType) -> List[str]:
    """
    Convenience function to get document sequence for a service type
    """
    return DocumentSequences.get_sequence(service_type)


def get_document_requirements(document_id: str) -> Dict[str, Any]:
    """
    Convenience function to get document requirements
    """
    return DocumentSequences.get_document_info(document_id)


def get_next_document(
    service_type: ServiceType,
    current_index: int,
    uploaded_documents: List[str],
    conditional_docs: Dict[str, bool]
) -> str:
    """
    Get the next document to upload based on current progress
    
    Args:
        service_type: Service type
        current_index: Current document index
        uploaded_documents: List of already uploaded document IDs
        conditional_docs: Dictionary of conditional document decisions
        
    Returns:
        Next document ID to upload, or empty string if complete
    """
    sequence = get_document_sequence(service_type)
    
    # Find next document that hasn't been uploaded
    for i in range(current_index, len(sequence)):
        doc_id = sequence[i]
        
        # Skip if already uploaded
        if doc_id in uploaded_documents:
            continue
        
        # Check conditional requirements
        doc_info = get_document_requirements(doc_id)
        if doc_info.get("conditional"):
            condition = doc_info.get("condition")
            if not conditional_docs.get(condition, False):
                continue  # Skip this conditional document
        
        return doc_id
    
    return ""  # All documents uploaded