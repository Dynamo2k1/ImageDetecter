"""
DNS Reconnaissance Service
Resolves DNS records (A, AAAA, MX, NS, TXT, SOA, CNAME) for a given domain.
Uses dnspython for resolution with timeout and error handling.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def _try_import_dns():
    try:
        import dns.resolver
        import dns.exception
        return dns.resolver, dns.exception
    except ImportError:
        raise RuntimeError(
            "dnspython is not installed. Run: pip install dnspython"
        )


def run_dns_recon(domain: str) -> Dict[str, Any]:
    """
    Perform a full DNS reconnaissance against the given domain.
    Returns all common record types with raw values and metadata.
    """
    resolver_mod, dns_exception = _try_import_dns()

    logger.info(f"Starting DNS recon for domain: {domain}")

    resolver = resolver_mod.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 10

    record_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]
    records: Dict[str, List[str]] = {}
    errors: Dict[str, str] = {}

    for rtype in record_types:
        try:
            answers = resolver.resolve(domain, rtype, raise_on_no_answer=False)
            rdata_list = []
            if answers:
                for rdata in answers:
                    rdata_list.append(str(rdata))
            records[rtype] = rdata_list
        except dns_exception.NXDOMAIN:
            errors[rtype] = "NXDOMAIN — domain does not exist"
            records[rtype] = []
        except dns_exception.NoAnswer:
            records[rtype] = []
        except dns_exception.Timeout:
            errors[rtype] = "DNS query timed out"
            records[rtype] = []
        except Exception as e:
            errors[rtype] = str(e)
            records[rtype] = []

    # Summarize
    total_records = sum(len(v) for v in records.values())
    has_ipv6 = bool(records.get("AAAA"))
    has_mail = bool(records.get("MX"))
    has_spf = any("v=spf1" in r for r in records.get("TXT", []))
    has_dmarc = any("v=DMARC1" in r for r in records.get("TXT", []))

    result = {
        "domain": domain,
        "timestamp": datetime.now().isoformat(),
        "records": records,
        "errors": errors,
        "summary": {
            "total_records_found": total_records,
            "has_ipv6": has_ipv6,
            "has_mail_exchanger": has_mail,
            "has_spf_record": has_spf,
            "has_dmarc_record": has_dmarc,
        }
    }

    logger.info(f"DNS recon completed for {domain}: {total_records} records found.")
    return result
