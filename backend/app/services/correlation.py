from typing import List
from sqlalchemy.orm import Session

from app.models.sql_models import (
    Job,
    NetworkScan,
    VulnerabilityFinding,
    EvidenceCorrelation,
    AuditLog
)


class CorrelationService:
    """Correlates scan findings with evidence and related logs by case number."""

    @staticmethod
    def create_case_correlations(db: Session, scan: NetworkScan) -> List[EvidenceCorrelation]:
        evidence_jobs = db.query(Job).filter(Job.case_number == scan.case_number).all()
        vulnerabilities = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.scan_id == scan.id).all()
        created: List[EvidenceCorrelation] = []

        for job in evidence_jobs:
            job_logs_count = db.query(AuditLog).filter(AuditLog.job_id == job.id).count()

            if vulnerabilities:
                for vuln in vulnerabilities:
                    corr = EvidenceCorrelation(
                        job_id=job.id,
                        scan_id=scan.id,
                        vulnerability_id=vuln.id,
                        correlation_type="case_vulnerability_link",
                        confidence=0.85 if vuln.risk_level == "High" else 0.7,
                        details={
                            "reason": "Matched by case number and active vulnerability finding",
                            "risk_level": vuln.risk_level,
                            "audit_log_count": job_logs_count
                        }
                    )
                    db.add(corr)
                    created.append(corr)
            else:
                corr = EvidenceCorrelation(
                    job_id=job.id,
                    scan_id=scan.id,
                    vulnerability_id=None,
                    correlation_type="case_scan_link",
                    confidence=0.6,
                    details={
                        "reason": "Matched by case number",
                        "audit_log_count": job_logs_count
                    }
                )
                db.add(corr)
                created.append(corr)

        db.commit()
        for item in created:
            db.refresh(item)
        return created
