"""
API endpoints for admin dashboard integration
Provides REST endpoints for application management and document retrieval
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.database import get_database
from app.models import (
    ApplicationModel, ApplicationStatusUpdate, VerificationStatus,
    ApplicationResponse, PaymentStatus
)
from app.file_service import file_storage_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/applications")
async def get_applications(
    status: Optional[VerificationStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get list of all applications with optional filtering
    """
    try:
        database = get_database()
        
        # Build query
        query = {}
        if status:
            query["verification.status"] = status
        
        # Get applications
        cursor = database.applications.find(query).sort("created_at", -1).skip(offset).limit(limit)
        applications = []
        
        async for doc in cursor:
            application = ApplicationModel(**doc)
            applications.append(ApplicationResponse(
                application_id=str(doc["_id"]),
                owner_phone=application.owner_phone,
                service_type=application.service_type,
                status=application.verification.status,
                created_at=application.created_at,
                updated_at=application.updated_at,
                verification_status=application.verification.status
            ))
        
        # Get total count
        total_count = await database.applications.count_documents(query)
        
        return {
            "applications": applications,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve applications")


@router.get("/applications/{application_id}")
async def get_application(application_id: str):
    """
    Get detailed information about a specific application
    """
    try:
        database = get_database()
        
        application_doc = await database.applications.find_one({"_id": application_id})
        
        if not application_doc:
            raise HTTPException(status_code=404, detail="Application not found")
        
        application = ApplicationModel(**application_doc)
        
        return application.model_dump(by_alias=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve application")


@router.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: str,
    status_update: ApplicationStatusUpdate
):
    """
    Update application verification status
    """
    try:
        database = get_database()
        
        # Check if application exists
        application = await database.applications.find_one({"_id": application_id})
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Prepare update data
        update_data = {
            "verification.status": status_update.status,
            "verification.rejection_reason": status_update.rejection_reason,
            "verification.notes": status_update.notes,
            "verification.reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Update application
        result = await database.applications.update_one(
            {"_id": application_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to update application")
        
        # Send notification to user (this would be implemented with WhatsApp service)
        # await send_status_notification(application_id, status_update.status)
        
        return {
            "success": True,
            "message": "Application status updated successfully",
            "application_id": application_id,
            "new_status": status_update.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update application status")


@router.get("/applications/{application_id}/documents")
async def get_application_documents(application_id: str):
    """
    Get document URLs for a specific application
    """
    try:
        database = get_database()
        
        application = await database.applications.find_one(
            {"_id": application_id},
            {"documents": 1, "service_type": 1}
        )
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "application_id": application_id,
            "service_type": application.get("service_type"),
            "documents": application.get("documents", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.post("/applications/{application_id}/reject")
async def reject_application(
    application_id: str,
    rejection_data: dict
):
    """
    Reject an application with reason
    """
    try:
        database = get_database()
        
        # Check if application exists
        application = await database.applications.find_one({"_id": application_id})
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        rejection_reason = rejection_data.get("reason")
        if not rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        
        # Update application status
        await database.applications.update_one(
            {"_id": application_id},
            {
                "$set": {
                    "verification.status": VerificationStatus.REJECTED,
                    "verification.rejection_reason": rejection_reason,
                    "verification.reviewed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Send rejection notification to user
        # await send_rejection_notification(application_id, rejection_reason)
        
        return {
            "success": True,
            "message": "Application rejected successfully",
            "application_id": application_id,
            "rejection_reason": rejection_reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting application: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject application")


@router.get("/applications/{application_id}/payment")
async def get_application_payment(application_id: str):
    """
    Get payment information for an application
    """
    try:
        database = get_database()
        
        application = await database.applications.find_one(
            {"_id": application_id},
            {"payment": 1}
        )
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "application_id": application_id,
            "payment": application.get("payment", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment information: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment information")


@router.get("/documents/{file_id}")
async def get_document(file_id: str):
    """
    Retrieve a document from GridFS by file ID
    """
    try:
        # Ensure file storage service is initialized
        await file_storage_service.initialize()
        
        # Retrieve file content
        content = await file_storage_service.retrieve_file(file_id)
        
        # Get file metadata
        metadata = await file_storage_service.get_file_metadata(file_id)
        
        from fastapi.responses import Response
        import mimetypes
        
        # Determine content type
        filename = metadata.get("filename", "document")
        content_type, _ = mimetypes.guess_type(filename)
        
        if not content_type:
            content_type = "application/octet-stream"
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.get("/conveyancers")
async def get_conveyancers(
    province: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get list of conveyancers with optional filtering
    """
    try:
        database = get_database()
        
        # Build query
        query = {}
        if province:
            query["province"] = province
        
        # Get conveyancers
        cursor = database.conveyancers.find(query).sort("company_name", 1).skip(offset).limit(limit)
        conveyancers = []
        
        async for doc in cursor:
            conveyancers.append(doc)
        
        # Get total count
        total_count = await database.conveyancers.count_documents(query)
        
        return {
            "conveyancers": conveyancers,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting conveyancers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conveyancers")


@router.get("/stats")
async def get_statistics():
    """
    Get application statistics
    """
    try:
        database = get_database()
        
        # Get total applications
        total_applications = await database.applications.count_documents({})
        
        # Get applications by status
        status_counts = {}
        for status in VerificationStatus:
            count = await database.applications.count_documents({
                "verification.status": status
            })
            status_counts[status.value] = count
        
        # Get payment statistics
        payment_stats = {}
        for payment_status in PaymentStatus:
            count = await database.applications.count_documents({
                "payment.status": payment_status
            })
            payment_stats[payment_status.value] = count
        
        # Get applications by service type
        from app.models import ServiceType
        service_type_counts = {}
        for service_type in ServiceType:
            count = await database.applications.count_documents({
                "service_type": service_type
            })
            service_type_counts[service_type.value] = count
        
        return {
            "total_applications": total_applications,
            "by_status": status_counts,
            "by_payment_status": payment_stats,
            "by_service_type": service_type_counts
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/health")
async def api_health():
    """
    Health check endpoint for API
    """
    try:
        # Check database connection
        database = get_database()
        await database.command('ping')
        
        return {
            "status": "healthy",
            "service": "admin-api",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "admin-api",
            "database": "disconnected",
            "error": str(e)
        }