import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from config import Config

class Encryptor:
    def __init__(self, key: str = None):
        if key:
            self.key = base64.b64decode(key)
        elif Config.ENCRYPTION_KEY:
            self.key = base64.b64decode(Config.ENCRYPTION_KEY)
        else:
            self.key = os.urandom(32)
    
    @staticmethod
    def generate_key() -> str:
        key = os.urandom(32)
        return base64.b64encode(key).decode('utf-8')
    
    def encrypt_file(self, input_file: str, output_file: str):
        iv = os.urandom(16)
        
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        with open(input_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                f_out.write(iv)
                
                padder = padding.PKCS7(128).padder()
                
                while True:
                    chunk = f_in.read(64 * 1024)
                    if not chunk:
                        break
                    
                    padded_chunk = padder.update(chunk)
                    encrypted_chunk = encryptor.update(padded_chunk)
                    f_out.write(encrypted_chunk)
                
                final_padded = padder.finalize()
                final_encrypted = encryptor.update(final_padded) + encryptor.finalize()
                f_out.write(final_encrypted)
    
    def decrypt_file(self, input_file: str, output_file: str):
        with open(input_file, 'rb') as f_in:
            iv = f_in.read(16)
            
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            with open(output_file, 'wb') as f_out:
                unpadder = padding.PKCS7(128).unpadder()
                
                while True:
                    chunk = f_in.read(64 * 1024)
                    if not chunk:
                        break
                    
                    decrypted_chunk = decryptor.update(chunk)
                    unpadded_chunk = unpadder.update(decrypted_chunk)
                    f_out.write(unpadded_chunk)
                
                final_decrypted = decryptor.finalize()
                final_unpadded = unpadder.update(final_decrypted) + unpadder.finalize()
                f_out.write(final_unpadded)
