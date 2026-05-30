import os
import time
import httpx
import json
import logging
from typing import List, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache keyed by "service-version"
_cache: Dict[str, List[Dict[str, Any]]] = {}

# Time tracking for rate limiting (max 5 requests per 30 seconds -> 6s delay between requests)
_last_request_time = 0.0

def _rate_limit():
    """Enforces a rate-limiting delay between NVD API requests to stay within limits"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    # 6 seconds delay secures max 5 requests per 30 seconds
    if elapsed < 6.0:
        sleep_time = 6.0 - elapsed
        logger.debug(f"Rate limiting NVD query: sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)
    _last_request_time = time.time()

def get_local_fallback(service: str, version: str) -> List[Dict[str, Any]]:
    """Loads vulnerabilities from offline data matching service/version keywords"""
    results = []
    try:
        # Resolve paths dynamically
        fallback_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "known_vulns.json"))
        if not os.path.exists(fallback_path):
            fallback_path = os.path.abspath(os.path.join("data", "known_vulns.json"))
        
        if os.path.exists(fallback_path):
            with open(fallback_path, "r") as f:
                vulns = json.load(f)
                
            for v in vulns:
                v_service = v.get("service", "").lower()
                v_version = v.get("version_contains", "").lower()
                
                # Check if service matches and version matches (if specified)
                service_match = v_service in service.lower() or service.lower() in v_service
                version_match = not version or v_version in version.lower() or version.lower() in v_version
                
                if service_match and version_match:
                    results.append({
                        "cve_id": v.get("cve_id"),
                        "description": v.get("description"),
                        "cvss_score": v.get("cvss_score"),
                        "severity": v.get("severity"),
                        "risk_level": v.get("risk_level"),
                        "nvd_url": f"https://nvd.nist.gov/vuln/detail/{v.get('cve_id')}"
                    })
    except Exception as e:
        logger.error(f"Known vulns fallback loading failed: {str(e)}")
    return results

def query_nvd_api(keyword: str) -> List[Dict[str, Any]]:
    """Queries the NIST NVD CVE 2.0 API with a specific keyword query"""
    # Enforce rate limit
    _rate_limit()
    
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {
        "keywordSearch": keyword,
        "resultsPerPage": 5
    }
    
    headers = {
        "User-Agent": "FEAS Digital Forensics Platform (Agentic Mapping Service)"
    }
    
    # Apply optional NVD API key
    if settings.NVD_API_KEY:
        headers["apiKey"] = settings.NVD_API_KEY
        
    try:
        logger.info(f"Querying NVD API: {url} with keyword: '{keyword}'")
        with httpx.Client(timeout=8.0) as client:
            response = client.get(url, params=params, headers=headers)
            
        if response.status_code != 200:
            logger.warning(f"NVD API returned non-200 status: {response.status_code}")
            return []
            
        data = response.json()
        findings = []
        vulnerabilities = data.get("vulnerabilities", [])
        
        for v in vulnerabilities:
            cve = v.get("cve", {})
            cve_id = cve.get("id")
            
            # Extract English description
            desc_val = ""
            for desc in cve.get("descriptions", []):
                if desc.get("lang") == "en":
                    desc_val = desc.get("value", "")
                    break
                    
            # Extract CVSS score and severity
            cvss_score = None
            severity = "Informational"
            metrics = cve.get("metrics", {})
            
            cvss_data = None
            if "cvssMetricV31" in metrics:
                cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
            elif "cvssMetricV30" in metrics:
                cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {})
            elif "cvssMetricV2" in metrics:
                cvss_data = metrics["cvssMetricV2"][0].get("cvssData", {})
                
            if cvss_data:
                cvss_score = cvss_data.get("baseScore")
                severity = cvss_data.get("baseSeverity", "Informational").capitalize()
                
            # Assign internal risk level
            if cvss_score is None:
                risk_level = "Informational"
                severity = "Informational"
            elif cvss_score >= 9.0:
                risk_level = "Critical"
            elif cvss_score >= 7.0:
                risk_level = "High"
            elif cvss_score >= 4.0:
                risk_level = "Medium"
            else:
                risk_level = "Low"
                
            findings.append({
                "cve_id": cve_id,
                "description": desc_val,
                "cvss_score": cvss_score,
                "severity": severity,
                "risk_level": risk_level,
                "nvd_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            })
            
        return findings
    except Exception as e:
        logger.error(f"NVD API request failed: {str(e)}")
        return []

def map_vulnerabilities(scan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Map open ports and services/versions discovered during network scan to CVEs.
    Caches results to avoid redundant API queries.
    """
    mapped_findings = []
    
    for host in scan_result.get("hosts", []):
        for port_info in host.get("ports", []):
            service = port_info.get("service", "")
            version = port_info.get("version", "")
            port = port_info.get("port")
            
            # Skip if service not defined
            if not service:
                continue
                
            cache_key = f"{service}-{version}"
            
            # Check Cache
            if cache_key in _cache:
                logger.info(f"Loaded CVE findings for {cache_key} from cache.")
                service_findings = _cache[cache_key]
            else:
                # Resolve CVEs
                service_findings = []
                
                # Check NVD API if internet access is available and we have a version
                if version:
                    query_keyword = f"{service} {version}"
                    service_findings = query_nvd_api(query_keyword)
                    
                # Fallback to local known_vulns if NVD query returned nothing
                if not service_findings:
                    logger.info(f"No NVD results for query '{service} {version}'. Falling back to local offline known_vulns.")
                    service_findings = get_local_fallback(service, version)
                    
                # Save to cache
                _cache[cache_key] = service_findings
                
            # Append findings with port details
            for f in service_findings:
                mapped_findings.append({
                    "port": port,
                    "service": service,
                    "version": version,
                    "cve_id": f.get("cve_id"),
                    "description": f.get("description"),
                    "cvss_score": f.get("cvss_score"),
                    "severity": f.get("severity"),
                    "risk_level": f.get("risk_level"),
                    "nvd_url": f.get("nvd_url")
                })
                
    return mapped_findings
