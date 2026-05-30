import pytest
import os
import shutil
import tempfile
from app.services.encryption import encrypt_file, decrypt_file, get_fernet

def test_key_load_or_creation():
    # Calling get_fernet should return a valid Fernet instance
    fernet = get_fernet()
    assert fernet is not None

def test_file_encrypt_decrypt_cycle():
    # Create temp files
    with tempfile.NamedTemporaryFile(delete=False) as orig_file:
        orig_file.write(b"Forensic Evidence Confidential Content")
        orig_path = orig_file.name
        
    enc_path = orig_path + ".enc"
    dec_path = orig_path + ".dec"
    
    try:
        # Encrypt
        encrypt_file(orig_path, enc_path)
        assert os.path.exists(enc_path)
        
        # Verify encrypted file does not contain plain text
        with open(enc_path, 'rb') as f:
            enc_content = f.read()
            assert b"Forensic Evidence" not in enc_content
            
        # Decrypt
        decrypt_file(enc_path, dec_path)
        assert os.path.exists(dec_path)
        
        # Verify decrypted matches original
        with open(dec_path, 'rb') as f:
            dec_content = f.read()
            assert dec_content == b"Forensic Evidence Confidential Content"
            
    finally:
        # Cleanup
        for path in [orig_path, enc_path, dec_path]:
            if os.path.exists(path):
                os.unlink(path)
