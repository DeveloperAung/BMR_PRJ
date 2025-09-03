# core/utils/encryption.py
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import logging

logger = logging.getLogger(__name__)


def get_encryption_key():
    """Get encryption key from settings"""
    key = getattr(settings, 'FERNET_KEY', None)
    if not key:
        raise ValueError("FERNET_KEY not set in settings")
    return key.encode() if isinstance(key, str) else key


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    if not data:
        return ""

    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        # Return base64 encoded string for storage
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    if not encrypted_data:
        return ""

    try:
        key = get_encryption_key()
        f = Fernet(key)
        # Decode from base64 first
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise


def mask_phone_number(phone: str) -> str:
    """Mask phone number for display (e.g., +659***4567)"""
    if not phone:
        return phone
    if len(phone) >= 8:
        # Show first 4 and last 4 digits
        return phone[:4] + '*' * (len(phone) - 8) + phone[-4:]
    elif len(phone) >= 6:
        # Fallback for shorter numbers
        return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]
    return phone


def mask_nric(nric: str) -> str:
    """Mask NRIC/FIN for display (e.g., S123***7A)"""
    if not nric:
        return nric
    if len(nric) >= 8:
        # Show first 4 and last 4 characters for NRIC (e.g., S123***7A)
        return nric[:4] + '*' * (len(nric) - 8) + nric[-4:]
    elif len(nric) >= 4:
        # Fallback for shorter strings
        return nric[:2] + '*' * (len(nric) - 4) + nric[-2:]
    return nric