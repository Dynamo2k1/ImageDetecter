import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.sql_models import Job, ChainOfCustody, ScanResult, VulnerabilityFinding

logger = logging.getLogger(__name__)

def build_unified_timeline(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """
    Builds a unified chronological timeline from all events associated with a job:
    1. Job acquisition/creation
    2. SQL Chain of Custody events
    3. Network scans
    4. Vulnerability findings
    """
    timeline = []

    # 1. Job details
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return timeline

    # Initial Acquisition Event
    timeline.append({
        "timestamp": job.created_at,
        "event": "EVIDENCE_ACQUIRED",
        "investigator_id": job.investigator_id or "system",
        "details": {
            "source": job.source,
            "filename": job.filename,
            "case_number": job.case_number,
            "notes": job.notes
        },
        "type": "system"
    })

    if job.completed_at:
        timeline.append({
            "timestamp": job.completed_at,
            "event": "PROCESSING_COMPLETED",
            "investigator_id": "system",
            "details": {
                "filename": job.filename,
                "sha256_hash": job.sha256_hash
            },
            "type": "system"
        })

    # 2. Chain of Custody logs
    custody_logs = db.query(ChainOfCustody).filter(ChainOfCustody.job_id == job_id).all()
    for log in custody_logs:
        # Avoid duplicating the initial acquisition if it is already covered
        if log.event == "EVIDENCE_ACQUISITION":
            continue
        timeline.append({
            "timestamp": log.timestamp,
            "event": log.event,
            "investigator_id": log.investigator_id,
            "details": log.details or {},
            "type": "custody"
        })

    # 3. Scan results
    scans = db.query(ScanResult).filter(ScanResult.job_id == job_id).all()
    for scan in scans:
        timeline.append({
            "timestamp": scan.scan_timestamp,
            "event": f"SCAN_{scan.status.upper()}",
            "investigator_id": scan.initiated_by,
            "details": {
                "scan_id": scan.id,
                "target": scan.target,
                "error": scan.error_message
            },
            "type": "scan"
        })

    # 4. Vulnerabilities
    vulns = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.job_id == job_id).all()
    for vuln in vulns:
        timeline.append({
            "timestamp": vuln.created_at,
            "event": "VULNERABILITY_MAPPED",
            "investigator_id": "system",
            "details": {
                "cve_id": vuln.cve_id,
                "port": vuln.port,
                "service": vuln.service,
                "severity": vuln.severity,
                "cvss_score": vuln.cvss_score
            },
            "type": "vulnerability"
        })

    # Sort chronologically
    timeline.sort(key=lambda x: x["timestamp"] or datetime.min)
    return timeline

def calculate_risk_score(db: Session, job_id: str) -> int:
    """
    Calculates an overall risk score from 0 to 100 based on security findings
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return 0

    score = 10  # Base score

    # Integrity Status
    if job.integrity_status == "COMPROMISED":
        score += 50

    # Vulnerability metrics
    vulns = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.job_id == job_id).all()
    
    crit_count = 0
    high_count = 0
    med_count = 0
    low_count = 0
    
    for v in vulns:
        r_level = (v.risk_level or "").lower()
        if r_level == "critical":
            crit_count += 1
        elif r_level == "high":
            high_count += 1
        elif r_level == "medium":
            med_count += 1
        elif r_level == "low":
            low_count += 1

    score += min(crit_count * 15, 40)
    score += min(high_count * 10, 30)
    score += min(med_count * 5, 20)
    score += min(low_count * 2, 10)

    # Unauthorized access attempts in chain of custody
    unauth_count = db.query(ChainOfCustody).filter(
        ChainOfCustody.job_id == job_id,
        ChainOfCustody.event == "UNAUTHORIZED_ACCESS_ATTEMPT"
    ).count()
    score += min(unauth_count * 10, 30)

    # Open ports metrics
    scans = db.query(ScanResult).filter(
        ScanResult.job_id == job_id,
        ScanResult.status == "completed"
    ).all()
    
    open_ports_count = 0
    for s in scans:
        if s.result_json and "hosts" in s.result_json:
            for host in s.result_json["hosts"]:
                open_ports_count += len(host.get("ports", []))

    score += min(open_ports_count * 3, 15)

    # Cap between 0 and 100
    return max(0, min(100, score))

def detect_high_risk_flags(db: Session, job_id: str) -> List[Dict[str, str]]:
    """
    Returns warning flags for high-risk findings
    """
    flags = []
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return flags

    # 1. Compromised Evidence
    if job.integrity_status == "COMPROMISED":
        flags.append({
            "id": "COMPROMISED_EVIDENCE",
            "title": "Evidence Integrity Failure",
            "description": "The digital fingerprint (SHA-256 hash) does not match the initial acquisition value.",
            "severity": "CRITICAL"
        })

    # 2. Critical Vulnerabilities
    vulns_count = db.query(VulnerabilityFinding).filter(
        VulnerabilityFinding.job_id == job_id,
        VulnerabilityFinding.risk_level.in_(["Critical", "High"])
    ).count()
    if vulns_count > 0:
        flags.append({
            "id": "CRITICAL_VULNERABILITIES_FOUND",
            "title": "Critical/High Vulnerabilities Mapped",
            "description": f"Found {vulns_count} high-severity CVE vulnerability mappings on target hosts.",
            "severity": "HIGH"
        })

    # 3. Unauthorized Access Attempts
    unauth_count = db.query(ChainOfCustody).filter(
        ChainOfCustody.job_id == job_id,
        ChainOfCustody.event == "UNAUTHORIZED_ACCESS_ATTEMPT"
    ).count()
    if unauth_count > 0:
        flags.append({
            "id": "UNAUTHORIZED_ACCESS_DETECTED",
            "title": "Unauthorized Access Attempts",
            "description": f"Blocked {unauth_count} access attempts to this evidence by unauthorized users.",
            "severity": "HIGH"
        })

    # 4. Insecure Ports Excluded
    scans = db.query(ScanResult).filter(
        ScanResult.job_id == job_id,
        ScanResult.status == "completed"
    ).all()
    
    insecure_ports = {21: "FTP", 23: "Telnet", 445: "SMB", 3389: "RDP"}
    found_insecure = []
    for s in scans:
        if s.result_json and "hosts" in s.result_json:
            for host in s.result_json["hosts"]:
                for port_info in host.get("ports", []):
                    p = port_info.get("port")
                    if p in insecure_ports:
                        found_insecure.append(f"Port {p} ({insecure_ports[p]})")

    if found_insecure:
        flags.append({
            "id": "INSECURE_PORTS_EXPOSED",
            "title": "Insecure Management Ports Exposed",
            "description": f"Discovered open legacy/insecure management ports: {', '.join(set(found_insecure))}.",
            "severity": "MEDIUM"
        })

    return flags

def generate_attack_hypotheses(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """
    Generates natural-language attack path scenarios based on discovered open ports and CVEs
    """
    hypotheses = []
    
    vulns = db.query(VulnerabilityFinding).filter(
        VulnerabilityFinding.job_id == job_id
    ).all()

    if not vulns:
        # Fallback if no vulnerabilities but some ports are open
        scans = db.query(ScanResult).filter(
            ScanResult.job_id == job_id,
            ScanResult.status == "completed"
        ).all()
        
        has_ports = False
        for s in scans:
            if s.result_json and "hosts" in s.result_json:
                for host in s.result_json["hosts"]:
                    if host.get("ports"):
                        has_ports = True
                        break
        
        if has_ports:
            hypotheses.append({
                "scenario": "Initial Reconnaissance",
                "probability": "Medium",
                "description": "Target has open network ports exposed. While no matching CVEs were mapped from version banners, exposed services (like SSH/HTTP) are susceptible to credential brute-forcing, configuration errors, or zero-day exploitation."
            })
        return hypotheses

    # Group by service/port to form cohesive scenarios
    service_vulns = {}
    for v in vulns:
        key = f"{v.service or 'unknown'} (Port {v.port or 'unknown'})"
        if key not in service_vulns:
            service_vulns[key] = []
        service_vulns[key].append(v)

    for svc, findings in service_vulns.items():
        highest_score = max([f.cvss_score for f in findings if f.cvss_score is not None] or [0.0])
        cves = [f.cve_id for f in findings if f.cve_id]
        
        prob = "Low"
        if highest_score >= 9.0:
            prob = "Critical"
        elif highest_score >= 7.0:
            prob = "High"
        elif highest_score >= 4.0:
            prob = "Medium"

        desc = (
            f"The exposed service '{svc}' is running a vulnerable version. "
            f"Specifically, we detected {len(findings)} vulnerability/vulnerabilities including {', '.join(cves[:3])}. "
            f"An external adversary could exploit these to execute remote code (RCE), bypass authentication, "
            f"or access sensitive resources. Depending on the service privileges, this could result in immediate "
            f"host compromise and allow lateral movement within the network."
        )
        
        hypotheses.append({
            "scenario": f"Service Exploitation: {svc}",
            "probability": prob,
            "description": desc
        })

    return hypotheses

def generate_correlation_report(db: Session, job_id: str, investigator_id: str) -> Dict[str, Any]:
    """
    Executes a complete correlation analysis and returns the payload to be stored
    """
    timeline = build_unified_timeline(db, job_id)
    score = calculate_risk_score(db, job_id)
    flags = detect_high_risk_flags(db, job_id)
    hypotheses = generate_attack_hypotheses(db, job_id)

    # Format timeline timestamps as string for JSON storage
    serializable_timeline = []
    for item in timeline:
        item_copy = item.copy()
        if isinstance(item_copy.get("timestamp"), datetime):
            item_copy["timestamp"] = item_copy["timestamp"].isoformat()
        serializable_timeline.append(item_copy)

    return {
        "score": score,
        "timeline": serializable_timeline,
        "flags": flags,
        "attack_hypotheses": hypotheses,
        "analyzed_at": datetime.utcnow().isoformat(),
        "generated_by": investigator_id
    }
