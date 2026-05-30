import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.session import get_db
from app.models.sql_models import Job, CorrelationReport, ChainOfCustody, User
from app.models.schemas import CorrelationCreate, CorrelationResponse
from app.api.v1.endpoints.auth import get_current_user
from app.services.correlator import generate_correlation_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/correlation", tags=["correlation"])

@router.post("/analyze", response_model=CorrelationResponse)
async def analyze_correlation(
    payload: CorrelationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers correlation analysis for an evidence job, builds the timeline,
    risk score, attack paths, and saves/updates it in the DB.
    """
    # 1. Verify job exists
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2. RBAC check: only owner or admin can trigger analysis
    if not (current_user.is_admin or (job.owner_user_id is None) or current_user.id == job.owner_user_id):
        # Log unauthorized attempt
        log = ChainOfCustody(
            job_id=job.id,
            event="UNAUTHORIZED_ACCESS_ATTEMPT",
            investigator_id=str(current_user.id),
            details={"action": "run_correlation_analysis", "user_email": current_user.email},
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=403, detail="Access Denied — you are not the owner of this evidence")

    try:
        # 3. Generate report payload
        report_data = generate_correlation_report(db, payload.job_id, payload.investigator_id)
        score = report_data.get("score", 0)

        # 4. Check if a report already exists for this job, overwrite or create new
        existing_report = db.query(CorrelationReport).filter(CorrelationReport.job_id == payload.job_id).first()
        if existing_report:
            existing_report.correlation_timestamp = datetime.utcnow()
            existing_report.result_json = report_data
            existing_report.correlation_score = score
            existing_report.generated_by = payload.investigator_id
            report = existing_report
        else:
            report = CorrelationReport(
                job_id=payload.job_id,
                correlation_timestamp=datetime.utcnow(),
                result_json=report_data,
                correlation_score=score,
                generated_by=payload.investigator_id
            )
            db.add(report)

        # 5. Log to Chain of Custody
        log_custody = ChainOfCustody(
            job_id=payload.job_id,
            event="CORRELATION_GENERATED",
            investigator_id=payload.investigator_id,
            details={
                "risk_score": score,
                "flags_count": len(report_data.get("flags", [])),
                "hypotheses_count": len(report_data.get("attack_hypotheses", []))
            },
            timestamp=datetime.utcnow()
        )
        db.add(log_custody)
        db.commit()
        db.refresh(report)

        return report

    except Exception as e:
        logger.error(f"Correlation analysis failed for job {payload.job_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")

@router.get("/{job_id}", response_model=CorrelationResponse)
async def get_correlation_report(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the latest correlation analysis report for an evidence job
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # RBAC check: only owner or admin can view report
    if not (current_user.is_admin or (job.owner_user_id is None) or current_user.id == job.owner_user_id):
        log = ChainOfCustody(
            job_id=job.id,
            event="UNAUTHORIZED_ACCESS_ATTEMPT",
            investigator_id=str(current_user.id),
            details={"action": "view_correlation_report", "user_email": current_user.email},
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=403, detail="Access Denied — you are not the owner of this evidence")

    report = db.query(CorrelationReport).filter(CorrelationReport.job_id == job_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Correlation report not generated yet for this job")

    return report
