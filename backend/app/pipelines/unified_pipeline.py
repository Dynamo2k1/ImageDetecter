import asyncio
import os
import magic 
import logging  # --- Added Standard Logging ---
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.sql_models import ChainOfCustody, Job
from app.models.schemas import JobDetailsResponse, JobStatus
from app.services.hashing import HashService
from app.services.metadata import MetadataExtractor
from app.services.storage import StorageService
from app.services.pdf_generator import PDFReportGenerator
from app.core.logger import ForensicLogger

# Setup standard logger for errors
std_logger = logging.getLogger(__name__)

class UnifiedForensicPipeline:
    
    def __init__(self):
        self.hash_service = HashService()
        self.metadata_extractor = MetadataExtractor()
        self.storage_service = StorageService()
        self.pdf_generator = PDFReportGenerator()

    async def process(self, 
                     file_path: str, 
                     job_id: str, 
                     investigator_id: str, 
                     source: str, 
                     filename: str = None,
                     original_url: str = None,
                     platform_info: Dict[str, Any] = None):
        """
        Main processing pipeline.
        """
        db: Session = SessionLocal()
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            db.close()
            raise ValueError(f"Job ID {job_id} not found in database.")

        try:
            # Update initial info
            if original_url:
                job.original_url = original_url
            if filename:
                job.filename = filename
            
            # --- 1. Hashing ---
            job.stage = "Hashing"
            job.progress = 10.0
            job.status = "processing"
            db.commit()

            sha256_hash = self.hash_service.compute_file_hash(file_path)

            log = ChainOfCustody(
                job_id=job_id,
                event="HASH_CALCULATED",
                investigator_id=investigator_id,
                details={"algorithm": "SHA256"},
                hash_verification=sha256_hash
            )
            db.add(log)
            db.commit()

            # --- 2. Metadata ---
            job.stage = "Metadata Extraction"
            job.progress = 30.0
            db.commit()

            metadata = self.metadata_extractor.extract_all_metadata(file_path)
            
            # Merge platform info if available
            if platform_info:
                metadata['platform'] = platform_info

            try:
                mime_type = magic.from_file(file_path, mime=True)
            except Exception:
                mime_type = "application/octet-stream"
            
            file_size = os.path.getsize(file_path)

            log = ChainOfCustody(
                job_id=job_id,
                event="METADATA_EXTRACTED",
                investigator_id=investigator_id,
                details={
                    "mime_type": mime_type, 
                    "file_size": file_size,
                    "platform_detected": platform_info.get('platform') if platform_info else "unknown"
                }
            )
            db.add(log)
            
            # Update job metadata
            job.file_size = file_size
            job.mime_type = mime_type
            db.commit()
            
            # --- 3. Storage ---
            job.stage = "Evidence Storage"
            job.progress = 60.0
            db.commit()
            
            final_filename = filename or os.path.basename(file_path)
            
            storage_metadata = {
                'basic': {'file_name': final_filename, 'file_size': file_size, 'mime_type': mime_type},
                'processing_info': {'sha256_hash': sha256_hash, 'investigator_id': investigator_id},
                'platform': platform_info
            }

            storage_result = await self.storage_service.store_evidence(
                file_path=file_path, 
                job_id=job_id, 
                metadata=storage_metadata
            )

            job.storage_path = storage_result.get('path')
            
            # Encrypt evidence file immediately after storing
            if job.storage_path and os.path.exists(job.storage_path):
                try:
                    from app.services.encryption import encrypt_file
                    temp_enc_path = job.storage_path + ".enc"
                    encrypt_file(job.storage_path, temp_enc_path)
                    os.replace(temp_enc_path, job.storage_path)
                    job.is_encrypted = True
                    logger.info(f"Evidence file encrypted at rest for job {job_id}")
                except Exception as enc_err:
                    logger.error(f"Failed to encrypt evidence file for job {job_id}: {str(enc_err)}")
                    # Proceed without encryption if it fails to not block pipeline completely
            
            # Assign owner user ID if we can resolve investigator_id to a user
            try:
                # Resolve owner_user_id from investigator_id
                # Check if investigator_id matches a user email or id
                from app.models.sql_models import User
                resolved_user = db.query(User).filter((User.id == investigator_id) | (User.email == investigator_id)).first()
                if resolved_user:
                    job.owner_user_id = resolved_user.id
            except Exception as rbac_err:
                logger.error(f"Failed to resolve owner user for job {job_id}: {str(rbac_err)}")

            job.sha256_hash = sha256_hash
            
            log = ChainOfCustody(
                job_id=job_id,
                event="EVIDENCE_STORED",
                investigator_id=investigator_id,
                details={"location": storage_result.get('location')}
            )
            db.add(log)
            db.commit()


            # --- 4. Report Generation ---
            job.stage = "Generating Report"
            job.progress = 90.0
            db.commit()
            
            current_logs = db.query(ChainOfCustody).filter(ChainOfCustody.job_id == job_id).order_by(ChainOfCustody.timestamp).all()
            
            job_details_obj = JobDetailsResponse(
                job_id=job.id,
                status=JobStatus.COMPLETED,
                source=job.source,
                platform=None, 
                metadata={
                    "file_name": job.filename or final_filename,
                    "file_size": job.file_size,
                    "mime_type": job.mime_type,
                    "sha256_hash": job.sha256_hash,
                    "extraction_timestamp": datetime.utcnow(),
                    "exif_data": metadata.get("exif"),
                    "media_metadata": metadata.get("media"),
                    "platform_metadata": metadata.get("platform")
                },
                chain_of_custody=[
                    {
                        "timestamp": log.timestamp,
                        "event": log.event,
                        "details": log.details,
                        "investigator_id": log.investigator_id,
                        "hash_verification": log.hash_verification
                    } for log in current_logs
                ],
                created_at=job.created_at,
                completed_at=datetime.utcnow(),
                file_path=job.storage_path,
                storage_location=storage_result.get('location'),
                original_url=job.original_url
            )

            pdf_path = self.pdf_generator.generate_report(job_details_obj)
            
            log = ChainOfCustody(
                job_id=job_id,
                event="REPORT_GENERATED",
                investigator_id=investigator_id,
                details={"report_path": pdf_path}
            )
            db.add(log)
            
            job.status = 'completed'
            job.progress = 100.0
            job.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": True, 
                "storage_path": job.storage_path, 
                "sha256_hash": sha256_hash, 
                "pdf_path": pdf_path
            }

        except Exception as e:
            # FIX: Use standard logger for errors
            std_logger.error(f"Pipeline failed for job {job_id}: {str(e)}")
            job.status = 'failed'
            job.notes = str(e)
            db.commit()
            raise 
        finally:
            db.close()

    def verify_integrity(self, file_path: str, original_hash: str, job_id: str, investigator_id: str):
        """Verifies if the current file hash matches the original chain of custody hash."""
        current_hash = self.hash_service.compute_file_hash(file_path)
        matches = (current_hash == original_hash)
        
        return {
            "success": True,
            "job_id": job_id,
            "original_hash": original_hash,
            "current_hash": current_hash,
            "matches": matches,
            "verification_details": {
                "verified_by": investigator_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }