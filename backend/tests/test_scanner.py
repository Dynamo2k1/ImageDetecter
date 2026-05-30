import pytest
from unittest.mock import MagicMock, patch
from app.services.scanner import is_private_target, run_scan
from app.core.config import settings

def test_is_private_target():
    # 127.0.0.1 is loopback/private
    assert is_private_target("127.0.0.1") is True
    # 192.168.1.50 is private RFC1918
    assert is_private_target("192.168.1.50") is True
    # 8.8.8.8 is a public IP
    assert is_private_target("8.8.8.8") is False
    # Localhost resolves to loopback
    assert is_private_target("localhost") is True

@patch("app.services.scanner.is_private_target")
def test_run_scan_prohibits_private_ips(mock_is_private):
    mock_is_private.return_value = True
    # Ensure ALLOW_INTERNAL_SCAN is False
    settings.ALLOW_INTERNAL_SCAN = False
    
    with pytest.raises(ValueError) as excinfo:
        run_scan("192.168.1.10")
    assert "private or loopback IP address" in str(excinfo.value)

@patch("nmap.PortScanner")
def test_run_scan_success(mock_nmap_class):
    # Mock nmap response
    mock_nmap = MagicMock()
    mock_nmap.scan.return_value = {
        "scan": {
            "8.8.8.8": {
                "hostnames": [{"name": "dns.google"}],
                "status": {"state": "up"},
                "tcp": {
                    53: {"state": "open", "name": "domain", "version": "dnsmasq 2.80"},
                    443: {"state": "open", "name": "https", "version": "nginx"}
                },
                "osmatch": [{"name": "Linux 5.x"}]
            }
        }
    }
    mock_nmap_class.return_value = mock_nmap
    
    # Temporarily allow or use public IP since it is mocked
    settings.ALLOW_INTERNAL_SCAN = True
    
    res = run_scan("8.8.8.8")
    
    assert res["target"] == "8.8.8.8"
    assert len(res["hosts"]) == 1
    host = res["hosts"][0]
    assert host["ip"] == "8.8.8.8"
    assert host["hostname"] == "dns.google"
    assert host["os_detection"] == "Linux 5.x"
    assert len(host["ports"]) == 2
    
    ports = sorted(host["ports"], key=lambda x: x["port"])
    assert ports[0]["port"] == 53
    assert ports[0]["service"] == "domain"
    assert ports[0]["version"] == "dnsmasq 2.80"
    
    assert ports[1]["port"] == 443
    assert ports[1]["service"] == "https"
    assert ports[1]["version"] == "nginx"
