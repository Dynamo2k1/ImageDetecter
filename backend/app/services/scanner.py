import nmap
import socket
import ipaddress
import logging
from datetime import datetime
from typing import Dict, Any, List

from app.core.config import settings

logger = logging.getLogger(__name__)

def is_private_target(target: str) -> bool:
    """Check if the target resolves to a private or loopback IP address"""
    try:
        # Resolve target to IP address (works for domains or IPs)
        ip = socket.gethostbyname(target)
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback
    except Exception as e:
        logger.error(f"Failed to resolve target '{target}': {str(e)}")
        # If it cannot be resolved, treat it as private/unsafe by default
        return True

def run_scan(target: str, job_id: str = None) -> Dict[str, Any]:
    """
    Run a controlled network scan (open ports, service banners, OS detection) against a target
    using nmap -sV -O --version-intensity 5
    """
    # 1. Target Validation
    if not settings.ALLOW_INTERNAL_SCAN:
        if is_private_target(target):
            raise ValueError(f"Target '{target}' is a private or loopback IP address, which is prohibited by security policy.")

    # 2. Check if nmap is available
    try:
        nm = nmap.PortScanner()
    except nmap.PortScannerError as e:
        logger.error(f"Nmap binary not found on the host: {str(e)}")
        raise RuntimeError("Nmap binary not found on system. Please run 'apt install nmap' or 'brew install nmap'.")

    logger.info(f"Initiating network scan on target: {target} (job_id: {job_id})")

    # 3. Run Scan
    # Arguments: -sV (Version detection), -O (OS detection), --version-intensity 5 (Aggressive version probe)
    # Timeout is handled via Python or nmap command
    try:
        scan_result = nm.scan(hosts=target, arguments='-sV -O --version-intensity 5', timeout=120)
    except Exception as e:
        logger.error(f"Nmap scan failed: {str(e)}")
        raise RuntimeError(f"Nmap scan failed: {str(e)}")

    # 4. Parse Results
    hosts_list = []
    for ip, host_data in scan_result.get('scan', {}).items():
        hostname = ""
        hostnames = host_data.get('hostnames', [])
        if hostnames:
            hostname = hostnames[0].get('name', '')

        ports_list = []
        # tcp ports
        tcp_data = host_data.get('tcp', {})
        for port, port_data in tcp_data.items():
            ports_list.append({
                "port": int(port),
                "protocol": "tcp",
                "state": port_data.get('state', 'unknown'),
                "service": port_data.get('name', 'unknown'),
                "version": port_data.get('version', '')
            })
        # udp ports
        udp_data = host_data.get('udp', {})
        for port, port_data in udp_data.items():
            ports_list.append({
                "port": int(port),
                "protocol": "udp",
                "state": port_data.get('state', 'unknown'),
                "service": port_data.get('name', 'unknown'),
                "version": port_data.get('version', '')
            })

        os_detection = None
        osmatches = host_data.get('osmatch', [])
        if osmatches:
            os_detection = osmatches[0].get('name', '')

        hosts_list.append({
            "ip": ip,
            "hostname": hostname,
            "state": host_data.get('status', {}).get('state', 'down'),
            "ports": ports_list,
            "os_detection": os_detection
        })

    result = {
        "target": target,
        "scan_timestamp": datetime.now().isoformat(),
        "hosts": hosts_list,
        "raw_nmap_output": str(scan_result)
    }

    logger.info(f"Network scan completed for target {target}. Found {len(hosts_list)} hosts.")
    return result
