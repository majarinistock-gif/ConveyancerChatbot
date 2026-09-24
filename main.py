"""
WhatsApp Chatbot for Property Conveyancing Services
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from pathlib import Path
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
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(payment_callback_router, prefix="/api/payment", tags=["payment"])

# Root endpoint
@app.get("/")
@app.head("/")
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

# Privacy Policy endpoint
@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy():
    """Serve the Privacy Policy document for Meta app submission"""
    privacy_policy_path = Path(__file__).parent / "PRIVACY_POLICY.md"
    
    if not privacy_policy_path.exists():
        return HTMLResponse(content="<h1>Privacy Policy Not Found</h1><p>The privacy policy document is not available.</p>", status_code=404)
    
    with open(privacy_policy_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()
    
    # Convert markdown to simple HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Privacy Policy - WhatsApp Conveyancing Bot</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            h1 {{
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                margin-top: 30px;
                border-bottom: 1px solid #ecf0f1;
                padding-bottom: 5px;
            }}
            ul, ol {{
                margin-left: 20px;
            }}
            li {{
                margin-bottom: 8px;
            }}
            code {{
                background-color: #f8f9fa;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{markdown_content}</pre>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=False  # Disable auto-reload for containerized deployments
    )