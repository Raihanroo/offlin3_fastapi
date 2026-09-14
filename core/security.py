# core/security.py
# Password hashing & verification using pwdlib

from pwdlib import PasswordHash

# PasswordHash.recommended() -> Argon2 based recommended hasher (with bcrypt fallback support)
password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Plain password ke securely hash kore return kore."""
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Login er somoy plain password ke stored hash er sathe compare kore."""
    return password_hash.verify(plain_password, hashed_password)
