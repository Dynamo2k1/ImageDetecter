# Passlib bcrypt patch for Python 3.12 compatibility
try:
    import bcrypt
    if not hasattr(bcrypt, "__about__"):
        bcrypt.__about__ = type('About', (object,), {'__version__': getattr(bcrypt, '__version__', '4.0.0')})
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import app.workers.celery_app

import logging
from app.api.v1.endpoints.links import router as links_router
from app.api.v1.endpoints.social import router as social_router
from app.api.v1.endpoints.profile import router as profile_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.scanner import router as scanner_router
from app.api.v1.endpoints.correlation import router as correlation_router
from app.api.v1.endpoints.recon import router as recon_router
from app.db.init_db import init_db
from app.db.session import get_db

logger = logging.getLogger("app.main")



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup and check for dependencies"""
    from app.db.session import SessionLocal
    import shutil
    
    # Check if nmap is installed
    if not shutil.which("nmap"):
        logger.warning("WARNING: 'nmap' binary is not found on the host system PATH. Controlled Network Scanning features will fail unless nmap is installed.")
    else:
        logger.info("Found 'nmap' binary on host system PATH.")
    
    # Initialize database tables
    init_db()
    
    # Create default admin user
    db = SessionLocal()
    try:
        from app.db.init_db import create_default_admin
        create_default_admin(db)
    finally:
        db.close()
    
    yield
    # Cleanup on shutdown (if needed)



app = FastAPI(title="FEAS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Root
@app.get("/")
async def root():
    return {"name": "FEAS", "version": "1.0.0"}

# Routers
app.include_router(auth_router)
app.include_router(links_router)
app.include_router(social_router)
app.include_router(profile_router)
app.include_router(dashboard_router)
app.include_router(jobs_router)
app.include_router(scanner_router)
app.include_router(correlation_router)
app.include_router(recon_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
