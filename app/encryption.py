import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class AESCipher:
    def __init__(self, key=None):
        # Ensure key is 32 bytes for AES-256
        key_str = key or os.environ.get('ENCRYPTION_KEY')
        if not key_str:
            raise ValueError("ENCRYPTION_KEY environment variable is not set")
            
        try:
            self.key = base64.urlsafe_b64decode(key_str)
        except Exception:
            # Handle case where key might not be base64 encoded (though it should be)
            # or if it's passed as raw bytes
            if isinstance(key_str, bytes):
                self.key = key_str
            else:
                self.key = key_str.encode()
                
        if len(self.key) != 32:
            # If decoding failed to produce 32 bytes, maybe the input was already 32 bytes raw?
            # But for security, we expect a proper 32-byte key. 
            # Let's be strict: the key from env should be base64 encoded 32 bytes.
            raise ValueError(f"Key must be 32 bytes for AES-256. Got {len(self.key)} bytes.")

    def encrypt(self, raw_data):
        if raw_data is None:
            return None
        # Generate a random 12-byte nonce (IV)
        nonce = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(raw_data.encode()) + encryptor.finalize()
        # Return nonce + tag + ciphertext encoded in base64
        return base64.b64encode(nonce + encryptor.tag + ciphertext).decode('utf-8')

    def decrypt(self, enc_data):
        if enc_data is None:
            return None
        try:
            data = base64.b64decode(enc_data)
            nonce = data[:12]
            tag = data[12:28]
            ciphertext = data[28:]
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return (decryptor.update(ciphertext) + decryptor.finalize()).decode('utf-8')
        except Exception:
            return None  # Handle decryption failure
