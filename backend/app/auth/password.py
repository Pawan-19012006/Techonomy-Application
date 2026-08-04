import bcrypt


def hash_password(password: str) -> str:
    """Hashes a plain text password using bcrypt.

    Args:
        password: Plain text password.

    Returns:
        str: Hashed password string.
    """
    salt = bcrypt.gensalt()
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a bcrypt hash.

    Args:
        plain_password: Password input to test.
        hashed_password: Hashed password stored in database.

    Returns:
        bool: True if matched, False otherwise.
    """
    pwd_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hash_bytes)
