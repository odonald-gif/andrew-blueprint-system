import logging
import hashlib
import os

logger = logging.getLogger("AuthHandshake")

class AuthHandshake:
    """
    The Anti-Mutiny Protocol.
    Ensures that Andrew cannot execute catastrophic or financial actions 
    without cryptographic proof from Donald.
    """
    def __init__(self):
        # Master secret is now loaded from .env for security.
        secret = os.getenv("ANDREW_MASTER_SECRET", "")
        if not secret:
            raise ValueError("ANDREW_MASTER_SECRET not configured. Auth Handshake cannot start.")
        self.master_secret_hash = hashlib.sha256(secret.encode()).hexdigest()

    def verify_request(self, provided_secret: str, action: str) -> bool:
        """
        Verifies the secret before allowing the action.
        """
        provided_hash = hashlib.sha256(provided_secret.encode()).hexdigest()
        
        if provided_hash == self.master_secret_hash:
            logger.info(f"Handshake Verified. Authorized high-stakes action: {action}")
            return True
        else:
            logger.warning(f"HANDSHAKE FAILED! Unauthorized attempt to execute: {action}")
            return False

auth_handshake = AuthHandshake()
