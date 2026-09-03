"""
Law firm selection with pagination
Handles paginated display of conveyancers for user selection
"""
import logging
from typing import Dict, Any, List, Optional
from app.config import settings
from app.database import get_database
from app.models import ConveyancerModel

logger = logging.getLogger(__name__)


class LawFirmSelector:
    """Manages law firm selection with pagination"""
    
    def __init__(self):
        self.firms_per_page = settings.CONVEYANCERS_PER_PAGE
    
    async def get_conveyancers(
        self,
        page: int = 1,
        province: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get conveyancers with pagination
        
        Args:
            page: Page number (1-based)
            province: Optional province filter
            
        Returns:
            Dictionary with conveyancers and pagination info
        """
        try:
            database = get_database()
            
            # Build query
            query = {}
            if province:
                query["province"] = province
            
            # Calculate skip value for pagination
            skip = (page - 1) * self.firms_per_page
            
            # Get total count
            total_count = await database.conveyancers.count_documents(query)
            
            # Get conveyancers for current page (sorted alphabetically)
            cursor = database.conveyancers.find(query).sort("company_name", 1).skip(skip).limit(self.firms_per_page)
            conveyancers = []
            async for doc in cursor:
                conveyancers.append(ConveyancerModel(**doc))
            
            # Calculate pagination info
            total_pages = (total_count + self.firms_per_page - 1) // self.firms_per_page
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "conveyancers": conveyancers,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "firms_per_page": self.firms_per_page,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting conveyancers: {e}")
            return {
                "conveyancers": [],
                "pagination": {
                    "current_page": page,
                    "total_pages": 0,
                    "total_count": 0,
                    "firms_per_page": self.firms_per_page,
                    "has_next": False,
                    "has_prev": False
                }
            }
    
    def format_conveyancers_message(
        self,
        conveyancers: List[ConveyancerModel],
        pagination: Dict[str, Any]
    ) -> str:
        """
        Format conveyancers list as WhatsApp message
        
        Args:
            conveyancers: List of conveyancers for current page
            pagination: Pagination information
            
        Returns:
            Formatted message string
        """
        if not conveyancers:
            return "No law firms found. Please try again later."
        
        message = "🏢 *Available Law Firms*\n\n"
        
        # Display conveyancers
        start_num = (pagination["current_page"] - 1) * self.firms_per_page + 1
        for i, conveyancer in enumerate(conveyancers, start=start_num):
            message += f"{i}. *{conveyancer.company_name}*\n"
            message += f"   Contact: {conveyancer.contact_person}\n"
            message += f"   Phone: {conveyancer.phone_number}\n"
            message += f"   Province: {conveyancer.province}\n\n"
        
        # Add pagination controls
        message += f"Page {pagination['current_page']} of {pagination['total_pages']}\n"
        
        if pagination["has_prev"]:
            message += "Reply 'prev' for previous page\n"
        
        if pagination["has_next"]:
            message += "Reply 'next' for more options\n"
        
        message += "\nOr reply with the number of your chosen firm."
        
        return message
    
    def format_conveyancer_selection_message(self, conveyancer: ConveyancerModel) -> str:
        """
        Format selected conveyancer confirmation message
        
        Args:
            conveyancer: Selected conveyancer
            
        Returns:
            Formatted confirmation message
        """
        return (
            f"✅ *Law Firm Selected*\n\n"
            f"*{conveyancer.company_name}*\n"
            f"Contact Person: {conveyancer.contact_person}\n"
            f"Email: {conveyancer.email}\n"
            f"Phone: {conveyancer.phone_number}\n"
            f"TIN: {conveyancer.tin_number}\n"
            f"Province: {conveyancer.province}\n\n"
            f"This firm will handle your conveyancing application."
        )
    
    async def get_conveyancer_by_selection(
        self,
        selection: str,
        current_page: int = 1
    ) -> Optional[ConveyancerModel]:
        """
        Get conveyancer by user selection (number or name)
        
        Args:
            selection: User's selection (number or firm name)
            current_page: Current page number for context
            
        Returns:
            Selected conveyancer or None
        """
        try:
            database = get_database()
            
            # Try to parse as number first
            try:
                selection_num = int(selection.strip())
                
                # Calculate which firm this corresponds to
                skip = (current_page - 1) * self.firms_per_page
                target_position = skip + selection_num - 1
                
                # Get the firm at this position
                cursor = database.conveyancers.find().sort("company_name", 1).skip(target_position).limit(1)
                doc = await cursor.next()
                
                if doc:
                    return ConveyancerModel(**doc)
                
            except ValueError:
                pass
            
            # Try to find by name
            name_match = await database.conveyancers.find_one({
                "company_name": {"$regex": selection, "$options": "i"}
            })
            
            if name_match:
                return ConveyancerModel(**name_match)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conveyancer by selection: {e}")
            return None
    
    async def get_provinces(self) -> List[str]:
        """
        Get list of available provinces for filtering
        
        Returns:
            List of province names
        """
        try:
            database = get_database()
            
            # Get distinct provinces
            provinces = await database.conveyancers.distinct("province")
            
            # Sort alphabetically
            provinces.sort()
            
            return provinces
            
        except Exception as e:
            logger.error(f"Error getting provinces: {e}")
            return []
    
    def format_provinces_message(self, provinces: List[str]) -> str:
        """
        Format provinces list as WhatsApp message
        
        Args:
            provinces: List of provinces
            
        Returns:
            Formatted message string
        """
        if not provinces:
            return "No provinces available."
        
        message = "📍 *Filter by Province*\n\n"
        
        for i, province in enumerate(provinces, 1):
            message += f"{i}. {province}\n"
        
        message += "\nReply with the number to filter, or 'all' to show all firms."
        
        return message
    
    async def get_conveyancer_by_id(self, conveyancer_id: str) -> Optional[ConveyancerModel]:
        """
        Get conveyancer by database ID
        
        Args:
            conveyancer_id: Conveyancer ID
            
        Returns:
            Conveyancer or None
        """
        try:
            database = get_database()
            from bson import ObjectId
            
            doc = await database.conveyancers.find_one({"_id": ObjectId(conveyancer_id)})
            
            if doc:
                return ConveyancerModel(**doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conveyancer by ID: {e}")
            return None


class FirmSelectionSession:
    """Manages a single firm selection session"""
    
    def __init__(self):
        self.current_page = 1
        self.selected_province = None
        self.selector = LawFirmSelector()
    
    async def get_current_page(self) -> str:
        """Get current page message"""
        result = await self.selector.get_conveyancers(
            page=self.current_page,
            province=self.selected_province
        )
        
        return self.selector.format_conveyancers_message(
            result["conveyancers"],
            result["pagination"]
        )
    
    async def next_page(self) -> str:
        """Move to next page"""
        self.current_page += 1
        return await self.get_current_page()
    
    async def prev_page(self) -> str:
        """Move to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
        return await self.get_current_page()
    
    async def select_firm(self, selection: str) -> Optional[ConveyancerModel]:
        """Select a firm"""
        return await self.selector.get_conveyancer_by_selection(
            selection,
            self.current_page
        )
    
    async def filter_by_province(self, province: str) -> str:
        """Filter by province"""
        self.selected_province = province
        self.current_page = 1
        return await self.get_current_page()
    
    async def reset_filter(self) -> str:
        """Reset province filter"""
        self.selected_province = None
        self.current_page = 1
        return await self.get_current_page()


# Global selector instance
law_firm_selector = LawFirmSelector()


async def get_conveyancers_page(page: int = 1, province: Optional[str] = None) -> str:
    """
    Convenience function to get conveyancers page as formatted message
    """
    result = await law_firm_selector.get_conveyancers(page, province)
    return law_firm_selector.format_conveyancers_message(
        result["conveyancers"],
        result["pagination"]
    )


async def select_conveyancer(selection: str, current_page: int = 1) -> Optional[ConveyancerModel]:
    """
    Convenience function to select conveyancer
    """
    return await law_firm_selector.get_conveyancer_by_selection(selection, current_page)


async def get_available_provinces() -> str:
    """
    Convenience function to get available provinces as formatted message
    """
    provinces = await law_firm_selector.get_provinces()
    return law_firm_selector.format_provinces_message(provinces)