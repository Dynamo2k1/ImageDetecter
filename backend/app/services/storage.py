import logging
import json
from pathlib import Path
from datetime import datetime
import uuid
import os
import hashlib
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    """Storage service for handling evidence files"""
    
    storage_type = settings.STORAGE_TYPE
    
    @classmethod
    async def initialize(cls):
        """Initialize storage service"""
        if cls.storage_type == "local":
            Path(settings.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage initialized at {settings.LOCAL_STORAGE_PATH}")
    
    @classmethod
    async def store_evidence(cls, file_path: str, job_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store evidence file"""
        if cls.storage_type == "local":
            return await cls._store_local(file_path, job_id, metadata)
        else:
            raise ValueError(f"Unsupported storage type: {cls.storage_type}")

    @classmethod
    async def _store_local(cls, file_path: str, job_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store file in local filesystem"""
        source_path = Path(file_path)
        
        # Create job directory
        job_dir = Path(settings.LOCAL_STORAGE_PATH) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        original_name = metadata.get('basic', {}).get('file_name', 'evidence')
        file_ext = Path(original_name).suffix
        if not file_ext:
            file_ext = source_path.suffix
            
        storage_name = f"{uuid.uuid4().hex}.enc"
        dest_path = job_dir / storage_name

        # Encrypt file before storage
        fernet = cls._get_fernet()
        with open(source_path, "rb") as source_file:
            plaintext = source_file.read()
        encrypted = fernet.encrypt(plaintext)
        with open(dest_path, "wb") as dest_file:
            dest_file.write(encrypted)
        
        # Create metadata file
        metadata_file = job_dir / "metadata.json"
        metadata = {
            **metadata,
            "security": {
                "encrypted_at_rest": True,
                "algorithm": "Fernet",
                "stored_extension": ".enc",
                "original_extension": file_ext
            }
        }
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return {
            'success': True,
            'path': str(dest_path),
            'location': f"local://{dest_path}",
            'size': dest_path.stat().st_size,
            'stored_at': datetime.utcnow().isoformat()
        }

    @classmethod
    def _get_fernet(cls) -> Fernet:
        configured_key = getattr(settings, "EVIDENCE_ENCRYPTION_KEY", None)
        if configured_key:
            key = configured_key.encode()
        else:
            configured_key_path = Path(getattr(settings, "EVIDENCE_ENCRYPTION_KEY_FILE", "./evidence_encryption.key"))
            if configured_key_path.is_absolute():
                key_file = configured_key_path
            else:
                key_file = Path(settings.LOCAL_STORAGE_PATH) / configured_key_path
            key_file.parent.mkdir(parents=True, exist_ok=True)
            if key_file.exists():
                key = key_file.read_bytes().strip()
            else:
                key = Fernet.generate_key()
                key_file.write_bytes(key)
                os.chmod(key_file, 0o600)
        return Fernet(key)

    @classmethod
    def read_decrypted_bytes(cls, encrypted_path: str) -> bytes:
        fernet = cls._get_fernet()
        with open(encrypted_path, "rb") as encrypted_file:
            encrypted = encrypted_file.read()
        return fernet.decrypt(encrypted)

    @classmethod
    def compute_stored_evidence_hash(cls, storage_path: str) -> Optional[str]:
        try:
            if storage_path.endswith(".enc"):
                content = cls.read_decrypted_bytes(storage_path)
                return hashlib.sha256(content).hexdigest()

            sha256_hash = hashlib.sha256()
            with open(storage_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return None
