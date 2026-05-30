"""
Recon API Router — Red Team Reconnaissance Module
Exposes endpoints for DNS, WHOIS, subdomain enum, HTTP headers,
SSL inspection, GeoIP, and threat intelligence lookups.
All operations are persisted to the recon_results table.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.sql_models import ReconResult, User
from app.api.v1.endpoints.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/recon", tags=["recon"])


# --- Pydantic Schemas ---

class TargetRequest(BaseModel):
    target: str = Field(..., description="Domain or IP address to investigate", example="example.com")
    job_id: Optional[str] = Field(None, description="Associate with an evidence job ID")

class SSLRequest(BaseModel):
    hostname: str = Field(..., description="Hostname to inspect TLS certificate", example="example.com")
    port: int = Field(443, description="Port number", ge=1, le=65535)
    job_id: Optional[str] = None

class ThreatIntelRequest(BaseModel):
    ioc: str = Field(..., description="IP address, domain, or file hash to check", example="8.8.8.8")
    job_id: Optional[str] = None
    abuseipdb_key: Optional[str] = Field(None, description="AbuseIPDB API key (optional)")
    vt_key: Optional[str] = Field(None, description="VirusTotal API key (optional)")

class ReconResultResponse(BaseModel):
    id: int
    recon_type: str
    target: str
    job_id: Optional[str]
    result_json: Optional[dict]
    performed_by: str
    created_at: str

    class Config:
        from_attributes = True


def _save_recon(db: Session, recon_type: str, target: str, result: dict,
                user_id: int, job_id: Optional[str] = None) -> ReconResult:
    """Persist a recon result to the database."""
    record = ReconResult(
        recon_type=recon_type,
        target=target,
        result_json=result,
        performed_by=str(user_id),
        job_id=job_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# --- DNS Recon ---
@router.post("/dns", summary="DNS Record Lookup")
async def dns_recon(
    body: TargetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform a full DNS reconnaissance for the given domain.
    Returns A, AAAA, MX, NS, TXT, SOA, and CNAME records with summary analysis.
    """
    try:
        from app.services.dns_recon import run_dns_recon
        result = run_dns_recon(body.target)
        _save_recon(db, "dns", body.target, result, current_user.id, body.job_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"DNS recon failed for {body.target}: {e}")
        raise HTTPException(status_code=500, detail=f"DNS recon failed: {str(e)}")


# --- WHOIS Lookup ---
@router.post("/whois", summary="WHOIS Domain Lookup")
async def whois_lookup(
    body: TargetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform a WHOIS lookup for a domain.
    Returns registrar, registration/expiry dates, nameservers, and DNSSEC status.
    """
    try:
        from app.services.whois_lookup import run_whois_lookup
        result = run_whois_lookup(body.target)
        _save_recon(db, "whois", body.target, result, current_user.id, body.job_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"WHOIS lookup failed for {body.target}: {e}")
        raise HTTPException(status_code=500, detail=f"WHOIS lookup failed: {str(e)}")


# --- Subdomain Enumeration ---
@router.post("/subdomains", summary="Subdomain Enumeration")
async def subdomain_enum(
    body: TargetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enumerate subdomains for a domain using a built-in wordlist + concurrent DNS resolution.
    This is an active recon technique — only use on authorized targets.
    """
    try:
        from app.services.subdomain_enum import run_subdomain_enum
        result = run_subdomain_enum(body.target)
        _save_recon(db, "subdomain", body.target, result, current_user.id, body.job_id)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Subdomain enum failed for {body.target}: {e}")
        raise HTTPException(status_code=500, detail=f"Subdomain enumeration failed: {str(e)}")


# --- HTTP Header Analysis ---
@router.post("/headers", summary="HTTP Header Security Analysis")
async def http_headers(
    body: TargetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch and analyze HTTP response headers for a target URL or domain.
    Returns a security grade (A-F) and lists present/missing security headers.
    """
    try:
        from app.services.http_headers import run_http_header_analysis
        result = run_http_header_analysis(body.target)
        _save_recon(db, "headers", body.target, result, current_user.id, body.job_id)
        return result
    except Exception as e:
        logger.error(f"HTTP header analysis failed for {body.target}: {e}")
        raise HTTPException(status_code=500, detail=f"HTTP header analysis failed: {str(e)}")


# --- SSL/TLS Certificate Inspector ---
@router.post("/ssl", summary="SSL/TLS Certificate Inspection")
async def ssl_inspection(
    body: SSLRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inspect the TLS certificate and cipher suite for a host:port.
    Checks for expired certs, weak ciphers, hostname mismatches, and old TLS versions.
    """
    try:
        from app.services.ssl_inspector import run_ssl_inspection
        result = run_ssl_inspection(body.hostname, body.port)
        _save_recon(db, "ssl", body.hostname, result, current_user.id, body.job_id)
        return result
    except Exception as e:
        logger.error(f"SSL inspection failed for {body.hostname}: {e}")
        raise HTTPException(status_code=500, detail=f"SSL inspection failed: {str(e)}")


# --- GeoIP & ASN Lookup ---
@router.get("/geoip/{target:path}", summary="GeoIP & ASN Lookup")
async def geoip_lookup(
    target: str,
    job_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Look up geographic and ASN information for an IP address or hostname.
    Detects proxy/VPN/hosting IPs. Uses ip-api.com (free, no key required).
    """
    try:
        from app.services.geoip import run_geoip_lookup
        result = run_geoip_lookup(target)
        _save_recon(db, "geoip", target, result, current_user.id, job_id)
        return result
    except Exception as e:
        logger.error(f"GeoIP lookup failed for {target}: {e}")
        raise HTTPException(status_code=500, detail=f"GeoIP lookup failed: {str(e)}")


# --- Threat Intelligence ---
@router.post("/threat-intel", summary="Threat Intelligence IoC Lookup")
async def threat_intel(
    body: ThreatIntelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Look up an IoC (IP, domain, or file hash) against threat intelligence sources.
    Offline checks always run; AbuseIPDB and VirusTotal checked if API keys provided.
    """
    try:
        from app.services.threat_intel import run_threat_intel_lookup
        from app.core.config import settings
        # Use provided keys or fall back to configured env vars
        abkey = body.abuseipdb_key or getattr(settings, "ABUSEIPDB_API_KEY", None)
        vtkey = body.vt_key or getattr(settings, "VT_API_KEY", None)
        result = run_threat_intel_lookup(body.ioc, abuseipdb_key=abkey, vt_key=vtkey)
        _save_recon(db, "threat_intel", body.ioc, result, current_user.id, body.job_id)
        return result
    except Exception as e:
        logger.error(f"Threat intel lookup failed for {body.ioc}: {e}")
        raise HTTPException(status_code=500, detail=f"Threat intel lookup failed: {str(e)}")


# --- History ---
@router.get("/history", summary="Recon History", response_model=List[ReconResultResponse])
async def recon_history(
    recon_type: Optional[str] = Query(None, description="Filter by recon type"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve past recon results. Optionally filter by recon type
    (dns, whois, subdomain, headers, ssl, geoip, threat_intel).
    """
    query = db.query(ReconResult).filter(ReconResult.performed_by == str(current_user.id))
    if recon_type:
        query = query.filter(ReconResult.recon_type == recon_type)
    records = query.order_by(ReconResult.created_at.desc()).limit(limit).all()
    return [
        ReconResultResponse(
            id=r.id,
            recon_type=r.recon_type,
            target=r.target,
            job_id=r.job_id,
            result_json=r.result_json,
            performed_by=r.performed_by,
            created_at=r.created_at.isoformat() if r.created_at else ""
        ) for r in records
    ]
