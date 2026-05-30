"""
SSL/TLS Certificate Inspector Service
Inspects SSL/TLS certificates for a given hostname:port.
Extracts certificate chain, cipher suite, validity, SANs, and known issues.
Uses Python's built-in ssl module + cryptography library.
"""
import ssl
import socket
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def _parse_cert_dates(cert: dict) -> tuple:
    """Parse notBefore and notAfter from ssl cert dict."""
    try:
        not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        return not_before, not_after
    except Exception:
        return None, None


def _extract_sans(cert: dict) -> List[str]:
    """Extract Subject Alternative Names from ssl cert dict."""
    sans = []
    for ext_type, entries in cert.get("subjectAltName", []):
        if ext_type.lower() == "dns":
            sans.append(entries)
    return sans


def _check_issues(cert: dict, not_before: datetime, not_after: datetime, hostname: str, sans: List[str]) -> List[Dict]:
    """Identify potential certificate issues."""
    issues = []
    now = datetime.utcnow()

    if not_after and not_after < now:
        issues.append({"severity": "Critical", "issue": "Certificate is EXPIRED", "detail": f"Expired on {not_after.isoformat()}"})

    if not_after:
        days_remaining = (not_after - now).days
        if 0 < days_remaining <= 30:
            issues.append({"severity": "High", "issue": "Certificate expires soon", "detail": f"{days_remaining} days remaining"})

    if not_before and not_before > now:
        issues.append({"severity": "High", "issue": "Certificate is not yet valid", "detail": f"Valid from {not_before.isoformat()}"})

    # Check if hostname is covered
    hostname_covered = any(
        hostname == san or
        (san.startswith("*.") and hostname.endswith(san[1:]))
        for san in sans
    )
    if sans and not hostname_covered:
        issues.append({"severity": "High", "issue": "Hostname not in SAN list", "detail": f"'{hostname}' not covered by any SAN"})

    return issues


def run_ssl_inspection(hostname: str, port: int = 443, timeout: int = 10) -> Dict[str, Any]:
    """
    Inspect SSL/TLS certificate and connection parameters for a host.
    Returns certificate details, cipher suite, SANs, and issue list.
    """
    logger.info(f"Starting SSL inspection for {hostname}:{port}")

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_OPTIONAL

    cert_dict: Optional[dict] = None
    cipher_info: Optional[tuple] = None
    tls_version: Optional[str] = None
    peer_cert_chain: List[dict] = []
    error: Optional[str] = None

    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                tls_version = ssock.version()
                cipher_info = ssock.cipher()
                cert_dict = ssock.getpeercert()
                # Get DER cert for chain info
                der_cert = ssock.getpeercert(binary_form=True)
    except ssl.SSLError as e:
        error = f"SSL Error: {str(e)}"
        logger.error(f"SSL Error for {hostname}:{port}: {e}")
    except socket.timeout:
        error = f"Connection timed out after {timeout}s"
        logger.error(f"Timeout connecting to {hostname}:{port}")
    except ConnectionRefusedError:
        error = f"Connection refused on port {port}"
        logger.error(f"Connection refused for {hostname}:{port}")
    except Exception as e:
        error = str(e)
        logger.error(f"SSL inspection failed for {hostname}:{port}: {e}")

    # Parse certificate details
    subject: Dict[str, str] = {}
    issuer: Dict[str, str] = {}
    not_before_iso: Optional[str] = None
    not_after_iso: Optional[str] = None
    days_remaining: Optional[int] = None
    sans: List[str] = []
    issues: List[Dict] = []
    serial_number: Optional[str] = None

    if cert_dict:
        for rdn in cert_dict.get("subject", []):
            for key, val in rdn:
                subject[key] = val
        for rdn in cert_dict.get("issuer", []):
            for key, val in rdn:
                issuer[key] = val

        not_before, not_after = _parse_cert_dates(cert_dict)
        if not_before:
            not_before_iso = not_before.isoformat()
        if not_after:
            not_after_iso = not_after.isoformat()
            days_remaining = (not_after - datetime.utcnow()).days

        sans = _extract_sans(cert_dict)
        serial_number = cert_dict.get("serialNumber")
        issues = _check_issues(cert_dict, not_before, not_after, hostname, sans)

    # Cipher suite analysis
    cipher_name = cipher_info[0] if cipher_info else None
    cipher_bits = cipher_info[2] if cipher_info else None

    # Flag weak ciphers
    weak_ciphers_keywords = ["RC4", "DES", "3DES", "NULL", "EXPORT", "ANON", "MD5"]
    is_weak_cipher = any(kw in (cipher_name or "") for kw in weak_ciphers_keywords)
    if is_weak_cipher:
        issues.append({"severity": "High", "issue": f"Weak cipher suite in use: {cipher_name}", "detail": "RC4/DES/3DES/NULL/EXPORT ciphers are insecure"})

    # Flag old TLS versions
    if tls_version in ("TLSv1", "TLSv1.1", "SSLv2", "SSLv3"):
        issues.append({"severity": "High", "issue": f"Outdated TLS version: {tls_version}", "detail": "TLS 1.0 and 1.1 are deprecated (RFC 8996)"})

    result = {
        "hostname": hostname,
        "port": port,
        "timestamp": datetime.now().isoformat(),
        "error": error,
        "tls_version": tls_version,
        "cipher_suite": {
            "name": cipher_name,
            "protocol": cipher_info[1] if cipher_info else None,
            "bits": cipher_bits,
            "is_weak": is_weak_cipher,
        },
        "certificate": {
            "subject": subject,
            "issuer": issuer,
            "serial_number": serial_number,
            "not_before": not_before_iso,
            "not_after": not_after_iso,
            "days_remaining": days_remaining,
            "subject_alt_names": sans,
        },
        "issues": issues,
        "summary": {
            "tls_ok": tls_version in ("TLSv1.2", "TLSv1.3"),
            "cert_valid": not any(i["severity"] in ("Critical", "High") for i in issues),
            "issue_count": len(issues),
        }
    }

    logger.info(f"SSL inspection complete for {hostname}:{port}. Issues found: {len(issues)}")
    return result
