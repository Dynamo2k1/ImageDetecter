# Security Policy

## Supported Versions

Currently, only the latest major release of FEAS is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

Security is a core tenet of the Forensic Evidence Acquisition System (FEAS). As a tool designed for handling sensitive forensic data, we take vulnerabilities extremely seriously.

If you discover a security vulnerability within FEAS, **please do not open a public issue.**

Instead, please email the core maintainer team at `security@feas.local` (or the equivalent repository owner email). 

Please include the following information in your report:
* A description of the vulnerability.
* The exact steps to reproduce the issue.
* The potential impact if the vulnerability is exploited.
* Any proposed mitigation or fix you might have.

### Triage Process

1. **Acknowledgement**: You should receive an acknowledgement of your report within 48 hours.
2. **Investigation**: The maintainer team will investigate the issue and determine its validity and severity.
3. **Resolution**: If a vulnerability is confirmed, we will develop a patch and release a security advisory.
4. **Credit**: We will publicly acknowledge your contribution in the security advisory unless you request to remain anonymous.

## Secure Deployment Recommendations

When deploying FEAS 2.0 in a production forensic environment, we strongly recommend:

1. **Change Default Credentials**: Immediately change the default admin credentials (`admin@feas.local` / `admin123`) configured in the `.env` file.
2. **Key Management**: Ensure `SECRET_KEY` and `FEAS_ENCRYPTION_KEY` are long, random, cryptographically secure strings and are never committed to version control.
3. **Network Isolation**: Restrict network access to the FEAS API and database. The scanner module (`ALLOW_INTERNAL_SCAN=false`) intentionally blocks scanning internal RFC1918 IPs by default to prevent SSRF-style internal pivot attacks. Do not enable this in production unless absolutely necessary and authorized.
4. **TLS/SSL**: Always deploy the frontend and backend behind a reverse proxy (e.g., Nginx) configured with TLS/SSL. Do not expose the raw Uvicorn server to the public internet.
