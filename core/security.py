"""
Security module for secure password storage and encryption
"""

import os
import json
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional, Dict, Any

class SecureStorage:
    def __init__(self, storage_file: str = "config/secure_storage.dat"):
        self.storage_file = storage_file
        self.logger = logging.getLogger(__name__)
        self._key = None
        self._setup_encryption()
        
    def _setup_encryption(self):
        """Setup encryption key"""
        try:
            # Generate or load master key
            key_file = "config/master.key"
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self._key = f.read()
            else:
                # Generate new key
                self._key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(self._key)
                # Set restrictive permissions on key file
                os.chmod(key_file, 0o600)
                
        except Exception as e:
            self.logger.error(f"Failed to setup encryption: {e}")
            # Fallback to session-only key
            self._key = Fernet.generate_key()
            
    def _get_cipher(self) -> Fernet:
        """Get cipher instance"""
        return Fernet(self._key)
        
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt data string
        
        Args:
            data: Data to encrypt
            
        Returns:
            str: Base64 encoded encrypted data
        """
        try:
            cipher = self._get_cipher()
            encrypted = cipher.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
            
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data string
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            str: Decrypted data
        """
        try:
            cipher = self._get_cipher()
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
            
    def save_connection_data(self, connection_data: Dict[str, Any]):
        """
        Save connection data securely
        
        Args:
            connection_data: Connection information to save
        """
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            # Load existing data
            stored_data = self._load_storage_file()
            
            # Encrypt sensitive fields
            secure_data = connection_data.copy()
            if 'password' in secure_data:
                secure_data['password'] = self.encrypt_data(secure_data['password'])
                
            # Store connection data
            stored_data['connections'] = stored_data.get('connections', {})
            connection_key = f"{secure_data.get('host', 'unknown')}_{secure_data.get('username', 'unknown')}"
            stored_data['connections'][connection_key] = secure_data
            
            # Save to file
            self._save_storage_file(stored_data)
            self.logger.info("Connection data saved securely")
            
        except Exception as e:
            self.logger.error(f"Failed to save connection data: {e}")
            raise
            
    def load_connection_data(self, host: str = None, username: str = None) -> Optional[Dict[str, Any]]:
        """
        Load connection data
        
        Args:
            host: Specific host to load (optional)
            username: Specific username to load (optional)
            
        Returns:
            Dict with connection data or None if not found
        """
        try:
            stored_data = self._load_storage_file()
            connections = stored_data.get('connections', {})
            
            if host and username:
                connection_key = f"{host}_{username}"
                if connection_key in connections:
                    connection_data = connections[connection_key].copy()
                    # Decrypt password if present
                    if 'password' in connection_data:
                        connection_data['password'] = self.decrypt_data(connection_data['password'])
                    return connection_data
            else:
                # Return the most recent connection
                if connections:
                    latest_key = list(connections.keys())[-1]
                    connection_data = connections[latest_key].copy()
                    # Decrypt password if present
                    if 'password' in connection_data:
                        connection_data['password'] = self.decrypt_data(connection_data['password'])
                    return connection_data
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load connection data: {e}")
            return None
            
    def delete_connection_data(self, host: str, username: str) -> bool:
        """
        Delete stored connection data
        
        Args:
            host: Host to delete
            username: Username to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            stored_data = self._load_storage_file()
            connections = stored_data.get('connections', {})
            
            connection_key = f"{host}_{username}"
            if connection_key in connections:
                del connections[connection_key]
                self._save_storage_file(stored_data)
                self.logger.info(f"Deleted connection data for {host}_{username}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete connection data: {e}")
            return False
            
    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all stored connections (without passwords)
        
        Returns:
            Dict with all connection data (passwords removed)
        """
        try:
            stored_data = self._load_storage_file()
            connections = stored_data.get('connections', {})
            
            # Remove passwords from response for security
            safe_connections = {}
            for key, conn_data in connections.items():
                safe_data = conn_data.copy()
                if 'password' in safe_data:
                    del safe_data['password']
                safe_connections[key] = safe_data
                
            return safe_connections
            
        except Exception as e:
            self.logger.error(f"Failed to get connections: {e}")
            return {}
            
    def save_application_settings(self, settings: Dict[str, Any]):
        """
        Save application settings
        
        Args:
            settings: Settings dictionary to save
        """
        try:
            stored_data = self._load_storage_file()
            stored_data['settings'] = settings
            self._save_storage_file(stored_data)
            self.logger.info("Application settings saved")
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            raise
            
    def load_application_settings(self) -> Dict[str, Any]:
        """
        Load application settings
        
        Returns:
            Dict with application settings
        """
        try:
            stored_data = self._load_storage_file()
            return stored_data.get('settings', {})
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            return {}
            
    def _load_storage_file(self) -> Dict[str, Any]:
        """Load data from storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load storage file: {e}")
                
        return {}
        
    def _save_storage_file(self, data: Dict[str, Any]):
        """Save data to storage file"""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Set restrictive permissions
        os.chmod(self.storage_file, 0o600)
        
    def clear_all_data(self) -> bool:
        """
        Clear all stored data (for security purposes)
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
                
            key_file = "config/master.key"
            if os.path.exists(key_file):
                os.remove(key_file)
                
            self.logger.info("All stored data cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear data: {e}")
            return False
            
    def export_settings(self, filepath: str, include_passwords: bool = False) -> bool:
        """
        Export settings to file
        
        Args:
            filepath: Path to export file
            include_passwords: Whether to include encrypted passwords
            
        Returns:
            bool: True if exported successfully
        """
        try:
            stored_data = self._load_storage_file()
            export_data = stored_data.copy()
            
            if not include_passwords and 'connections' in export_data:
                # Remove passwords from export
                for conn_key, conn_data in export_data['connections'].items():
                    if 'password' in conn_data:
                        del conn_data['password']
                        
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Settings exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return False
            
    def import_settings(self, filepath: str) -> bool:
        """
        Import settings from file
        
        Args:
            filepath: Path to import file
            
        Returns:
            bool: True if imported successfully
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            # Merge with existing data
            stored_data = self._load_storage_file()
            
            # Import connections
            if 'connections' in import_data:
                stored_data['connections'] = stored_data.get('connections', {})
                stored_data['connections'].update(import_data['connections'])
                
            # Import settings
            if 'settings' in import_data:
                stored_data['settings'] = stored_data.get('settings', {})
                stored_data['settings'].update(import_data['settings'])
                
            self._save_storage_file(stored_data)
            self.logger.info(f"Settings imported from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return False
