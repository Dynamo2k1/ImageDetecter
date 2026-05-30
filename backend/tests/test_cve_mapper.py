import pytest
import time
from unittest.mock import patch, MagicMock
from app.services.cve_mapper import get_local_fallback, query_nvd_api, map_vulnerabilities, _rate_limit

def test_local_fallback_matching():
    # Test fallback mapping
    results = get_local_fallback("http", "2.4.41")
    # Verify that it finds matches from known_vulns.json
    assert len(results) > 0
    for r in results:
        assert "cve_id" in r
        assert "risk_level" in r
        assert "Apache" in r["description"] or "HTTP" in r["description"] or "server" in r["description"] or "CVE" in r["cve_id"]

@patch("httpx.Client")
def test_query_nvd_api_success(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2021-41773",
                    "descriptions": [{"lang": "en", "value": "Path traversal and file disclosure in Apache HTTP Server 2.4.49"}],
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "cvssData": {
                                    "baseScore": 7.5,
                                    "baseSeverity": "HIGH"
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    findings = query_nvd_api("apache 2.4.49")
    assert len(findings) == 1
    assert findings[0]["cve_id"] == "CVE-2021-41773"
    assert findings[0]["cvss_score"] == 7.5
    assert findings[0]["risk_level"] == "High"

@patch("app.services.cve_mapper.time.sleep")
def test_rate_limiter_spacing(mock_sleep):
    # Call twice to trigger rate limit delay check
    _rate_limit()
    t0 = time.time()
    _rate_limit()
    # If the second request is immediate, the elapsed time is < 6s, so sleep is called
    assert mock_sleep.called

@patch("app.services.cve_mapper.query_nvd_api")
def test_map_vulnerabilities_integrates_findings(mock_query_nvd):
    mock_query_nvd.return_value = [
        {
            "cve_id": "CVE-2017-7529",
            "description": "Nginx vulnerability",
            "cvss_score": 7.5,
            "severity": "High",
            "risk_level": "High",
            "nvd_url": "http://nvd.url"
        }
    ]

    scan_result = {
        "target": "nginx.org",
        "hosts": [
            {
                "ip": "1.2.3.4",
                "ports": [
                    {
                        "port": 80,
                        "protocol": "tcp",
                        "service": "nginx",
                        "version": "1.13.2"
                    }
                ]
            }
        ]
    }

    mapped = map_vulnerabilities(scan_result)
    assert len(mapped) == 1
    assert mapped[0]["port"] == 80
    assert mapped[0]["cve_id"] == "CVE-2017-7529"
    assert mapped[0]["service"] == "nginx"
