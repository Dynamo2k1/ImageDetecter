import re
import subprocess
import xml.etree.ElementTree as ET
import ipaddress
import socket
from typing import Dict, Any, List


class NetworkScannerService:
    """Executes and parses nmap scan results."""

    SAFE_TARGET_RE = re.compile(r"^[a-zA-Z0-9\.\-:]+$")

    @classmethod
    def validate_target(cls, target: str) -> bool:
        return bool(target and cls.SAFE_TARGET_RE.match(target))

    @classmethod
    def normalize_target(cls, target: str) -> str:
        if not cls.validate_target(target):
            raise ValueError("Invalid scan target.")

        try:
            return str(ipaddress.ip_address(target))
        except ValueError:
            resolved_ip = socket.gethostbyname(target)
            return str(ipaddress.ip_address(resolved_ip))

    @classmethod
    def run_scan(cls, target: str) -> Dict[str, Any]:
        safe_target_ip = cls.normalize_target(target)
        # shell=False + IP-normalized target keeps command execution constrained.
        command = ["nmap", "-sV", "-Pn", "-oX", "-", "--", safe_target_ip]
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
            check=False,
        )

        if process.returncode != 0:
            raise RuntimeError(process.stderr.strip() or "Nmap scan failed.")

        xml_output = process.stdout
        parsed = cls.parse_nmap_xml(xml_output)
        return {
            "command": " ".join(command),
            "raw_output": xml_output,
            "parsed": parsed
        }

    @staticmethod
    def parse_nmap_xml(xml_output: str) -> Dict[str, Any]:
        root = ET.fromstring(xml_output)
        hosts: List[Dict[str, Any]] = []

        for host in root.findall("host"):
            addresses = [a.attrib.get("addr") for a in host.findall("address") if a.attrib.get("addr")]
            ports: List[Dict[str, Any]] = []
            ports_node = host.find("ports")

            if ports_node is not None:
                for port in ports_node.findall("port"):
                    state_node = port.find("state")
                    service_node = port.find("service")
                    state = state_node.attrib.get("state") if state_node is not None else "unknown"
                    service_name = service_node.attrib.get("name") if service_node is not None else ""
                    product = service_node.attrib.get("product", "") if service_node is not None else ""
                    version = service_node.attrib.get("version", "") if service_node is not None else ""
                    version_text = " ".join([product, version]).strip()

                    if state == "open":
                        ports.append(
                            {
                                "port": int(port.attrib.get("portid", 0)),
                                "protocol": port.attrib.get("protocol", "tcp"),
                                "state": state,
                                "service": service_name,
                                "version": version_text
                            }
                        )

            hosts.append(
                {
                    "addresses": addresses,
                    "ports": ports
                }
            )

        return {"hosts": hosts}
