from flask_bcrypt import Bcrypt
import re

bcrypt = Bcrypt()

# Configure bcrypt with higher work factor (default is 12)
BCRYPT_ROUNDS = 14

def validate_password(password):
    """
    Validate password strength
    Returns (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def hash_password(password):
    """
    Hash password with increased rounds for better security
    """
    return bcrypt.generate_password_hash(
        password, 
        rounds=BCRYPT_ROUNDS
    ).decode('utf-8')

def check_password(password_hash, password):
    """
    Verify password against hash
    """
    return bcrypt.check_password_hash(password_hash, password) 