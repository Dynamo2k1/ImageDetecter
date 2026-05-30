"""
GeoIP & ASN Lookup Service
Uses the free ip-api.com service (no API key required, rate limit: 45 req/min)
to resolve geographic and network information for an IP address.
Falls back gracefully if the service is unavailable.
"""
import logging
import httpx
import socket
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

IP_API_URL = "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query"


def _resolve_hostname_to_ip(target: str) -> Optional[str]:
    """If target is a domain, resolve it to an IP address."""
    try:
        import ipaddress
        ipaddress.ip_address(target)  # Will succeed if already an IP
        return target
    except ValueError:
        # It's a hostname
        try:
            return socket.gethostbyname(target)
        except Exception:
            return None


def run_geoip_lookup(target: str) -> Dict[str, Any]:
    """
    Look up geographic and ASN information for an IP address or hostname.
    Returns country, city, ISP, ASN, and proxy/VPN detection flags.
    """
    logger.info(f"Starting GeoIP lookup for: {target}")

    # Resolve hostname to IP first
    ip = _resolve_hostname_to_ip(target)
    if not ip:
        return {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "error": f"Could not resolve '{target}' to an IP address.",
            "data": None
        }

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(IP_API_URL.format(ip=ip))
            data = resp.json()
    except Exception as e:
        logger.error(f"GeoIP lookup failed for {ip}: {e}")
        return {
            "target": target,
            "resolved_ip": ip,
            "timestamp": datetime.now().isoformat(),
            "error": f"GeoIP service request failed: {str(e)}",
            "data": None
        }

    if data.get("status") == "fail":
        return {
            "target": target,
            "resolved_ip": ip,
            "timestamp": datetime.now().isoformat(),
            "error": data.get("message", "GeoIP lookup failed"),
            "data": None
        }

    # Flag suspicious indicators
    risk_flags = []
    if data.get("proxy"):
        risk_flags.append("Proxy/VPN detected")
    if data.get("hosting"):
        risk_flags.append("Hosting/datacenter IP (not residential)")
    if data.get("mobile"):
        risk_flags.append("Mobile carrier IP")

    result = {
        "target": target,
        "resolved_ip": ip,
        "timestamp": datetime.now().isoformat(),
        "error": None,
        "data": {
            "ip": data.get("query"),
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("regionName"),
            "region_code": data.get("region"),
            "city": data.get("city"),
            "zip": data.get("zip"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "organization": data.get("org"),
            "asn": data.get("as"),
            "asn_name": data.get("asname"),
            "reverse_dns": data.get("reverse"),
            "is_mobile": data.get("mobile", False),
            "is_proxy": data.get("proxy", False),
            "is_hosting": data.get("hosting", False),
        },
        "risk_flags": risk_flags,
    }

    logger.info(f"GeoIP lookup completed for {target} ({ip}): {data.get('country', 'Unknown')}")
    return result
