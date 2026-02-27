from werkzeug.security import generate_password_hash, check_password_hash

# Pre-calculated hash for timing attack mitigation (username enumeration)
DUMMY_HASH = generate_password_hash("timing_attack_mitigation_constant")

def hash_password(password: str) -> str:
    if password is None:
        raise ValueError("password is required")
    password = password.strip()
    if len(password) < 10:
        raise ValueError("password must be at least 10 characters")
    return generate_password_hash(password)

def verify_password(password_hash: str, password_attempt: str) -> bool:
    if not password_hash or password_attempt is None:
        return False
    return check_password_hash(password_hash, password_attempt.strip())