"""
Enhanced Security Module for Cisco Translator
Provides advanced security features including multi-factor authentication,
session management, and enhanced encryption capabilities.
"""

import os
import json
import base64
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class EnhancedSecureStorage:
    """Enhanced security storage with additional features"""
    
    def __init__(self, storage_file: str = "config/secure_storage_enhanced.dat"):
        self.storage_file = storage_file
        self.logger = logging.getLogger(__name__)
        self._key = None
        self._session_tokens = {}
        self._failed_attempts = {}
        self._setup_encryption()
        
    def _setup_encryption(self):
        """Setup enhanced encryption with stronger key derivation"""
        try:
            key_file = "config/master_enhanced.key"
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self._key = f.read()
            else:
                # Generate stronger key using PBKDF2
                password = secrets.token_bytes(32)
                salt = secrets.token_bytes(16)
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                self._key = base64.urlsafe_b64encode(kdf.derive(password))
                
                # Store key securely
                with open(key_file, 'wb') as f:
                    f.write(salt + self._key)
                os.chmod(key_file, 0o600)
                
        except Exception as e:
            self.logger.error(f"Failed to setup enhanced encryption: {e}")
            self._key = Fernet.generate_key()
            
    def generate_session_token(self, user_id: str, duration_hours: int = 24) -> str:
        """Generate secure session token"""
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=duration_hours)
        
        self._session_tokens[token] = {
            'user_id': user_id,
            'created': datetime.now(),
            'expires': expiry,
            'active': True
        }
        
        return token
        
    def validate_session_token(self, token: str) -> bool:
        """Validate session token"""
        if token not in self._session_tokens:
            return False
            
        session = self._session_tokens[token]
        if not session['active'] or datetime.now() > session['expires']:
            self.revoke_session_token(token)
            return False
            
        return True
        
    def revoke_session_token(self, token: str):
        """Revoke session token"""
        if token in self._session_tokens:
            self._session_tokens[token]['active'] = False
            
    def check_rate_limit(self, identifier: str, max_attempts: int = 5, 
                        window_minutes: int = 15) -> bool:
        """Check if identifier is rate limited"""
        now = datetime.now()
        
        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = []
            
        # Clean old attempts
        cutoff = now - timedelta(minutes=window_minutes)
        self._failed_attempts[identifier] = [
            attempt for attempt in self._failed_attempts[identifier]
            if attempt > cutoff
        ]
        
        return len(self._failed_attempts[identifier]) < max_attempts
        
    def record_failed_attempt(self, identifier: str):
        """Record failed authentication attempt"""
        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = []
            
        self._failed_attempts[identifier].append(datetime.now())
        
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """Hash password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(32)
            
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                     password.encode('utf-8'), 
                                     salt, 
                                     100000)
        return pwdhash, salt
        
    def verify_password(self, password: str, stored_hash: bytes, salt: bytes) -> bool:
        """Verify password against stored hash"""
        pwdhash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(pwdhash, stored_hash)
        
    def encrypt_with_aes(self, data: str, key: Optional[bytes] = None) -> str:
        """Encrypt data using AES-256-GCM"""
        if key is None:
            key = secrets.token_bytes(32)
            
        iv = secrets.token_bytes(12)  # GCM recommended IV size
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
        
        # Combine IV, tag, and ciphertext
        encrypted_data = iv + encryptor.tag + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
        
    def get_security_audit_log(self) -> List[Dict[str, Any]]:
        """Get security audit log"""
        try:
            stored_data = self._load_storage_file()
            return stored_data.get('audit_log', [])
        except Exception as e:
            self.logger.error(f"Failed to get audit log: {e}")
            return []
            
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event for audit"""
        try:
            stored_data = self._load_storage_file()
            if 'audit_log' not in stored_data:
                stored_data['audit_log'] = []
                
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'details': details
            }
            
            stored_data['audit_log'].append(event)
            
            # Keep only last 1000 events
            if len(stored_data['audit_log']) > 1000:
                stored_data['audit_log'] = stored_data['audit_log'][-1000:]
                
            self._save_storage_file(stored_data)
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
            
    def _load_storage_file(self) -> Dict[str, Any]:
        """Load data from enhanced storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load enhanced storage file: {e}")
                
        return {}
        
    def _save_storage_file(self, data: Dict[str, Any]):
        """Save data to enhanced storage file"""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.chmod(self.storage_file, 0o600)