"""Password hashing utilities for FastFrame authentication."""

import hashlib
import secrets
from typing import Any


def make_password(password: str, salt: str | None = None) -> str:
    """
    Hash a password using PBKDF2 with SHA256.
    
    Args:
        password: The plaintext password to hash
        salt: Optional salt (auto-generated if not provided)
        
    Returns:
        Hashed password in format: pbkdf2_sha256$salt$hash
    """
    if not password:
        return ""
    
    if salt is None:
        salt = secrets.token_hex(16)
    
    # 120,000 iterations is Django's current default (2024)
    iterations = 120_000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
    
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def check_password(password: str, encoded: str) -> bool:
    """
    Check a password against a hash.
    
    Args:
        password: The plaintext password to check
        encoded: The hashed password to check against
        
    Returns:
        True if password matches, False otherwise
    """
    if not password or not encoded:
        return False
    
    try:
        algorithm, salt, hash_value = encoded.split('$', 2)
        if algorithm != 'pbkdf2_sha256':
            return False
        
        # Re-hash the provided password with the stored salt
        expected = make_password(password, salt)
        return expected == encoded
        
    except ValueError:
        # Invalid format
        return False