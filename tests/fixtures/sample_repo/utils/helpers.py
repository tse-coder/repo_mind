import hashlib
import secrets


def hash_password(password: str) -> str:
    """Generate SHA256 hash for password."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_hex(length)
