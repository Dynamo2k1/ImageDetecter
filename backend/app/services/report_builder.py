import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.sql_models import Job, ChainOfCustody, ScanResult, VulnerabilityFinding, CorrelationReport
from app.services.correlator import generate_correlation_report

logger = logging.getLogger(__name__)

def build_report_data(
    db: Session,
    job_id: str,
    investigator_id: str,
    include_custody: bool = True,
    include_scans: bool = True,
    include_vulnerabilities: bool = True,
    include_correlation: bool = True
) -> Dict[str, Any]:
    """
    Gathers all data requested for the report and structure it for the PDF generator.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    # Fetch custody logs
    custody = []
    if include_custody:
        custody = db.query(ChainOfCustody).filter(ChainOfCustody.job_id == job_id).order_by(ChainOfCustody.timestamp).all()

    # Fetch network scans
    scans = []
    if include_scans:
        scans = db.query(ScanResult).filter(ScanResult.job_id == job_id).order_by(ScanResult.scan_timestamp.desc()).all()

    # Fetch vulnerabilities
    vulnerabilities = []
    if include_vulnerabilities:
        vulnerabilities = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.job_id == job_id).order_by(VulnerabilityFinding.cvss_score.desc().nullslast()).all()

    # Fetch correlation analysis
    correlation = None
    if include_correlation:
        corr_report = db.query(CorrelationReport).filter(CorrelationReport.job_id == job_id).first()
        if corr_report:
            correlation = corr_report.result_json
        else:
            # Generate on the fly if not yet run
            try:
                correlation = generate_correlation_report(db, job_id, investigator_id)
            except Exception as e:
                logger.error(f"Failed to generate correlation on-the-fly for report: {str(e)}")

    # Format into metadata dict matching schema expectations or new dynamic parameters
    # Load metadata JSON if it exists
    exif = {}
    media = {}
    platform = {}
    
    import json
    import os
    if job.storage_path:
        meta_json_path = os.path.join(os.path.dirname(job.storage_path), "metadata.json")
        if os.path.exists(meta_json_path):
            try:
                with open(meta_json_path, 'r') as f:
                    stored_meta = json.load(f)
                    exif = stored_meta.get("exif", {})
                    media = stored_meta.get("media", {})
                    platform = stored_meta.get("platform", {})
            except Exception as e:
                logger.error(f"Failed to load metadata.json: {str(e)}")

    report_payload = {
        "job_id": job.id,
        "status": job.status,
        "source": job.source,
        "original_url": job.original_url,
        "integrity_status": job.integrity_status,
        "is_encrypted": getattr(job, 'is_encrypted', False),
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "file_path": job.storage_path or "",
        
        # Metadata
        "filename": job.filename,
        "file_size": job.file_size,
        "mime_type": job.mime_type,
        "sha256_hash": job.sha256_hash,
        "exif_data": exif,
        "media_metadata": media,
        "platform_metadata": platform,

        # Sections
        "include_custody": include_custody,
        "chain_of_custody": custody,
        
        "include_scans": include_scans,
        "scans": scans,
        
        "include_vulnerabilities": include_vulnerabilities,
        "vulnerabilities": vulnerabilities,
        
        "include_correlation": include_correlation,
        "correlation": correlation
    }

    return report_payload
