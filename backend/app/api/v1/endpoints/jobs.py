from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
import uuid
import os
import tempfile
from datetime import datetime, timedelta
import logging
import asyncio
from sqlalchemy.orm import Session
from kombu.exceptions import OperationalError as KombuOperationalError

from app.db.session import get_db
from app.models.sql_models import (
    Job,
    ChainOfCustody,
    NetworkScan,
    ScanPort,
    VulnerabilityFinding,
    IntegrityAlert,
)
from app.models.schemas import (
    URLJobCreate,
    JobStatusResponse,
    JobDetailsResponse,
    VerificationResponse,
    NetworkScanRequest,
    NetworkScanResponse,
)
from app.pipelines.url_pipeline import URLPipeline
from app.pipelines.upload_pipeline import UploadPipeline
from app.pipelines.unified_pipeline import UnifiedForensicPipeline
from app.services.validator import FileValidator
from app.services.storage import StorageService
from app.services.audit import AuditLogService
from app.services.network_scanner import NetworkScannerService
from app.services.vulnerability_mapper import VulnerabilityMapperService
from app.services.correlation import CorrelationService
from app.core.logger import ForensicLogger
from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user, user_has_any_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["jobs"])

# Conditionally import Celery tasks only when USE_CELERY is enabled
if settings.USE_CELERY:
    from app.workers.tasks import process_url_job, process_upload_job

# --- Background Helpers for non-Celery mode ---
# Note: FastAPI BackgroundTasks runs these in a ThreadPoolExecutor,
# so asyncio.run() is safe here - each thread gets its own event loop.

def run_url_pipeline_sync(job_id: str, url: str, investigator_id: str, case_number: str = None):
    """Synchronous wrapper for URL pipeline (runs in background thread)"""
    try:
        pipeline = URLPipeline()
        asyncio.run(pipeline.process_url(url, job_id, investigator_id, case_number))
    except Exception as e:
        logger.error(f"URL pipeline failed for job {job_id}: {str(e)}")


def run_upload_pipeline_sync(job_id: str, file_path: str, filename: str, investigator_id: str, case_number: str = None):
    """Synchronous wrapper for upload pipeline (runs in background thread)"""
    try:
        pipeline = UploadPipeline()
        asyncio.run(pipeline.process_file_path(file_path, filename, job_id, investigator_id))
    except Exception as e:
        logger.error(f"Upload pipeline failed for job {job_id}: {str(e)}")


# Additional enforcement
ALLOWED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
    "application/zip",
    "video/mp4",
    "audio/mpeg",
    "audio/wav",
}
MAX_UPLOAD_MB = 500


# --- Helpers ---

def _ensure_role(db: Session, current_user, allowed_roles: List[str]):
    if not user_has_any_role(db, current_user, allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access restricted to roles: {', '.join(allowed_roles)}",
        )


def _trigger_integrity_alert(
    db: Session,
    job: Job,
    expected_hash: str,
    current_hash: str,
    user_id: str,
    action: str,
):
    alert = IntegrityAlert(
        job_id=job.id,
        expected_hash=expected_hash or "",
        current_hash=current_hash or "",
        message=f"Integrity mismatch detected during {action}",
        resolved=False,
    )
    db.add(alert)

    db.add(
        ChainOfCustody(
            job_id=job.id,
            event="HASH_MISMATCH_ALERT",
            investigator_id=user_id,
            details={
                "action": action,
                "expected_hash": expected_hash,
                "current_hash": current_hash,
            },
            hash_verification=current_hash,
        )
    )
    db.commit()


def _verify_integrity_on_access(db: Session, job: Job, user_id: str, action: str) -> Dict[str, Any]:
    if not job.storage_path or not os.path.exists(job.storage_path):
        return {"checked": False, "matches": None, "current_hash": None}

    current_hash = StorageService.compute_stored_evidence_hash(job.storage_path)
    if not current_hash:
        return {"checked": True, "matches": False, "current_hash": None}

    matches = current_hash == (job.sha256_hash or "")
    if not matches:
        _trigger_integrity_alert(db, job, job.sha256_hash or "", current_hash, user_id, action)

    AuditLogService.append(
        db=db,
        action="view",
        user_id=user_id,
        job_id=job.id,
        details={
            "context": action,
            "integrity_checked": True,
            "integrity_match": matches,
            "current_hash": current_hash,
        },
    )

    return {"checked": True, "matches": matches, "current_hash": current_hash}


# --- Endpoints ---

@router.post("/jobs/url", response_model=JobStatusResponse)
async def submit_url_job(
    job_data: URLJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            status="pending",
            source="url",
            original_url=str(job_data.url),
            investigator_id=job_data.investigator_id,
            case_number=job_data.case_number,
            notes=job_data.notes,
            stage="Initialization",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        ForensicLogger.log_acquisition(
            job_id=job_id,
            source="url",
            investigator_id=job_data.investigator_id,
            url=str(job_data.url),
        )
        AuditLogService.append(
            db=db,
            action="upload",
            user_id=str(current_user.id),
            job_id=job_id,
            details={"source": "url", "target": str(job_data.url)},
        )

        # Use Celery if enabled, otherwise fall back to FastAPI BackgroundTasks
        if settings.USE_CELERY:
            try:
                process_url_job.delay(
                    job_id=job_id,
                    url=str(job_data.url),
                    investigator_id=job_data.investigator_id,
                    case_number=job_data.case_number,
                )
            except (KombuOperationalError, ConnectionError, OSError) as celery_error:
                # Fallback to BackgroundTasks if Celery/Redis is not available
                logger.warning(f"Celery unavailable, falling back to BackgroundTasks: {str(celery_error)}")
                background_tasks.add_task(
                    run_url_pipeline_sync,
                    job_id,
                    str(job_data.url),
                    job_data.investigator_id,
                    job_data.case_number,
                )
        else:
            # Use FastAPI BackgroundTasks when USE_CELERY is disabled
            logger.info(f"Processing URL job {job_id} with BackgroundTasks (USE_CELERY=false)")
            background_tasks.add_task(
                run_url_pipeline_sync,
                job_id,
                str(job_data.url),
                job_data.investigator_id,
                job_data.case_number,
            )
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL job submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/upload", response_model=JobStatusResponse)
async def submit_local_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    investigator_id: str = Form(...),
    case_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        # Validate File
        validator = FileValidator()
        validation_result = validator.validate_upload_file(file)
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])

        # Enforce MIME type
        if file.content_type not in ALLOWED_TYPES and not any(file.content_type.startswith(p) for p in ["image/", "video/", "audio/"]):
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

        job_id = str(uuid.uuid4())

        # Save to temp file
        storage_base = os.path.abspath(settings.LOCAL_STORAGE_PATH)
        temp_dir = os.path.join(storage_base, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            dir=temp_dir,
            suffix=f"_{file.filename}",
        )
        try:
            written = 0
            with open(temp_file.name, "wb") as f:
                while True:
                    chunk = file.file.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > MAX_UPLOAD_MB * 1024 * 1024:
                        os.unlink(temp_file.name)
                        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_MB}MB")
                    f.write(chunk)
        except HTTPException:
            raise
        except Exception:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")

        job = Job(
            id=job_id,
            status="pending",
            source="local_upload",
            filename=file.filename,
            investigator_id=investigator_id,
            case_number=case_number,
            notes=notes,
            stage="Initialization",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        ForensicLogger.log_acquisition(
            job_id=job_id,
            source="local_upload",
            investigator_id=investigator_id,
            filename=file.filename,
        )
        AuditLogService.append(
            db=db,
            action="upload",
            user_id=str(current_user.id),
            job_id=job_id,
            details={"source": "local_upload", "filename": file.filename},
        )

        # Use Celery if enabled, otherwise fall back to FastAPI BackgroundTasks
        if settings.USE_CELERY:
            try:
                process_upload_job.delay(
                    job_id=job_id,
                    file_path=temp_file.name,
                    filename=file.filename,
                    investigator_id=investigator_id,
                    case_number=case_number,
                )
            except (KombuOperationalError, ConnectionError, OSError) as celery_error:
                # Fallback to BackgroundTasks if Celery/Redis is not available
                logger.warning(f"Celery unavailable, falling back to BackgroundTasks: {str(celery_error)}")
                background_tasks.add_task(
                    run_upload_pipeline_sync,
                    job_id,
                    temp_file.name,
                    file.filename,
                    investigator_id,
                    case_number,
                )
        else:
            # Use FastAPI BackgroundTasks when USE_CELERY is disabled
            logger.info(f"Processing upload job {job_id} with BackgroundTasks (USE_CELERY=false)")
            background_tasks.add_task(
                run_upload_pipeline_sync,
                job_id,
                temp_file.name,
                file.filename,
                investigator_id,
                case_number,
            )
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload job submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _ensure_role(db, current_user, ["Analyst", "Senior Analyst", "Admin", "Investigator"])
    return db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _ensure_role(db, current_user, ["Analyst", "Senior Analyst", "Admin", "Investigator"])
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    AuditLogService.append(
        db=db,
        action="view",
        user_id=str(current_user.id),
        job_id=job.id,
        details={"context": "status"},
    )
    return job


@router.get("/jobs/{job_id}/details", response_model=JobDetailsResponse)
async def get_job_details(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _ensure_role(db, current_user, ["Analyst", "Senior Analyst", "Admin", "Investigator"])
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    integrity = _verify_integrity_on_access(db, job, str(current_user.id), "details")

    logs = (
        db.query(ChainOfCustody)
        .filter(ChainOfCustody.job_id == job_id)
        .order_by(ChainOfCustody.timestamp)
        .all()
    )

    scans = []
    vulnerabilities = []
    risk_assessment = {"counts": {"High": 0, "Medium": 0, "Low": 0}, "overall_risk": "Low"}

    if job.case_number:
        case_scans = db.query(NetworkScan).filter(NetworkScan.case_number == job.case_number).all()
        for scan in case_scans:
            scan_ports = db.query(ScanPort).filter(ScanPort.scan_id == scan.id).all()
            scans.append(
                {
                    "scan_id": scan.id,
                    "target": scan.target,
                    "status": scan.status,
                    "ports": [
                        {
                            "port": p.port,
                            "protocol": p.protocol,
                            "state": p.state,
                            "service": p.service,
                            "version": p.version,
                        }
                        for p in scan_ports
                    ],
                }
            )

            scan_vulns = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.scan_id == scan.id).all()
            for v in scan_vulns:
                vulnerabilities.append(
                    {
                        "id": v.id,
                        "cve_id": v.cve_id,
                        "service": v.service,
                        "version": v.version,
                        "risk_level": v.risk_level,
                        "description": v.description,
                    }
                )

        risk_assessment = VulnerabilityMapperService.summarize_risk(vulnerabilities)

    metadata = {
        "file_name": job.filename,
        "file_size": job.file_size,
        "mime_type": job.mime_type,
        "sha256_hash": job.sha256_hash,
        "extraction_timestamp": job.updated_at,
        "exif_data": {},
        "media_metadata": {},
    }

    if integrity.get("checked") and integrity.get("matches") is False:
        metadata["integrity_alert"] = {
            "message": "Integrity mismatch detected",
            "current_hash": integrity.get("current_hash"),
            "expected_hash": job.sha256_hash,
        }

    return JobDetailsResponse(
        job_id=job.id,
        status=job.status,
        source=job.source,
        platform=None,
        metadata=metadata,
        chain_of_custody=[
            {
                "timestamp": l.timestamp,
                "event": l.event,
                "details": l.details,
                "investigator_id": l.investigator_id,
                "hash_verification": l.hash_verification,
            }
            for l in logs
        ],
        original_url=job.original_url,
        file_path=job.storage_path or "",
        storage_location=job.storage_path or "",
        created_at=job.created_at,
        completed_at=job.completed_at,
        scan_results=scans,
        vulnerabilities=vulnerabilities,
        risk_assessment=risk_assessment,
    )


@router.get("/jobs/{job_id}/report")
async def download_report(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _ensure_role(db, current_user, ["Analyst", "Senior Analyst", "Admin", "Investigator"])
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    integrity = _verify_integrity_on_access(db, job, str(current_user.id), "report")
    if integrity.get("checked") and integrity.get("matches") is False:
        AuditLogService.append(
            db=db,
            action="view",
            user_id=str(current_user.id),
            job_id=job.id,
            details={
                "context": "report_blocked_integrity",
                "expected_hash": job.sha256_hash,
                "current_hash": integrity.get("current_hash"),
            },
        )
        raise HTTPException(status_code=409, detail="Evidence integrity mismatch detected; report download blocked")

    report_log = (
        db.query(ChainOfCustody)
        .filter(ChainOfCustody.job_id == job_id, ChainOfCustody.event == "REPORT_GENERATED")
        .first()
    )
    pdf_path = report_log.details.get("report_path") if report_log and report_log.details else None

    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Report not available")

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"Forensic_Report_{job_id}.pdf")


@router.get("/jobs/{job_id}/pdf")
async def generate_pdf_endpoint(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return await download_report(job_id, db, current_user)


@router.get("/analytics")
async def get_analytics(period: str = "7d", db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _ensure_role(db, current_user, ["Analyst", "Senior Analyst", "Admin", "Investigator"])
    now = datetime.utcnow()

    # Parse period parameter
    if period == "24h":
        start_date = now - timedelta(hours=24)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:  # default to 7d
        start_date = now - timedelta(days=7)

    total = db.query(Job).filter(Job.created_at >= start_date).count()
    completed = db.query(Job).filter(Job.created_at >= start_date, Job.status == "completed").count()
    failed = db.query(Job).filter(Job.created_at >= start_date, Job.status == "failed").count()
    pending = db.query(Job).filter(Job.created_at >= start_date, Job.status == "pending").count()

    return {"total_jobs": total, "completed_jobs": completed, "failed_jobs": failed, "pending_jobs": pending}


@router.post("/jobs/{job_id}/verify", response_model=VerificationResponse)
async def verify_integrity(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _ensure_role(db, current_user, ["Analyst", "Senior Analyst", "Admin", "Investigator"])
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or not job.storage_path:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if not os.path.exists(job.storage_path):
        raise HTTPException(status_code=404, detail="Stored evidence file not found")

    current_hash = StorageService.compute_stored_evidence_hash(job.storage_path)
    if not current_hash:
        raise HTTPException(status_code=500, detail="Failed to compute evidence hash")

    matches = current_hash == (job.sha256_hash or "")

    db.add(
        ChainOfCustody(
            job_id=job.id,
            event="INTEGRITY_VERIFICATION",
            investigator_id=str(current_user.id),
            details={"verified_via": "verify_endpoint"},
            hash_verification=current_hash,
        )
    )
    db.commit()

    if not matches:
        _trigger_integrity_alert(db, job, job.sha256_hash or "", current_hash, str(current_user.id), "verify")

    AuditLogService.append(
        db=db,
        action="view",
        user_id=str(current_user.id),
        job_id=job.id,
        details={"context": "verify", "matches": matches},
    )

    pipeline = UnifiedForensicPipeline()
    result = pipeline.verify_integrity(job.storage_path, job.sha256_hash, job.id, str(current_user.id))
    result["current_hash"] = current_hash
    result["matches"] = matches

    return VerificationResponse(
        job_id=job.id,
        verification_timestamp=datetime.utcnow(),
        original_hash=result["original_hash"],
        current_hash=result["current_hash"],
        matches=result["matches"],
        verification_details=result["verification_details"],
    )


@router.delete("/jobs/{job_id}")
async def delete_evidence_job(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _ensure_role(db, current_user, ["Admin"])

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.storage_path and os.path.exists(job.storage_path):
        try:
            os.remove(job.storage_path)
        except OSError as exc:
            logger.error(f"Failed to delete evidence file for job {job_id}: {str(exc)}")
            raise HTTPException(status_code=500, detail="Failed to delete stored evidence file")

    job.storage_path = None
    job.stage = "Deleted"
    job.status = "failed"
    job.notes = "Evidence deleted by authorized user"

    db.add(
        ChainOfCustody(
            job_id=job.id,
            event="EVIDENCE_DELETED",
            investigator_id=str(current_user.id),
            details={"reason": "authorized_delete"},
        )
    )
    db.commit()

    AuditLogService.append(
        db=db,
        action="delete",
        user_id=str(current_user.id),
        job_id=job.id,
        details={"result": "deleted"},
    )

    return {"ok": True, "job_id": job_id, "deleted": True}


@router.post("/scans/network", response_model=NetworkScanResponse)
async def run_network_scan(
    payload: NetworkScanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _ensure_role(db, current_user, ["Analyst", "Senior Analyst", "Admin", "Investigator"])

    scan = NetworkScan(
        case_number=payload.case_number,
        target=payload.target,
        initiated_by=str(current_user.id),
        command="nmap -sV -Pn -oX -",
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        scan_result = NetworkScannerService.run_scan(payload.target)
        parsed = scan_result["parsed"]
        all_ports: List[Dict[str, Any]] = []

        for host in parsed.get("hosts", []):
            all_ports.extend(host.get("ports", []))

        port_row_by_number = {}
        for p in all_ports:
            port_row = ScanPort(
                scan_id=scan.id,
                port=p.get("port", 0),
                protocol=p.get("protocol", "tcp"),
                state=p.get("state", "open"),
                service=p.get("service"),
                version=p.get("version"),
            )
            db.add(port_row)
            db.flush()
            port_row_by_number.setdefault(p.get("port", 0), []).append(port_row)

        findings = VulnerabilityMapperService.map_ports(all_ports)
        for finding in findings:
            matching_port = port_row_by_number.get(finding.get("port"), [None])[0]
            vuln = VulnerabilityFinding(
                scan_id=scan.id,
                scan_port_id=matching_port.id if matching_port else None,
                cve_id=finding["cve_id"],
                service=finding.get("service"),
                version=finding.get("version"),
                risk_level=finding["risk_level"],
                description=finding.get("description"),
            )
            db.add(vuln)
            db.flush()

        scan.raw_output = scan_result["raw_output"]
        scan.command = scan_result["command"]
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(scan)

        created_correlations = CorrelationService.create_case_correlations(db, scan)
        risk_assessment = VulnerabilityMapperService.summarize_risk(findings)

        AuditLogService.append(
            db=db,
            action="scan",
            user_id=str(current_user.id),
            details={
                "scan_id": scan.id,
                "target": payload.target,
                "case_number": payload.case_number,
                "ports_found": len(all_ports),
                "vulnerabilities_found": len(findings),
            },
        )

        return NetworkScanResponse(
            scan_id=scan.id,
            case_number=scan.case_number,
            target=scan.target,
            status=scan.status,
            command=scan.command,
            ports=all_ports,
            vulnerabilities=findings,
            risk_assessment=risk_assessment,
            correlations_created=len(created_correlations),
        )

    except FileNotFoundError:
        scan.status = "failed"
        scan.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail="Nmap binary is not available on the server")
    except Exception as e:
        scan.status = "failed"
        scan.completed_at = datetime.utcnow()
        db.commit()
        logger.error(f"Network scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
