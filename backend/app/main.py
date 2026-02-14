"""RiskShield - GRC Compliance Tool Main Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import devices, risks, ml_routes, reports, treatment

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ISO 31000-aligned GRC compliance tool with ML-powered risk detection",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(devices.router)
app.include_router(risks.router)
app.include_router(ml_routes.router)
app.include_router(reports.router)
app.include_router(treatment.router)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "ISO 31000-aligned GRC compliance tool",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
