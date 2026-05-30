import pytest
import os
from datetime import datetime
from unittest.mock import MagicMock
from app.services.pdf_generator import PDFReportGenerator
from app.models.sql_models import ScanResult, VulnerabilityFinding

def test_generate_custom_report():
    # Construct mock report data payload matching report_builder structure
    report_data = {
        "job_id": "test-job-uuid",
        "status": "completed",
        "source": "url",
        "original_url": "https://youtube.com/watch?v=123",
        "integrity_status": "VERIFIED",
        "is_encrypted": True,
        "created_at": datetime.now(),
        "completed_at": datetime.now(),
        "file_path": "/fake/storage/path.enc",
        "filename": "video.mp4",
        "file_size": 1500000, # 1.5MB
        "mime_type": "video/mp4",
        "sha256_hash": "a" * 64,
        "exif_data": {},
        "media_metadata": {},
        "platform_metadata": {"platform": "youtube"},

        "include_custody": True,
        "chain_of_custody": [
            MagicMock(timestamp=datetime.now(), event="EVIDENCE_ACQUIRED", investigator_id="1", details={"source": "url"}),
            MagicMock(timestamp=datetime.now(), event="INTEGRITY_VERIFIED", investigator_id="system", details={})
        ],
        
        "include_scans": True,
        "scans": [
            MagicMock(
                scan_timestamp=datetime.now(),
                status="completed",
                target="8.8.8.8",
                initiated_by="1",
                scan_id=1,
                result_json={
                    "hosts": [
                        {
                            "ip": "8.8.8.8",
                            "hostname": "dns.google",
                            "state": "up",
                            "os_detection": "Linux",
                            "ports": [
                                {"port": 53, "protocol": "tcp", "state": "open", "service": "dns", "version": "1.0"}
                            ]
                        }
                    ]
                }
            )
        ],
        
        "include_vulnerabilities": True,
        "vulnerabilities": [
            MagicMock(
                port=53,
                service="dns",
                version="1.0",
                cve_id="CVE-2023-1234",
                description="DNS cache poisoning bug.",
                cvss_score=8.5,
                severity="High",
                risk_level="High",
                nvd_url="http://nvd.url"
            )
        ],
        
        "include_correlation": True,
        "correlation": {
            "score": 60,
            "flags": [
                {"id": "CRITICAL_VULNERABILITIES_FOUND", "title": "Critical/High Vulnerabilities Mapped", "description": "High CVSS mapped.", "severity": "HIGH"}
            ],
            "attack_hypotheses": [
                {"scenario": "DNS Spoofing", "probability": "High", "description": "Cache poisoning vulnerability."}
            ],
            "timeline": [
                {"timestamp": datetime.now().isoformat(), "event": "EVIDENCE_ACQUIRED", "investigator_id": "1", "details": {}},
                {"timestamp": datetime.now().isoformat(), "event": "SCAN_COMPLETED", "investigator_id": "1", "details": {}}
            ]
        }
    }

    pdf_path = PDFReportGenerator.generate_custom_report(report_data)
    
    assert pdf_path is not None
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0
    
    # Cleanup
    if os.path.exists(pdf_path):
        os.unlink(pdf_path)
