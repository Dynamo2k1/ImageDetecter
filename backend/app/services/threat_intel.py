"""
Threat Intelligence IoC Lookup Service
Checks IPs, domains, and hashes against known threat intelligence sources.
Supports:
 - Offline built-in known malicious IP/domain lists (no API key needed)
 - AbuseIPDB (if ABUSEIPDB_API_KEY is configured)
 - VirusTotal basic lookup (if VT_API_KEY is configured)
"""
import logging
import hashlib
import ipaddress
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# --- Built-in Known Bad IPs (sample known C2/scanner IPs from public feeds) ---
# In production this would be loaded from a regularly-updated threat feed file
KNOWN_MALICIOUS_IPS = {
    "185.220.101.1": "Tor exit node (dan.me.uk)",
    "185.220.101.34": "Tor exit node",
    "45.142.212.100": "Known C2 infrastructure",
    "194.165.16.77": "Known mass scanner",
    "80.82.77.33": "Shodan scanner (shodan.io)",
    "80.82.77.139": "Shodan scanner (shodan.io)",
    "198.20.69.74": "Shodan scanner",
    "198.20.69.98": "Shodan scanner",
    "162.142.125.0": "Censys scanner",
    "162.142.125.1": "Censys scanner",
}

# --- Built-in Known Bad Domains (samples from public phishing/malware feeds) ---
KNOWN_MALICIOUS_DOMAINS = {
    "malware.wicar.org": "Known malware test site",
    "eicar.org": "EICAR malware test domain",
    "phishing-test.example.com": "Phishing test",
}

# Known suspicious TLDs (high-risk but not necessarily malicious)
SUSPICIOUS_TLDS = [".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".click", ".download"]


def _detect_ioc_type(ioc: str) -> str:
    """Detect whether an IoC is an IP, domain, or hash."""
    # Check for IP
    try:
        ipaddress.ip_address(ioc)
        return "ip"
    except ValueError:
        pass
    # Check for hash (MD5=32, SHA1=40, SHA256=64)
    if len(ioc) in (32, 40, 64) and all(c in "0123456789abcdefABCDEF" for c in ioc):
        return "hash"
    # Default to domain
    return "domain"


def _check_offline(ioc: str, ioc_type: str) -> Dict[str, Any]:
    """Check IoC against built-in offline lists."""
    findings = []
    risk_score = 0

    if ioc_type == "ip":
        if ioc in KNOWN_MALICIOUS_IPS:
            findings.append({
                "source": "FEAS Offline Feed",
                "verdict": "Malicious",
                "detail": KNOWN_MALICIOUS_IPS[ioc]
            })
            risk_score = 85
        else:
            findings.append({"source": "FEAS Offline Feed", "verdict": "Not found in offline database", "detail": None})

    elif ioc_type == "domain":
        ioc_lower = ioc.lower()
        if ioc_lower in KNOWN_MALICIOUS_DOMAINS:
            findings.append({
                "source": "FEAS Offline Feed",
                "verdict": "Malicious",
                "detail": KNOWN_MALICIOUS_DOMAINS[ioc_lower]
            })
            risk_score = 80
        else:
            # Check suspicious TLD
            for tld in SUSPICIOUS_TLDS:
                if ioc_lower.endswith(tld):
                    findings.append({
                        "source": "FEAS Offline Feed",
                        "verdict": "Suspicious TLD",
                        "detail": f"Domain uses high-risk TLD: {tld}"
                    })
                    risk_score = max(risk_score, 35)
                    break

            if not findings:
                findings.append({"source": "FEAS Offline Feed", "verdict": "Not found in offline database", "detail": None})

    elif ioc_type == "hash":
        findings.append({"source": "FEAS Offline Feed", "verdict": "Hash lookup requires online source", "detail": "Configure VT_API_KEY for hash lookups"})

    return {"findings": findings, "risk_score": risk_score}


def _check_abuseipdb(ip: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Query AbuseIPDB v2 API for IP reputation."""
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": True},
                headers={"Key": api_key, "Accept": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return {
                    "source": "AbuseIPDB",
                    "verdict": "Malicious" if data.get("abuseConfidenceScore", 0) >= 50 else "Suspicious" if data.get("abuseConfidenceScore", 0) > 0 else "Clean",
                    "detail": f"Abuse confidence: {data.get('abuseConfidenceScore')}%, "
                              f"Reports: {data.get('totalReports')}, "
                              f"ISP: {data.get('isp')}, "
                              f"Country: {data.get('countryCode')}",
                    "abuse_score": data.get("abuseConfidenceScore", 0),
                }
    except Exception as e:
        logger.warning(f"AbuseIPDB lookup failed: {e}")
    return None


def _check_virustotal(ioc: str, ioc_type: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Query VirusTotal v3 API for IP, domain, or hash reputation."""
    try:
        if ioc_type == "ip":
            endpoint = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}"
        elif ioc_type == "domain":
            endpoint = f"https://www.virustotal.com/api/v3/domains/{ioc}"
        elif ioc_type == "hash":
            endpoint = f"https://www.virustotal.com/api/v3/files/{ioc}"
        else:
            return None

        with httpx.Client(timeout=15) as client:
            resp = client.get(
                endpoint,
                headers={"x-apikey": api_key}
            )
            if resp.status_code == 200:
                attrs = resp.json().get("data", {}).get("attributes", {})
                stats = attrs.get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                total = sum(stats.values())

                verdict = "Clean"
                if malicious >= 5:
                    verdict = "Malicious"
                elif malicious > 0 or suspicious > 0:
                    verdict = "Suspicious"

                return {
                    "source": "VirusTotal",
                    "verdict": verdict,
                    "detail": f"{malicious}/{total} engines flagged as malicious, {suspicious} suspicious",
                    "malicious_count": malicious,
                    "suspicious_count": suspicious,
                    "total_engines": total,
                }
            elif resp.status_code == 404:
                return {"source": "VirusTotal", "verdict": "Not found", "detail": "No data for this IoC in VirusTotal"}
    except Exception as e:
        logger.warning(f"VirusTotal lookup failed: {e}")
    return None


def run_threat_intel_lookup(ioc: str, abuseipdb_key: Optional[str] = None, vt_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Look up an IoC (IP, domain, or file hash) against threat intelligence sources.
    Always runs offline check; runs online checks only if API keys are provided.
    """
    logger.info(f"Starting threat intel lookup for IoC: {ioc}")

    ioc_type = _detect_ioc_type(ioc.strip())
    all_findings: List[Dict] = []
    overall_risk_score = 0

    # 1. Offline check (always)
    offline_result = _check_offline(ioc, ioc_type)
    all_findings.extend(offline_result["findings"])
    overall_risk_score = max(overall_risk_score, offline_result["risk_score"])

    # 2. AbuseIPDB (if key + IP)
    if abuseipdb_key and ioc_type == "ip":
        abuseipdb_result = _check_abuseipdb(ioc, abuseipdb_key)
        if abuseipdb_result:
            all_findings.append(abuseipdb_result)
            if abuseipdb_result.get("abuse_score", 0) > overall_risk_score:
                overall_risk_score = abuseipdb_result["abuse_score"]

    # 3. VirusTotal (if key)
    if vt_key:
        vt_result = _check_virustotal(ioc, ioc_type, vt_key)
        if vt_result:
            all_findings.append(vt_result)
            if vt_result.get("verdict") == "Malicious":
                overall_risk_score = max(overall_risk_score, 90)
            elif vt_result.get("verdict") == "Suspicious":
                overall_risk_score = max(overall_risk_score, 50)

    # Determine overall verdict
    if overall_risk_score >= 75:
        overall_verdict = "Malicious"
    elif overall_risk_score >= 35:
        overall_verdict = "Suspicious"
    else:
        overall_verdict = "Clean"

    result = {
        "ioc": ioc,
        "ioc_type": ioc_type,
        "timestamp": datetime.now().isoformat(),
        "overall_verdict": overall_verdict,
        "risk_score": overall_risk_score,
        "findings": all_findings,
        "sources_checked": [f["source"] for f in all_findings],
        "online_sources_available": {
            "abuseipdb": bool(abuseipdb_key),
            "virustotal": bool(vt_key),
        }
    }

    logger.info(f"Threat intel lookup complete for {ioc}: verdict={overall_verdict}, score={overall_risk_score}")
    return result
