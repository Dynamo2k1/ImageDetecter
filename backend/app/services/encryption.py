import os
import logging
from pathlib import Path
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)

_fernet_instance = None

def get_fernet() -> Fernet:
    """Lazily load or generate the Fernet key and initialize the instance"""
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    key = settings.FEAS_ENCRYPTION_KEY
    if key:
        try:
            _fernet_instance = Fernet(key.encode())
            logger.info("Fernet encryption key initialized from settings.")
            return _fernet_instance
        except Exception as e:
            logger.error(f"Provided FEAS_ENCRYPTION_KEY is invalid: {str(e)}. Generating fallback.")

    # Fallback to local file key persistence
    key_dir = Path("data")
    key_dir.mkdir(exist_ok=True)
    key_file = key_dir / "feas.key"

    if key_file.exists():
        try:
            persisted_key = key_file.read_bytes()
            _fernet_instance = Fernet(persisted_key)
            logger.info(f"Fernet encryption key loaded from persisted key file: {key_file}")
            return _fernet_instance
        except Exception as e:
            logger.error(f"Failed to load persisted key file: {str(e)}. Generating new one.")

    # Generate new key
    new_key = Fernet.generate_key()
    try:
        key_file.write_bytes(new_key)
        logger.warning(f"FEAS_ENCRYPTION_KEY env var not set. Generated fallback key and persisted to {key_file}. KEEP THIS KEY SAFE!")
        _fernet_instance = Fernet(new_key)
    except Exception as e:
        logger.critical(f"Failed to persist generated encryption key to {key_file}: {str(e)}")
        # In-memory fallback
        _fernet_instance = Fernet(new_key)

    return _fernet_instance

def encrypt_file(source_path: str, dest_path: str) -> None:
    """Encrypt a file at rest using AES-256 Fernet"""
    fernet = get_fernet()
    with open(source_path, "rb") as f:
        plaintext = f.read()
    ciphertext = fernet.encrypt(plaintext)
    with open(dest_path, "wb") as f:
        f.write(ciphertext)
    logger.info(f"File encrypted successfully: {source_path} -> {dest_path}")

def decrypt_file(source_path: str, dest_path: str) -> None:
    """Decrypt a file from storage using AES-256 Fernet"""
    fernet = get_fernet()
    with open(source_path, "rb") as f:
        ciphertext = f.read()
    plaintext = fernet.decrypt(ciphertext)
    with open(dest_path, "wb") as f:
        f.write(plaintext)
    logger.info(f"File decrypted successfully: {source_path} -> {dest_path}")

def is_encrypted(path: str) -> bool:
    """Checks if a file starts with the Fernet token header"""
    try:
        if not os.path.exists(path):
            return False
        with open(path, "rb") as f:
            header = f.read(6)
        return header == b"gAAAAA"
    except Exception as e:
        logger.error(f"Failed to check encryption header: {str(e)}")
        return False
