import logging
from celery import shared_task
from datetime import datetime

from app.db.session import SessionLocal
from app.models.sql_models import ScanResult, VulnerabilityFinding, ChainOfCustody
from app.services.scanner import run_scan
from app.services.cve_mapper import map_vulnerabilities

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="run_network_scan_task")
def run_network_scan_task(self, scan_id: int):
    """Celery task to run a network scan and automatically map CVE vulnerabilities"""
    db = SessionLocal()
    try:
        # 1. Load ScanResult by scan_id, set status="running"
        scan = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
        if not scan:
            logger.error(f"ScanResult with ID {scan_id} not found.")
            return

        scan.status = "running"
        db.commit()
        logger.info(f"Scan {scan_id} on target {scan.target} status updated to running.")

        # Log SCAN_INITIATED to chain of custody if job_id is set
        if scan.job_id:
            log_init = ChainOfCustody(
                job_id=scan.job_id,
                event="SCAN_INITIATED",
                investigator_id=scan.initiated_by,
                details={"target": scan.target, "scan_id": scan_id},
                timestamp=datetime.utcnow()
            )
            db.add(log_init)
            db.commit()

        # 2. Call scanner.run_scan(target)
        scan_data = run_scan(scan.target, job_id=scan.job_id)

        # 3. Save result_json, set status="completed"
        scan.result_json = scan_data
        scan.status = "completed"
        db.commit()

        # 4. Trigger CVE mapping automatically at the end of the scan
        logger.info(f"Scan {scan_id} completed. Auto-mapping vulnerabilities...")
        findings = map_vulnerabilities(scan_data)
        
        for f in findings:
            finding_entry = VulnerabilityFinding(
                scan_id=scan_id,
                job_id=scan.job_id,
                port=f.get("port"),
                service=f.get("service"),
                version=f.get("version"),
                cve_id=f.get("cve_id"),
                description=f.get("description"),
                cvss_score=f.get("cvss_score"),
                severity=f.get("severity"),
                risk_level=f.get("risk_level"),
                nvd_url=f.get("nvd_url"),
                created_at=datetime.utcnow()
            )
            db.add(finding_entry)

        # 5. Log SCAN_COMPLETED to chain of custody if job_id is set
        if scan.job_id:
            log_comp = ChainOfCustody(
                job_id=scan.job_id,
                event="SCAN_COMPLETED",
                investigator_id=scan.initiated_by,
                details={
                    "target": scan.target,
                    "scan_id": scan_id,
                    "findings_count": len(findings)
                },
                timestamp=datetime.utcnow()
            )
            db.add(log_comp)
            
        db.commit()
        logger.info(f"Vulnerability mapping completed for scan {scan_id}. Saved {len(findings)} findings.")

    except Exception as e:
        logger.error(f"Error in network scan task {scan_id}: {str(e)}")
        # Reload scan record in a new transaction context if session is corrupted
        db.rollback()
        scan = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
        if scan:
            scan.status = "failed"
            scan.error_message = str(e)
            db.commit()
            
            # Log failure to chain of custody
            if scan.job_id:
                log_fail = ChainOfCustody(
                    job_id=scan.job_id,
                    event="SCAN_FAILED",
                    investigator_id=scan.initiated_by,
                    details={"target": scan.target, "scan_id": scan_id, "error": str(e)},
                    timestamp=datetime.utcnow()
                )
                db.add(log_fail)
                db.commit()
    finally:
        db.close()
