"""
File validation and storage service
Handles file validation with service-specific rules and MongoDB GridFS storage
"""
import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from app.config import settings
from app.database import get_gridfs_bucket, get_database
from app.models import ServiceType

logger = logging.getLogger(__name__)


class FileValidationService:
    """Service for validating uploaded files"""
    
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        self.allowed_image_formats = settings.allowed_image_formats_list
        self.allowed_document_formats = settings.allowed_document_formats_list
    
    def validate_file(
        self,
        file_url: str,
        document_type: str,
        service_type: ServiceType
    ) -> Dict[str, Any]:
        """
        Validate file based on document type and service requirements
        
        Args:
            file_url: URL of the file to validate
            document_type: Type of document being uploaded
            service_type: Service type for context-specific validation
            
        Returns:
            Dictionary with validation result and error messages
        """
        # This is a placeholder - in production, you'd download and check the file
        # For now, we'll simulate validation based on URL patterns
        
        result = {
            "valid": True,
            "error": None,
            "file_size": None,
            "file_format": None
        }
        
        # Simulate file format detection from URL
        file_format = self._detect_format_from_url(file_url)
        result["file_format"] = file_format
        
        # Check file size (placeholder - would download file in production)
        # result["file_size"] = self._get_file_size(file_url)
        
        # Apply service-specific validation rules
        validation_error = self._apply_service_specific_rules(
            document_type, service_type, file_format
        )
        
        if validation_error:
            result["valid"] = False
            result["error"] = validation_error
        
        return result
    
    def _detect_format_from_url(self, file_url: str) -> Optional[str]:
        """Detect file format from URL"""
        # Common WhatsApp CDN patterns
        if any(ext in file_url.lower() for ext in ['.jpg', '.jpeg']):
            return 'jpg'
        elif '.png' in file_url.lower():
            return 'png'
        elif '.pdf' in file_url.lower():
            return 'pdf'
        return None
    
    def _apply_service_specific_rules(
        self,
        document_type: str,
        service_type: ServiceType,
        file_format: Optional[str]
    ) -> Optional[str]:
        """
        Apply service-specific validation rules
        """
        # ID documents: Image (JPG, PNG) or PDF
        if document_type.endswith("_id"):
            if file_format not in self.allowed_image_formats + ['pdf']:
                return f"ID documents must be in {', '.join(self.allowed_image_formats)} or PDF format"
        
        # Title Deeds: Combined multi-page PDF only
        elif "deed" in document_type.lower() and "title" in document_type.lower():
            if file_format != 'pdf':
                return "Title deeds must be in PDF format (combined multi-page document)"
        
        # Surveyor General Diagrams: PDF required
        elif "surveyor" in document_type.lower() or "diagram" in document_type.lower():
            if file_format != 'pdf':
                return "Surveyor General diagrams must be in PDF format"
        
        # Legal documents (Agreements, Declarations, Forms): PDF preferred, image accepted
        elif any(keyword in document_type.lower() for keyword in 
                 ["agreement", "declaration", "form", "affidavit"]):
            if file_format not in self.allowed_image_formats + ['pdf']:
                return f"Legal documents must be in {', '.join(self.allowed_image_formats)} or PDF format"
        
        # Government certificates (CGT, Rates, Levy): PDF preferred, image accepted
        elif any(keyword in document_type.lower() for keyword in 
                 ["cgt", "rates", "levy", "clearance", "certificate"]):
            if file_format not in self.allowed_image_formats + ['pdf']:
                return f"Government certificates must be in {', '.join(self.allowed_image_formats)} or PDF format"
        
        # Default: allow common formats
        elif file_format not in self.allowed_image_formats + ['pdf']:
            return f"File must be in {', '.join(self.allowed_image_formats)} or PDF format"
        
        return None
    
    def get_allowed_formats_message(self, document_type: str) -> str:
        """Get user-friendly message about allowed formats for a document type"""
        if document_type.endswith("_id"):
            return f"Please upload your ID as an image (JPG, PNG) or PDF"
        elif "deed" in document_type.lower() and "title" in document_type.lower():
            return "Please upload your title deed as a combined multi-page PDF"
        elif "surveyor" in document_type.lower() or "diagram" in document_type.lower():
            return "Please upload the Surveyor General diagram as a PDF"
        else:
            return f"Please upload the document as an image (JPG, PNG) or PDF"


class FileStorageService:
    """Service for storing files in MongoDB GridFS"""
    
    def __init__(self):
        self.gridfs_bucket: Optional[AsyncIOMotorGridFSBucket] = None
    
    async def initialize(self):
        """Initialize GridFS bucket"""
        self.gridfs_bucket = get_gridfs_bucket()
    
    async def store_file(
        self,
        file_url: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Download file from URL and store in GridFS
        
        Args:
            file_url: URL of the file to download and store
            metadata: Metadata to store with the file
            
        Returns:
            GridFS file ID
        """
        try:
            # Download file
            async with httpx.AsyncClient() as client:
                response = await client.get(file_url)
                response.raise_for_status()
                file_content = response.content
            
            # Ensure GridFS is initialized
            if not self.gridfs_bucket:
                await self.initialize()
            
            # Store in GridFS
            file_id = await self.gridfs_bucket.upload_from_stream(
                filename=metadata.get("filename", "uploaded_file"),
                source=file_content,
                metadata=metadata
            )
            
            logger.info(f"File stored in GridFS with ID: {file_id}")
            return str(file_id)
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error storing file in GridFS: {e}")
            raise
    
    async def retrieve_file(self, file_id: str) -> bytes:
        """
        Retrieve file from GridFS by ID
        
        Args:
            file_id: GridFS file ID
            
        Returns:
            File content as bytes
        """
        try:
            if not self.gridfs_bucket:
                await self.initialize()
            
            # Open download stream
            grid_out = await self.gridfs_bucket.open_download_stream(file_id)
            content = await grid_out.read()
            
            return content
            
        except Exception as e:
            logger.error(f"Error retrieving file from GridFS: {e}")
            raise
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get file metadata from GridFS
        
        Args:
            file_id: GridFS file ID
            
        Returns:
            File metadata dictionary
        """
        try:
            if not self.gridfs_bucket:
                await self.initialize()
            
            # Get file document
            from bson import ObjectId
            file_doc = await self.gridfs_bucket.find_one({"_id": ObjectId(file_id)})
            
            if file_doc:
                return file_doc.get("metadata", {})
            return {}
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file from GridFS
        
        Args:
            file_id: GridFS file ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.gridfs_bucket:
                await self.initialize()
            
            from bson import ObjectId
            await self.gridfs_bucket.delete(ObjectId(file_id))
            
            logger.info(f"File deleted from GridFS: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from GridFS: {e}")
            return False


class DocumentUploadProgress:
    """Track document upload progress for applications"""
    
    @staticmethod
    async def update_document_url(
        application_id: str,
        document_type: str,
        file_id: str
    ):
        """
        Update document URL in application
        
        Args:
            application_id: Application ID
            document_type: Type of document
            file_id: GridFS file ID
        """
        database = get_database()
        
        # Map document type to field name
        field_mapping = {
            "seller_id": "documents.id_document_url",
            "buyer_id": "documents.id_document_url",
            "owner_id": "documents.id_document_url",
            "grantee_id": "documents.id_document_url",
            "title_deed": "documents.deeds_document_url",
            "agreement_of_sale": "documents.agreement_of_sale_url",
            "power_of_attorney": "documents.power_of_attorney_url",
            "declarations": "documents.declarations_url",
            "cgt_clearance": "documents.cgt_clearance_url",
            "rates_clearance": "documents.rates_clearance_url",
            "levy_clearance": "documents.levy_clearance_url",
            "marital_status_proof": "documents.marital_status_proof_url",
            "surveyor_general_diagram": "documents.surveyor_general_diagram_url",
            "subdivision_permit": "documents.subdivision_permit_url",
            "certificate_of_compliance": "documents.certificate_of_compliance_url",
            "section40_form": "documents.section40_form_url",
            "partition_agreement": "documents.partition_agreement_url",
            "exchange_agreement": "documents.exchange_agreement_url",
            "affidavit": "documents.affidavit_url",
            "rectification_form": "documents.rectification_form_url",
            "allocation_letter": "documents.allocation_letter_url",
            "draft_deed_of_grant": "documents.draft_deed_of_grant_url"
        }
        
        field_name = field_mapping.get(document_type)
        if not field_name:
            logger.warning(f"Unknown document type: {document_type}")
            return
        
        # Update application
        await database.applications.update_one(
            {"_id": application_id},
            {
                "$set": {
                    field_name: f"gridfs://{file_id}",
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "uploaded_documents": document_type
                }
            }
        )
    
    @staticmethod
    async def get_upload_progress(application_id: str) -> Dict[str, Any]:
        """
        Get upload progress for an application
        
        Args:
            application_id: Application ID
            
        Returns:
            Dictionary with upload progress information
        """
        database = get_database()
        application = await database.applications.find_one({"_id": application_id})
        
        if not application:
            return {"error": "Application not found"}
        
        document_sequence = application.get("document_sequence", [])
        uploaded_documents = application.get("uploaded_documents", [])
        current_index = application.get("current_document_index", 0)
        
        total_documents = len(document_sequence)
        uploaded_count = len(uploaded_documents)
        
        return {
            "total_documents": total_documents,
            "uploaded_count": uploaded_count,
            "current_index": current_index,
            "progress_percentage": (uploaded_count / total_documents * 100) if total_documents > 0 else 0,
            "remaining_documents": total_documents - uploaded_count,
            "next_document": document_sequence[current_index] if current_index < total_documents else None
        }


# Global service instances
file_validation_service = FileValidationService()
file_storage_service = FileStorageService()
document_upload_progress = DocumentUploadProgress()


async def validate_and_store_file(
    file_url: str,
    document_type: str,
    service_type: ServiceType,
    application_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to validate and store a file
    
    Args:
        file_url: URL of the file
        document_type: Type of document
        service_type: Service type
        application_id: Application ID
        metadata: Additional metadata
        
    Returns:
        Dictionary with operation result
    """
    # Prepare metadata
    if metadata is None:
        metadata = {}
    
    metadata.update({
        "document_type": document_type,
        "service_type": service_type,
        "application_id": application_id,
        "uploaded_at": datetime.utcnow().isoformat()
    })
    
    # Validate file
    validation_result = file_validation_service.validate_file(
        file_url, document_type, service_type
    )
    
    if not validation_result["valid"]:
        return {
            "success": False,
            "error": validation_result["error"],
            "message": file_validation_service.get_allowed_formats_message(document_type)
        }
    
    # Store file
    try:
        file_id = await file_storage_service.store_file(file_url, metadata)
        
        # Update application
        await document_upload_progress.update_document_url(
            application_id, document_type, file_id
        )
        
        return {
            "success": True,
            "file_id": file_id,
            "file_format": validation_result["file_format"]
        }
        
    except Exception as e:
        logger.error(f"Error storing file: {e}")
        return {
            "success": False,
            "error": f"Failed to store file: {str(e)}"
        }