import os
import base64
from cryptography.fernet import Fernet
from config import Config

class CredentialsManager:
    def __init__(self):
        key = self._get_or_create_credentials_key()
        self.cipher = Fernet(key)
    
    def _get_or_create_credentials_key(self) -> bytes:
        if Config.ENCRYPTION_KEY:
            try:
                key_bytes = base64.b64decode(Config.ENCRYPTION_KEY)
                if len(key_bytes) == 32:
                    return base64.urlsafe_b64encode(key_bytes)
            except:
                pass
        
        key_file = 'credentials.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        
        return key
    
    def encrypt(self, value: str) -> str:
        if not value:
            return ''
        
        encrypted = self.cipher.encrypt(value.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_value: str) -> str:
        if not encrypted_value:
            return ''
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_value)
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except:
            return ''
