"""
HTTP Headers Analysis Service
Fetches HTTP response headers from a target URL and analyzes them
for security posture (HSTS, CSP, X-Frame-Options, Referrer-Policy, etc.)
"""
import logging
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# --- Security Header Definitions ---
SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "description": "Enforces HTTPS connections (HSTS)",
        "severity_if_missing": "High"
    },
    "Content-Security-Policy": {
        "description": "Controls which resources can be loaded (XSS mitigation)",
        "severity_if_missing": "High"
    },
    "X-Frame-Options": {
        "description": "Prevents clickjacking attacks",
        "severity_if_missing": "Medium"
    },
    "X-Content-Type-Options": {
        "description": "Prevents MIME-sniffing attacks",
        "severity_if_missing": "Medium"
    },
    "Referrer-Policy": {
        "description": "Controls referrer information in requests",
        "severity_if_missing": "Low"
    },
    "Permissions-Policy": {
        "description": "Controls browser feature access",
        "severity_if_missing": "Low"
    },
    "X-XSS-Protection": {
        "description": "Legacy XSS filter (deprecated, but still checked)",
        "severity_if_missing": "Informational"
    },
    "Cache-Control": {
        "description": "Prevents sensitive data caching",
        "severity_if_missing": "Low"
    },
    "Cross-Origin-Embedder-Policy": {
        "description": "Prevents cross-origin resource isolation bypass",
        "severity_if_missing": "Low"
    },
    "Cross-Origin-Opener-Policy": {
        "description": "Prevents cross-origin window attacks",
        "severity_if_missing": "Low"
    },
}

SENSITIVE_HEADERS = [
    "Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version",
    "X-Generator", "X-Drupal-Cache", "X-Varnish", "Via",
]


def _compute_security_grade(missing_high: int, missing_medium: int, missing_low: int) -> str:
    """Compute an A-F security grade based on missing headers."""
    if missing_high >= 2:
        return "F"
    if missing_high == 1 and missing_medium >= 1:
        return "D"
    if missing_high == 1:
        return "C"
    if missing_medium >= 2:
        return "C"
    if missing_medium == 1:
        return "B"
    if missing_low >= 3:
        return "B"
    return "A"


def run_http_header_analysis(target: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Fetch HTTP headers from target and analyze security posture.
    Automatically tries HTTPS first, falls back to HTTP.
    """
    # Ensure we have a proper URL
    if not target.startswith(("http://", "https://")):
        target_url = f"https://{target}"
        fallback_url = f"http://{target}"
    else:
        target_url = target
        fallback_url = None

    logger.info(f"Analyzing HTTP headers for: {target_url}")

    headers_dict: Dict[str, str] = {}
    status_code: Optional[int] = None
    final_url: str = target_url
    redirect_chain: List[str] = []
    error: Optional[str] = None
    used_https = target_url.startswith("https://")

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "FEAS-Recon/2.0 (Authorized Security Assessment)"}
        ) as client:
            resp = client.get(target_url)
            status_code = resp.status_code
            headers_dict = dict(resp.headers)
            final_url = str(resp.url)
            # Capture redirect chain
            for r in resp.history:
                redirect_chain.append(str(r.url))
    except Exception as e:
        logger.warning(f"HTTPS request failed for {target_url}: {e}. Trying HTTP fallback.")
        if fallback_url:
            try:
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    resp = client.get(fallback_url)
                    status_code = resp.status_code
                    headers_dict = dict(resp.headers)
                    final_url = str(resp.url)
                    used_https = False
            except Exception as e2:
                error = str(e2)
                logger.error(f"HTTP fallback also failed: {e2}")
        else:
            error = str(e)

    # Analyze security headers
    present_security: List[Dict] = []
    missing_security: List[Dict] = []
    missing_high = missing_medium = missing_low = 0

    for header_name, meta in SECURITY_HEADERS.items():
        # Case-insensitive check
        value = next(
            (v for k, v in headers_dict.items() if k.lower() == header_name.lower()),
            None
        )
        if value:
            present_security.append({
                "header": header_name,
                "value": value,
                "description": meta["description"]
            })
        else:
            sev = meta["severity_if_missing"]
            missing_security.append({
                "header": header_name,
                "description": meta["description"],
                "severity": sev
            })
            if sev == "High":
                missing_high += 1
            elif sev == "Medium":
                missing_medium += 1
            elif sev == "Low":
                missing_low += 1

    # Find sensitive information-disclosing headers
    sensitive_found: List[Dict] = []
    for s_header in SENSITIVE_HEADERS:
        value = next(
            (v for k, v in headers_dict.items() if k.lower() == s_header.lower()),
            None
        )
        if value:
            sensitive_found.append({"header": s_header, "value": value})

    grade = _compute_security_grade(missing_high, missing_medium, missing_low)

    result = {
        "target": target,
        "final_url": final_url,
        "timestamp": datetime.now().isoformat(),
        "status_code": status_code,
        "used_https": used_https,
        "redirect_chain": redirect_chain,
        "error": error,
        "security_grade": grade,
        "all_headers": headers_dict,
        "security_headers": {
            "present": present_security,
            "missing": missing_security,
        },
        "sensitive_headers": sensitive_found,
        "summary": {
            "total_headers": len(headers_dict),
            "security_headers_present": len(present_security),
            "security_headers_missing": len(missing_security),
            "missing_high": missing_high,
            "missing_medium": missing_medium,
            "missing_low": missing_low,
            "sensitive_info_disclosures": len(sensitive_found),
        }
    }

    logger.info(f"HTTP header analysis complete for {target}: Grade {grade}")
    return result
