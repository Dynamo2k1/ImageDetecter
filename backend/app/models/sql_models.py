from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, index=True)  # pending, completed, failed
    source = Column(String)  # url, local_upload
    progress = Column(Float, default=0.0)
    stage = Column(String)
    
    # Metadata
    filename = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    sha256_hash = Column(String, index=True, nullable=True)
    
    # Investigation Info
    investigator_id = Column(String, index=True)
    case_number = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    original_url = Column(String, nullable=True)
    
    # Storage
    storage_path = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    custody_logs = relationship("ChainOfCustody", back_populates="job", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="job", cascade="all, delete-orphan")
    integrity_alerts = relationship("IntegrityAlert", back_populates="job", cascade="all, delete-orphan")
    correlations = relationship("EvidenceCorrelation", back_populates="job", cascade="all, delete-orphan")

class ChainOfCustody(Base):
    __tablename__ = "chain_of_custody"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    timestamp = Column(DateTime, default=datetime.now)
    event = Column(String)
    investigator_id = Column(String)
    details = Column(JSON)
    hash_verification = Column(String, nullable=True)

    job = relationship("Job", back_populates="custody_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)  # upload, view, delete, scan
    user_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    details = Column(JSON, nullable=True)

    job = relationship("Job", back_populates="audit_logs")


class NetworkScan(Base):
    __tablename__ = "network_scans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number = Column(String, nullable=False, index=True)
    target = Column(String, nullable=False, index=True)
    initiated_by = Column(String, nullable=False, index=True)
    command = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    raw_output = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ports = relationship("ScanPort", back_populates="scan", cascade="all, delete-orphan")
    vulnerabilities = relationship("VulnerabilityFinding", back_populates="scan", cascade="all, delete-orphan")
    correlations = relationship("EvidenceCorrelation", back_populates="scan", cascade="all, delete-orphan")


class ScanPort(Base):
    __tablename__ = "scan_ports"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("network_scans.id"), nullable=False, index=True)
    port = Column(Integer, nullable=False, index=True)
    protocol = Column(String, nullable=False, default="tcp")
    state = Column(String, nullable=False, default="open")
    service = Column(String, nullable=True)
    version = Column(String, nullable=True)

    scan = relationship("NetworkScan", back_populates="ports")
    vulnerabilities = relationship("VulnerabilityFinding", back_populates="port_ref", cascade="all, delete-orphan")


class VulnerabilityFinding(Base):
    __tablename__ = "vulnerability_findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("network_scans.id"), nullable=False, index=True)
    scan_port_id = Column(Integer, ForeignKey("scan_ports.id"), nullable=True)
    cve_id = Column(String, nullable=False, index=True)
    service = Column(String, nullable=True, index=True)
    version = Column(String, nullable=True)
    risk_level = Column(String, nullable=False, index=True)  # Low, Medium, High
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("NetworkScan", back_populates="vulnerabilities")
    port_ref = relationship("ScanPort", back_populates="vulnerabilities")
    correlations = relationship("EvidenceCorrelation", back_populates="vulnerability", cascade="all, delete-orphan")


class IntegrityAlert(Base):
    __tablename__ = "integrity_alerts"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    expected_hash = Column(String, nullable=False)
    current_hash = Column(String, nullable=False)
    message = Column(String, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False)

    job = relationship("Job", back_populates="integrity_alerts")


class EvidenceCorrelation(Base):
    __tablename__ = "evidence_correlations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    scan_id = Column(String, ForeignKey("network_scans.id"), nullable=False, index=True)
    vulnerability_id = Column(Integer, ForeignKey("vulnerability_findings.id"), nullable=True)
    correlation_type = Column(String, nullable=False)
    confidence = Column(Float, default=0.5)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="correlations")
    scan = relationship("NetworkScan", back_populates="correlations")
    vulnerability = relationship("VulnerabilityFinding", back_populates="correlations")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship to profile
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String, default="Investigator")
    role = Column(String, default="Senior Analyst")
    bio = Column(String, default="Digital forensics specialist.")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship back to user
    user = relationship("User", back_populates="profile")

class SocialLink(Base):
    __tablename__ = "social_links"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String) # e.g., "twitter"
    handle = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.now)
