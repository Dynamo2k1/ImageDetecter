import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.sql_models import ScanResult, VulnerabilityFinding, User
from app.models.schemas import ScanCreate, ScanStatusResponse, VulnerabilityResponse
from app.api.v1.endpoints.auth import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/scanner", tags=["scanner"])

# Conditionally import Celery tasks
if settings.USE_CELERY:
    from app.workers.scan_tasks import run_network_scan_task

def run_network_scan_sync(scan_id: int):
    """Synchronous wrapper to execute nmap scanning in a background thread when Celery is off"""
    try:
        from app.workers.scan_tasks import run_network_scan_task
        run_network_scan_task(scan_id)
    except Exception as e:
        logger.error(f"Synchronous network scan background thread failed for scan {scan_id}: {str(e)}")

@router.post("/scan", response_model=ScanStatusResponse)
async def initiate_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a non-blocking network scan against a domain or IP target"""
    try:
        # Perform target validation to reject private IPs before queueing if ALLOW_INTERNAL_SCAN is false
        if not settings.ALLOW_INTERNAL_SCAN:
            from app.services.scanner import is_private_target
            if is_private_target(scan_data.target):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target '{scan_data.target}' is a private or loopback IP address, which is prohibited by security policy."
                )

        scan = ScanResult(
            job_id=scan_data.job_id,
            target=scan_data.target,
            status="pending",
            initiated_by=str(current_user.id)
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Trigger background execution
        if settings.USE_CELERY:
            try:
                run_network_scan_task.delay(scan.id)
                logger.info(f"Triggered scan {scan.id} via Celery queue.")
            except Exception as celery_err:
                logger.warning(f"Celery queue failed, falling back to BackgroundTasks: {str(celery_err)}")
                background_tasks.add_task(run_network_scan_sync, scan.id)
        else:
            logger.info(f"Triggered scan {scan.id} via FastAPI BackgroundTasks.")
            background_tasks.add_task(run_network_scan_sync, scan.id)

        return ScanStatusResponse(
            scan_id=scan.id,
            status="running",
            target=scan.target
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate network scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the current status and parsed findings of a network scan"""
    scan = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan job not found")
        
    return ScanStatusResponse(
        scan_id=scan.id,
        status=scan.status,
        target=scan.target,
        result=scan.result_json,
        error=scan.error_message
    )

@router.get("/scans", response_model=List[ScanStatusResponse])
async def list_job_scans(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all scans associated with a given evidence job ID"""
    scans = db.query(ScanResult).filter(ScanResult.job_id == job_id).order_by(ScanResult.scan_timestamp.desc()).all()
    return [
        ScanStatusResponse(
            scan_id=s.id,
            status=s.status,
            target=s.target,
            result=s.result_json,
            error=s.error_message
        ) for s in scans
    ]

@router.get("/scan/{scan_id}/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_scan_vulnerabilities(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all vulnerability findings mapped from a single network scan"""
    findings = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.scan_id == scan_id).all()
    return findings

@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_job_vulnerabilities(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all vulnerability findings mapped across all scans of a job, sorted by CVSS rating desc"""
    findings = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.job_id == job_id).order_by(
        VulnerabilityFinding.cvss_score.desc().nullslast()
    ).all()
    return findings
