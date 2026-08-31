"""FastAPI Main Application Entry Point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.api import api_router
from app.database.base import Base
from app.database.session import engine
from app.utils.logger import app_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context."""
    app_logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        app_logger.info("Database tables initialized successfully.")
    except Exception as exc:
        app_logger.error(f"Error creating database tables: {exc}")
    yield
    app_logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade AI Healthcare SaaS Platform backend API.",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.get_cors_origins()
allowed_origins = list(set([
    *origins,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://care-ai-saa-j8tpn00lf-pillu212006-4156s-projects.vercel.app",
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint for container probes and cloud monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }


@app.get("/", tags=["Root"])
def root():
    """Root redirect / landing summary."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "documentation": "/docs",
        "health": "/api/health",
        "api_v1": settings.API_V1_STR,
    }


# Mount API V1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global fallback exception handler."""
    app_logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Please contact support."},
    )
