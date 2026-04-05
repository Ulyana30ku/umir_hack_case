"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.routes import health, agent

# Setup logging on startup
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Browser Assistant - управление браузером через естественный язык",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Request Models ============

class RunRequest(BaseModel):
    """Request for agent run."""
    query: str
    run_id: Optional[str] = None


class DebugCommandRequest(BaseModel):
    """Request for debug commands."""
    session_id: str = "default"
    url: Optional[str] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    key: Optional[str] = None


# ============ Include Routers ============

app.include_router(health.router, tags=["Health"])
app.include_router(agent.router, tags=["Agent"])


# ============ Startup Event ============

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize tools
    try:
        from app.tools import init_tools
        from app.mcp.server import get_mcp_server
        init_tools()
        # Verify tools are registered
        server = get_mcp_server()
        tool_count = len(server.list_tools())
        logger.info(f"Tools initialized successfully: {tool_count} tools")
    except Exception as e:
        logger.warning(f"Failed to initialize tools: {e}")
    
    # Initialize browser
    try:
        from app.browser.session_manager import init_browser
        await init_browser(headless=True)
        logger.info("Browser initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize browser: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.app_name}")
    
    # Close browser
    try:
        from app.browser.session_manager import close_browser
        await close_browser()
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")


# ============ Custom OpenAPI ============

def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Browser Assistant - управление браузером через естественный язык",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ============ Capabilities Endpoint ============

@app.get("/agent/capabilities")
async def get_capabilities():
    """Get agent capabilities."""
    try:
        from app.mcp.server import get_mcp_server
        server = get_mcp_server()
        return server.get_capabilities()
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return {"error": str(e)}


# ============ Health Check ============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.get("/version")
async def get_version():
    """Get application version."""
    return {
        "version": settings.app_version,
        "name": settings.app_name,
    }
