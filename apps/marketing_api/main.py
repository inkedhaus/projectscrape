import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.database import init_db
from .routers import ads, campaigns, performance, suppliers

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Marketing Suite API")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Marketing Suite API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Marketing Intelligence and Campaign Management Suite",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name, "debug": settings.debug}


# Include routers
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["suppliers"])

app.include_router(ads.router, prefix="/api/ads", tags=["ads"])

app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])

app.include_router(performance.router, prefix="/api/performance", tags=["performance"])


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Marketing Suite API", "version": "1.0.0", "docs": "/docs"}
