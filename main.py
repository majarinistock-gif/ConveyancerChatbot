"""
WhatsApp Chatbot for Property Conveyancing Services
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import connect_to_mongodb, close_mongodb_connection
from app.webhook import router as webhook_router
from app.api import router as api_router
from app.payment_callback import router as payment_callback_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    await connect_to_mongodb()
    print(f"🚀 {settings.ENVIRONMENT} mode active")
    print("📱 WhatsApp Conveyancing Bot started successfully")
    
    yield
    
    # Shutdown
    await close_mongodb_connection()
    print("👋 WhatsApp Conveyancing Bot shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="WhatsApp Conveyancing Bot",
    description="Property conveyancing services chatbot for Zimbabwe",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router, prefix="/webhook")
app.include_router(api_router, prefix="/api")
app.include_router(payment_callback_router, prefix="/api/payment")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "WhatsApp Conveyancing Bot",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook",
            "api": "/api",
            "docs": "/docs"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "service": "whatsapp-conveyancing-bot"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=settings.ENVIRONMENT == "sandbox"
    )