"""
OCR.space integration for document processing
Handles OCR processing for Zimbabwean ID documents
"""
import logging
import re
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.models import ExtractedProfile

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR processing using OCR.space API"""
    
    def __init__(self):
        self.api_key = settings.OCR_SPACE_API_KEY
        self.engine = settings.OCR_SPACE_ENGINE
        self.base_url = "https://api.ocr.space/parse/image"
    
    async def process_document(self, image_url: str) -> Dict[str, Any]:
        """
        Process document image through OCR.space API
        
        Args:
            image_url: URL of the image to process
            
        Returns:
            Dictionary with OCR results and extracted profile data
        """
        try:
            # Download image content
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                if response.status_code != 200:
                    logger.error(f"Failed to download image: {response.status_code}")
                    return {"success": False, "error": "Failed to download image"}
                
                image_content = response.content
            
            # Prepare OCR request
            payload = {
                "base64Image": f"data:image/jpeg;base64,{self._encode_to_base64(image_content)}",
                "language": "eng",
                "isTable": True,
                "scale": True,
                "OCREngine": self.engine,
                "detectOrientation": True,
                "isCreateSearchablePdf": False
            }
            
            # Send OCR request
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, data=payload)
                response.raise_for_status()
                ocr_result = response.json()
            
            # Process OCR results
            if ocr_result.get("IsErroredOnProcessing", False):
                error_message = ocr_result.get("ErrorMessage", "Unknown OCR error")
                logger.error(f"OCR processing failed: {error_message}")
                return {"success": False, "error": error_message}
            
            # Extract text from OCR results
            parsed_text = self._extract_text_from_ocr(ocr_result)
            
            # Parse Zimbabwean ID patterns
            extracted_profile = self._parse_zimbabwean_id(parsed_text)
            
            return {
                "success": True,
                "raw_text": parsed_text,
                "extracted_profile": extracted_profile,
                "ocr_result": ocr_result
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during OCR processing: {e}")
            return {"success": False, "error": "HTTP error during OCR processing"}
        except Exception as e:
            logger.error(f"Error during OCR processing: {e}")
            return {"success": False, "error": "OCR processing failed"}
    
    def _encode_to_base64(self, content: bytes) -> str:
        """Encode bytes to base64 string"""
        import base64
        return base64.b64encode(content).decode('utf-8')
    
    def _extract_text_from_ocr(self, ocr_result: Dict[str, Any]) -> str:
        """Extract text from OCR.space API response"""
        parsed_results = ocr_result.get("ParsedResults", [])
        if not parsed_results:
            return ""
        
        # Combine text from all parsed results
        text_lines = []
        for result in parsed_results:
            lines = result.get("ParsedText", "").split('\n')
            text_lines.extend([line.strip() for line in lines if line.strip()])
        
        return '\n'.join(text_lines)
    
    def _parse_zimbabwean_id(self, text: str) -> ExtractedProfile:
        """
        Parse Zimbabwean ID document text to extract profile information
        
        Zimbabwean ID patterns:
        - ID Number: XX-XXXXXXX[XX] (e.g., 63-201948Z18)
        - DOB: DD-MM-YYYY or DD/MM/YYYY
        - Gender: M/F indicators
        - Name: SURNAME and NAMES fields
        """
        profile = ExtractedProfile()
        
        # Extract ID number (pattern: XX-XXXXXXX[XX])
        id_pattern = r'\d{2}-\d{6,7}[A-Z]\d{2}'
        id_match = re.search(id_pattern, text)
        if id_match:
            profile.id_number = id_match.group()
        
        # Extract date of birth (multiple formats)
        dob_patterns = [
            r'\d{2}[-/.](0[1-9]|1[0-2])[-/.](19|20)\d{2}',  # DD-MM-YYYY
            r'(DOB|Date of Birth)[:\s]*(\d{2}[-/.](0[1-9]|1[0-2])[-/.](19|20)\d{2})'
        ]
        
        for pattern in dob_patterns:
            dob_match = re.search(pattern, text, re.IGNORECASE)
            if dob_match:
                # Extract just the date part
                date_str = re.search(r'\d{2}[-/.](0[1-9]|1[0-2])[-/.](19|20)\d{2}', dob_match.group())
                if date_str:
                    profile.date_of_birth = date_str.group()
                    break
        
        # Extract gender (M/F indicators)
        gender_patterns = [
            r'Gender[:\s]*([MF])',
            r'Sex[:\s]*([MF])',
            r'\b([MF])\b'  # Standalone M or F
        ]
        
        for pattern in gender_patterns:
            gender_match = re.search(pattern, text, re.IGNORECASE)
            if gender_match:
                gender = gender_match.group(1).upper()
                profile.gender = "Male" if gender == "M" else "Female"
                break
        
        # Extract name (SURNAME and NAMES fields)
        name_patterns = [
            r'SURNAME[:\s]*([A-Za-z\s]+)',
            r'NAMES[:\s]*([A-Za-z\s]+)',
            r'Name[:\s]*([A-Za-z\s]+)'
        ]
        
        surname = None
        first_names = None
        
        for pattern in name_patterns:
            if "SURNAME" in pattern:
                surname_match = re.search(pattern, text, re.IGNORECASE)
                if surname_match:
                    surname = surname_match.group(1).strip()
            elif "NAMES" in pattern:
                names_match = re.search(pattern, text, re.IGNORECASE)
                if names_match:
                    first_names = names_match.group(1).strip()
        
        # Combine surname and first names
        if surname and first_names:
            profile.full_name = f"{first_names} {surname}"
        elif surname:
            profile.full_name = surname
        elif first_names:
            profile.full_name = first_names
        
        return profile
    
    async def process_with_fallback(self, image_url: str) -> Dict[str, Any]:
        """
        Process document with automatic fallback to manual input on failure
        """
        result = await self.process_document(image_url)
        
        if not result["success"]:
            logger.warning(f"OCR processing failed, returning fallback result: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "fallback_required": True,
                "message": "OCR processing failed. Please enter your details manually."
            }
        
        # Check if OCR extracted sufficient data
        profile = result.get("extracted_profile")
        if not profile or not any([profile.full_name, profile.id_number]):
            logger.warning("OCR extracted insufficient data")
            return {
                "success": False,
                "error": "Insufficient data extracted",
                "fallback_required": True,
                "message": "Could not extract complete information. Please enter your details manually."
            }
        
        return result


# Global OCR service instance
ocr_service = OCRService()


async def process_document_ocr(image_url: str) -> Dict[str, Any]:
    """
    Convenience function to process document through OCR
    """
    return await ocr_service.process_with_fallback(image_url)