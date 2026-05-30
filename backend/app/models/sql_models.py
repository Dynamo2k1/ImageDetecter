from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Integer, Boolean
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
    
    # Secure Evidence Storage & Integrity
    integrity_status = Column(String, default="VERIFIED")
    is_encrypted = Column(Boolean, default=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = Column(DateTime, nullable=True)


    # Relationships
    custody_logs = relationship("ChainOfCustody", back_populates="job", cascade="all, delete-orphan")

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

class ScanResult(Base):
    __tablename__ = "scan_results"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    target = Column(String, nullable=False)
    scan_timestamp = Column(DateTime, default=datetime.now)
    status = Column(String, default="pending")  # pending, running, completed, failed
    result_json = Column(JSON, nullable=True)
    initiated_by = Column(String, nullable=False)  # investigator user ID
    error_message = Column(String, nullable=True)

class VulnerabilityFinding(Base):
    __tablename__ = "vulnerability_findings"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scan_results.id"))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    port = Column(Integer, nullable=True)
    service = Column(String, nullable=True)
    version = Column(String, nullable=True)
    cve_id = Column(String, nullable=True)
    description = Column(String, nullable=True)
    cvss_score = Column(Float, nullable=True)
    severity = Column(String, nullable=True)  # Critical, High, Medium, Low, Informational
    risk_level = Column(String, nullable=True)
    nvd_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class ReconResult(Base):
    __tablename__ = "recon_results"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    recon_type = Column(String, nullable=False)  # dns, whois, subdomain, headers, ssl, geoip, threat_intel
    target = Column(String, nullable=False)
    result_json = Column(JSON, nullable=True)
    performed_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class CorrelationReport(Base):
    __tablename__ = "correlation_reports"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    correlation_timestamp = Column(DateTime, default=datetime.now)
    result_json = Column(JSON)
    correlation_score = Column(Integer, default=0)
    generated_by = Column(String)

from sqlalchemy import event

@event.listens_for(ChainOfCustody, "before_update")
def prevent_custody_update(mapper, connection, target):
    raise RuntimeError("Chain of Custody is append-only. Modification is prohibited.")

@event.listens_for(ChainOfCustody, "before_delete")
def prevent_custody_delete(mapper, connection, target):
    raise RuntimeError("Chain of Custody is append-only. Deletion is prohibited.")

