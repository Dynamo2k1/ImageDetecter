"""
WHOIS Lookup Service
Retrieves domain registration information including registrar, owner,
creation/expiry dates, and nameservers using python-whois.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _try_import_whois():
    try:
        import whois
        return whois
    except ImportError:
        raise RuntimeError(
            "python-whois is not installed. Run: pip install python-whois"
        )


def _format_date(d) -> Optional[str]:
    """Convert datetime or list of datetimes to ISO string."""
    if d is None:
        return None
    if isinstance(d, list):
        d = d[0] if d else None
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.isoformat()
    return str(d)


def run_whois_lookup(domain: str) -> Dict[str, Any]:
    """
    Perform a WHOIS lookup for the given domain.
    Returns structured registrar, dates, nameservers, and status info.
    """
    whois_mod = _try_import_whois()

    logger.info(f"Starting WHOIS lookup for: {domain}")

    try:
        w = whois_mod.whois(domain)
    except Exception as e:
        logger.error(f"WHOIS lookup failed for {domain}: {str(e)}")
        return {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "raw": None,
        }

    # Normalize nameservers
    nameservers = w.name_servers
    if nameservers:
        if isinstance(nameservers, str):
            nameservers = [nameservers]
        nameservers = [ns.lower() for ns in nameservers]
    else:
        nameservers = []

    # Status
    status = w.status
    if isinstance(status, str):
        status = [status]
    elif not status:
        status = []

    # Compute domain age if creation_date available
    created = _format_date(w.creation_date)
    expires = _format_date(w.expiration_date)
    updated = _format_date(w.updated_date)

    domain_age_days = None
    if w.creation_date:
        creation_dt = w.creation_date if isinstance(w.creation_date, datetime) else (
            w.creation_date[0] if isinstance(w.creation_date, list) else None
        )
        if creation_dt and isinstance(creation_dt, datetime):
            domain_age_days = (datetime.utcnow() - creation_dt.replace(tzinfo=None)).days

    # Days until expiry
    days_until_expiry = None
    if w.expiration_date:
        expiry_dt = w.expiration_date if isinstance(w.expiration_date, datetime) else (
            w.expiration_date[0] if isinstance(w.expiration_date, list) else None
        )
        if expiry_dt and isinstance(expiry_dt, datetime):
            days_until_expiry = (expiry_dt.replace(tzinfo=None) - datetime.utcnow()).days

    result = {
        "domain": domain,
        "timestamp": datetime.now().isoformat(),
        "registrar": w.registrar,
        "registrant_name": w.get("registrant_name") or w.get("name"),
        "registrant_org": w.get("org"),
        "registrant_country": w.get("country"),
        "creation_date": created,
        "expiration_date": expires,
        "updated_date": updated,
        "domain_age_days": domain_age_days,
        "days_until_expiry": days_until_expiry,
        "nameservers": nameservers,
        "status": status,
        "emails": list(w.emails) if isinstance(w.emails, (list, set)) else ([w.emails] if w.emails else []),
        "dnssec": w.get("dnssec", "Unknown"),
    }

    logger.info(f"WHOIS lookup completed for {domain}.")
    return result
