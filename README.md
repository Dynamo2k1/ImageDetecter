# 🕵️‍♂️ Forensic Evidence Acquisition System (FEAS) 2.0

![License](https://img.shields.io/badge/License-MIT-blue.svg) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![React](https://img.shields.io/badge/React-18.2-61DAFB) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)

> **Enterprise-grade digital forensics and red team reconnaissance platform.**
> Acquire, preserve, analyze, and correlate web and local evidence with an immutable chain of custody.

---

## 📖 Overview

The **Forensic Evidence Acquisition System (FEAS) 2.0** is a secure, full-stack solution designed for law enforcement, digital forensic investigators, and red teamers. 

Version 2.0 expands the platform from a secure evidence downloader to a complete **cyber threat intelligence and analysis suite**, introducing network scanning, CVE correlation, and a comprehensive OSINT/Recon module.

## ✨ Key Features

### 🔍 Red Team Recon Module (NEW in v2.0)
A complete suite of 7 passive and active reconnaissance tools:
* **DNS Recon**: Query A/AAAA/MX/NS/TXT/SOA/CNAME + SPF/DMARC detection
* **WHOIS Lookup**: Domain registration, age, and expiry countdowns
* **Subdomain Enumeration**: High-performance concurrent DNS brute-force
* **HTTP Security Headers**: A-F grading and missing header detection
* **SSL/TLS Inspector**: Certificate analysis, cipher suites, and expiry checks
* **GeoIP & ASN Lookup**: Country, ISP, and proxy/VPN detection
* **Threat Intel**: IoC lookup with AbuseIPDB, VirusTotal, and offline feeds

### 🛡️ Vulnerability & Network Scanning (NEW in v2.0)
* **Nmap Integration**: Automated port, service, and OS detection
* **CVE Correlation**: NIST NVD API v2.0 integration maps discovered services to known vulnerabilities
* **Offline Fallback**: Built-in vulnerability database for air-gapped environments
* **Risk Scoring**: 0-100 score based on critical/high/medium/low findings

### 🔒 Core Forensic Capabilities
* **Universal Acquisition**: Download from Twitter/X, YouTube, Facebook, Instagram or local upload
* **Secure Authentication**: JWT tokens, bcrypt hashing, and Role-Based Access Control (RBAC)
* **Evidence Integrity**: SHA-256 hashing + Fernet AES-128 encryption at rest
* **Chain of Custody**: Immutable, append-only logs for every single action
* **Metadata Extraction**: EXIF, video codecs, and file magic MIME detection
* **Automated Reporting**: Generates legally admissible PDF forensic reports

---

## 🛠️ Tech Stack

* **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLite/PostgreSQL, Celery, Redis
* **Frontend**: React 18, Styled-Components, React Query, Zustand
* **Forensic Tools**: `nmap`, `dnspython`, `python-whois`, `yt-dlp`, `ffmpeg`, `exifread`, `python-magic`
* **Security**: `passlib[bcrypt]`, `python-jose`, `cryptography` (Fernet)

---

## 🚀 Getting Started

### Quick Start (Development Mode)

The system can run locally using SQLite and background tasks (no Docker or Redis required).

1. **Setup Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env from example
cp .env.example .env

# Run server with SQLite and internal tasks (no Celery)
USE_SQLITE=true USE_CELERY=false ALLOW_INTERNAL_SCAN=true \
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. **Setup Frontend**
```bash
cd frontend
npm install
npm start
```
The React app will open at `http://localhost:3000`.

**Default Admin Credentials:**
* Email: `admin@feas.local`
* Password: `admin123`

### Production Deployment (Docker)

```bash
cd backend
docker-compose up -d --build
```
This spins up PostgreSQL, Redis, FastAPI, Celery Worker, Celery Beat, and the React Frontend.

---

## 📚 Documentation

For deep technical dives, refer to our comprehensive markdown documentation:
* [**System Architecture & Data Flows**](ARCHITECTURE.md)
* [**Security Policies & Hardening**](SECURITY.md)
* [**Contributing Guidelines**](CONTRIBUTING.md)
* [**PostgreSQL Setup**](POSTGRESQL_SETUP.md)
* [**URL Acquisition Setup**](URL_SETUP.md)

---

## 📸 Screenshots

| Reconnaissance Module | Correlation Engine |
|:---:|:---:|
| *7-tool OSINT and Active Recon Suite* | *Timeline & Risk Score Generation* |
| Network Scanner | Vulnerability Mapping |
| *Nmap integration with live status* | *NIST NVD CVE lookups* |

---

## 📄 License

This project is licensed under the MIT License.

> **Disclaimer:** This software is intended for authorized forensic investigations and authorized penetration testing only. Ensure compliance with all local laws regarding data privacy, scanning, and evidence handling. The developers are not responsible for any misuse of this software.
