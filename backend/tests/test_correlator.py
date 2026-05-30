import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from app.services.correlator import (
    build_unified_timeline,
    calculate_risk_score,
    detect_high_risk_flags,
    generate_attack_hypotheses
)
from app.models.sql_models import Job, ChainOfCustody, ScanResult, VulnerabilityFinding

@pytest.fixture
def mock_db():
    db = MagicMock()
    return db

def test_risk_score_calculation(mock_db):
    job_id = "test-job-uuid"
    
    # 1. Base Job mock
    job = Job(
        id=job_id,
        created_at=datetime.utcnow(),
        integrity_status="VERIFIED",
        filename="evidence.bin",
        owner_user_id=1
    )
    
    # Mock database queries
    def db_query(model):
        query_mock = MagicMock()
        
        if model == Job:
            query_mock.filter.return_value.first.return_value = job
        elif model == VulnerabilityFinding:
            # Return list of vulnerabilities
            query_mock.filter.return_value.all.return_value = [
                VulnerabilityFinding(risk_level="Critical", cvss_score=9.8),
                VulnerabilityFinding(risk_level="High", cvss_score=8.5)
            ]
        elif model == ChainOfCustody:
            # Count mock for unauthorized attempts
            query_mock.filter.return_value.count.return_value = 2
        elif model == ScanResult:
            # Mock completed scan with 2 open ports
            query_mock.filter.return_value.all.return_value = []
            
        return query_mock

    mock_db.query.side_effect = db_query

    # Calculated score:
    # Base: 10
    # Integrity: 0 (verified)
    # Vulns: Critical (15) + High (10) = 25
    # Unauth attempts: 2 * 10 = 20
    # Open ports: 0
    # Expected total: 10 + 25 + 20 = 55
    score = calculate_risk_score(mock_db, job_id)
    assert score == 55

    # Change integrity to compromised -> +50
    job.integrity_status = "COMPROMISED"
    # Expected total: 55 + 50 = 105 -> Capped at 100
    score = calculate_risk_score(mock_db, job_id)
    assert score == 100

def test_detect_high_risk_flags(mock_db):
    job_id = "test-job-uuid"
    
    job = Job(
        id=job_id,
        created_at=datetime.utcnow(),
        integrity_status="COMPROMISED"
    )
    
    def db_query(model):
        query_mock = MagicMock()
        if model == Job:
            query_mock.filter.return_value.first.return_value = job
        elif model == VulnerabilityFinding:
            # Mock critical vulnerability
            query_mock.filter.return_value.count.return_value = 1
        elif model == ChainOfCustody:
            # Mock 1 unauthorized attempt
            query_mock.filter.return_value.count.return_value = 1
        elif model == ScanResult:
            # Mock no scans
            query_mock.filter.return_value.all.return_value = []
        return query_mock

    mock_db.query.side_effect = db_query
    
    flags = detect_high_risk_flags(mock_db, job_id)
    flag_ids = [f["id"] for f in flags]
    
    assert "COMPROMISED_EVIDENCE" in flag_ids
    assert "CRITICAL_VULNERABILITIES_FOUND" in flag_ids
    assert "UNAUTHORIZED_ACCESS_DETECTED" in flag_ids

def test_generate_attack_hypotheses(mock_db):
    job_id = "test-job-uuid"
    
    def db_query(model):
        query_mock = MagicMock()
        if model == VulnerabilityFinding:
            query_mock.filter.return_value.all.return_value = [
                VulnerabilityFinding(
                    service="http", port=80, cve_id="CVE-2021-41773", cvss_score=7.5, risk_level="High"
                )
            ]
        return query_mock

    mock_db.query.side_effect = db_query
    
    hypotheses = generate_attack_hypotheses(mock_db, job_id)
    assert len(hypotheses) == 1
    assert "Service Exploitation: http (Port 80)" in hypotheses[0]["scenario"]
    assert "CVE-2021-41773" in hypotheses[0]["description"]
    assert hypotheses[0]["probability"] == "High"

def test_build_unified_timeline(mock_db):
    job_id = "test-job-uuid"
    now = datetime.utcnow()
    
    job = Job(
        id=job_id,
        created_at=now,
        completed_at=now + timedelta(minutes=5),
        filename="test.png",
        source="local_upload",
        investigator_id="1"
    )
    
    def db_query(model):
        query_mock = MagicMock()
        if model == Job:
            query_mock.filter.return_value.first.return_value = job
        elif model == ChainOfCustody:
            query_mock.filter.return_value.all.return_value = [
                ChainOfCustody(
                    timestamp=now + timedelta(minutes=2),
                    event="EVIDENCE_VIEWED",
                    investigator_id="1",
                    details={"action": "view"}
                )
            ]
        elif model == ScanResult:
            query_mock.filter.return_value.all.return_value = [
                ScanResult(
                    scan_timestamp=now + timedelta(minutes=7),
                    status="completed",
                    target="8.8.8.8",
                    initiated_by="1",
                    id=1
                )
            ]
        elif model == VulnerabilityFinding:
            query_mock.filter.return_value.all.return_value = [
                VulnerabilityFinding(
                    created_at=now + timedelta(minutes=8),
                    cve_id="CVE-2019-11043",
                    port=9000,
                    service="php-fpm",
                    severity="Critical"
                )
            ]
        return query_mock

    mock_db.query.side_effect = db_query
    
    timeline = build_unified_timeline(mock_db, job_id)
    
    assert len(timeline) == 5  # acquisition, view, completed, scan, vuln
    
    # Chronological sort order checks
    assert timeline[0]["event"] == "EVIDENCE_ACQUIRED"
    assert timeline[1]["event"] == "EVIDENCE_VIEWED"
    assert timeline[2]["event"] == "PROCESSING_COMPLETED"
    assert timeline[3]["event"] == "SCAN_COMPLETED"
    assert timeline[4]["event"] == "VULNERABILITY_MAPPED"
