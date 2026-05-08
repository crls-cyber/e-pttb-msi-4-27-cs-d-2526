"""Cryptography utilities for secrets management."""
from cryptography.fernet import Fernet
import os


class SecretManager:
    """Manage encrypted secrets using Fernet."""
    
    def __init__(self):
        """Initialize Fernet cipher."""
        key = os.getenv('FERNET_KEY')
        if not key:
            raise ValueError("FERNET_KEY environment variable not set")
        
        self.cipher = Fernet(key.encode())
    
    def encrypt(self, plaintext):
        """Encrypt a string."""
        if not plaintext:
            return None
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext):
        """Decrypt a string."""
        if not ciphertext:
            return None
        return self.cipher.decrypt(ciphertext.encode()).decode()


# Global instance
secret_manager = SecretManager()
