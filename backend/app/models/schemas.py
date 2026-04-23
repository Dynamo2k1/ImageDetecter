from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, HttpUrl, Field, validator, ConfigDict

class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    HASHING = "hashing"
    EXTRACTING_METADATA = "extracting_metadata"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"

class EvidenceSource(str, Enum):
    URL = "url"
    LOCAL_UPLOAD = "local_upload"

class Platform(str, Enum):
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LOCAL = "local"

class URLJobCreate(BaseModel):
    url: HttpUrl
    investigator_id: str = Field(..., min_length=1, max_length=100)
    case_number: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('url')
    def validate_url_domain(cls, v):
        allowed_domains = ['twitter.com', 'x.com', 'youtube.com', 'youtu.be', 'facebook.com', 'fb.watch', 'instagram.com']
        domain = str(v).split('/')[2]
        if not any(allowed in domain for allowed in allowed_domains):
            raise ValueError(f'URL domain not allowed. Allowed: {allowed_domains}')
        return v

class FileUploadRequest(BaseModel):
    investigator_id: str = Field(..., min_length=1, max_length=100)
    case_number: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)

class JobStatusResponse(BaseModel):
    # FIX: Use validation_alias to map 'id' (from DB) to 'job_id' (for API)
    job_id: str = Field(..., validation_alias="id")
    status: str
    source: str
    progress: float = Field(0.0, ge=0.0, le=100.0)
    stage: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Metadata(BaseModel):
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    sha256_hash: Optional[str] = None
    exif_data: Optional[Dict[str, Any]] = None
    platform_metadata: Optional[Dict[str, Any]] = None
    media_metadata: Optional[Dict[str, Any]] = None
    extraction_timestamp: Optional[datetime] = None

class ChainOfCustodyEntry(BaseModel):
    timestamp: datetime
    event: str
    details: Dict[str, Any]
    investigator_id: str
    hash_verification: Optional[str] = None

class JobDetailsResponse(BaseModel):
    job_id: str
    status: str
    source: str
    platform: Optional[str] = None
    metadata: Metadata
    chain_of_custody: List[ChainOfCustodyEntry]
    original_url: Optional[str] = None
    file_path: str
    storage_location: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    scan_results: Optional[List[Dict[str, Any]]] = None
    vulnerabilities: Optional[List[Dict[str, Any]]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    
    # Allow mapping if we ever use from_attributes here too
    model_config = ConfigDict(from_attributes=True)

class VerificationResponse(BaseModel):
    job_id: str
    verification_timestamp: datetime
    original_hash: str
    current_hash: str
    matches: bool
    verification_details: Dict[str, Any]

class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]


class NetworkScanRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255)
    case_number: str = Field(..., min_length=1, max_length=50)


class NetworkScanResponse(BaseModel):
    scan_id: str
    case_number: str
    target: str
    status: str
    command: str
    ports: List[Dict[str, Any]]
    vulnerabilities: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    correlations_created: int
