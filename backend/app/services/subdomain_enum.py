"""
Subdomain Enumeration Service
Brute-force discovers subdomains using a built-in wordlist + DNS resolution.
No external API needed — uses dnspython for resolution.
"""
import logging
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# --- Common Subdomain Wordlist (top 200 most common subdomains) ---
COMMON_SUBDOMAINS = [
    "www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2",
    "smtp", "secure", "vpn", "m", "shop", "ftp", "mail2", "test",
    "portal", "dns", "host", "dev", "staging", "api", "admin", "cdn",
    "beta", "mobile", "static", "media", "img", "images", "assets",
    "support", "help", "docs", "forum", "news", "calendar", "dashboard",
    "app", "apps", "cloud", "wiki", "intranet", "corp", "hr", "crm",
    "erp", "git", "svn", "jenkins", "ci", "jira", "confluence", "smtp",
    "pop", "imap", "pop3", "exchange", "owa", "autodiscover", "autoconfig",
    "cpanel", "whm", "webdisk", "ns3", "ns4", "mx", "mx1", "mx2",
    "email", "lists", "chat", "irc", "sip", "voip", "lab", "labs",
    "staging2", "uat", "qa", "preprod", "prod", "demo", "sandbox",
    "monitor", "nagios", "grafana", "kibana", "elastic", "logstash",
    "auth", "sso", "login", "register", "account", "accounts", "pay",
    "payment", "checkout", "store", "ecommerce", "download", "downloads",
    "upload", "uploads", "files", "fileserver", "backup", "archive",
    "old", "new", "dev2", "dev3", "web", "web2", "web3",
    "proxy", "gateway", "firewall", "load", "lb", "health",
    "status", "internal", "external", "partner", "partners", "client",
    "clients", "customer", "customers", "user", "users", "member",
    "members", "community", "social", "share", "collaborate",
    "survey", "events", "careers", "jobs", "hr", "people",
    "marketing", "campaign", "affiliate", "promo", "deals", "sale",
    "analytics", "tracking", "report", "reports", "metrics", "stats",
    "db", "database", "mysql", "postgres", "redis", "mongo", "sql",
    "admin2", "administrator", "root", "superadmin", "system", "sys",
    "control", "panel", "cp", "manage", "manager", "console",
    "api2", "api3", "rest", "graphql", "grpc", "socket", "ws", "wss",
    "push", "notifications", "alerts", "webhook", "hooks", "events2",
    "search", "query", "data", "services", "service", "microservice",
    "k8s", "kubernetes", "docker", "registry", "repo", "repository",
    "artifacts", "packages", "pypi", "npm", "maven",
    "office", "sharepoint", "teams", "meet", "video", "stream",
    "live", "broadcast", "cdn2", "edge", "cache", "assets2",
    "s3", "storage", "blob", "bucket", "fs", "nfs",
    "jump", "bastion", "ssh", "rdp", "vnc", "kvm",
]


def _resolve_subdomain(subdomain: str, domain: str) -> Dict[str, Any]:
    """Attempt to resolve a single subdomain and return result."""
    try:
        import dns.resolver
        import dns.exception
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2
        resolver.lifetime = 3
        fqdn = f"{subdomain}.{domain}"
        answers = resolver.resolve(fqdn, "A", raise_on_no_answer=False)
        ips = [str(r) for r in answers] if answers else []
        if ips:
            return {"subdomain": fqdn, "ips": ips, "status": "resolved"}
    except Exception:
        pass
    return None


def run_subdomain_enum(domain: str, max_workers: int = 30) -> Dict[str, Any]:
    """
    Enumerate subdomains for the given domain using the built-in wordlist.
    Uses concurrent DNS resolution for speed.
    Returns list of discovered subdomains with their resolved IPs.
    """
    try:
        import dns.resolver  # noqa – just check import works
    except ImportError:
        raise RuntimeError("dnspython is not installed. Run: pip install dnspython")

    logger.info(f"Starting subdomain enumeration for: {domain} ({len(COMMON_SUBDOMAINS)} words)")
    start_time = datetime.now()

    discovered: List[Dict[str, Any]] = []
    checked = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_resolve_subdomain, sub, domain): sub
            for sub in COMMON_SUBDOMAINS
        }
        for future in concurrent.futures.as_completed(futures):
            checked += 1
            try:
                res = future.result()
                if res:
                    discovered.append(res)
            except Exception:
                pass

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Subdomain enumeration done for {domain}: {len(discovered)} found in {elapsed:.1f}s")

    return {
        "domain": domain,
        "timestamp": start_time.isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "words_checked": checked,
        "subdomains_found": len(discovered),
        "subdomains": sorted(discovered, key=lambda x: x["subdomain"]),
    }
