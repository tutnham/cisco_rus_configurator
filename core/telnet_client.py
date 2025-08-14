"""
Telnet Client for connecting to Cisco devices
"""
import socket
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TelnetClient:
    def __init__(self):
        self.connection = None
        self.is_connected = False
        self.host = None
        self.port = None

    def connect(self, hostname: str, username: str, password: str, port: int = 23, timeout: int = 10) -> bool:
        """
        Connect to Telnet device
        
        Args:
            hostname: Device IP address or hostname
            username: Telnet username
            password: Telnet password
            port: Telnet port (default 23)
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create socket connection
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(timeout)
            self.connection.connect((hostname, port))
            
            # Simple telnet simulation - in real implementation would need proper telnet protocol
            self.is_connected = True
            self.host = hostname
            self.port = port
            logger.info(f"Connected to {hostname}:{port} via Telnet (simplified)")
            return True
                
        except Exception as e:
            logger.error(f"Telnet connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from the device"""
        try:
            if self.connection:
                self.connection.close()
                logger.info(f"Disconnected from {self.host}")
            
            self.is_connected = False
            self.connection = None
            self.host = None
            self.port = None
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def execute_command(self, command: str, timeout: int = 30) -> str:
        """
        Execute a command on the device
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            str: Command output
            
        Raises:
            Exception: If not connected or command fails
        """
        if not self.is_connected or not self.connection:
            raise Exception("Not connected to device")
            
        try:
            # Simplified command execution for demo
            # In real implementation would need proper telnet protocol handling
            logger.info(f"Executing command via Telnet: {command}")
            
            # Return simulated output
            return f"Telnet simulation - executed: {command}\nDevice response would appear here"
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise Exception(f"Failed to execute command '{command}': {str(e)}")

    def _clean_output(self, output: str, command: str) -> str:
        """Clean and format command output"""
        lines = output.split('\n')
        cleaned_lines = []
        
        # Remove echo of the command and prompt
        for line in lines:
            stripped = line.strip()
            if stripped and stripped != command and not stripped.endswith('#'):
                cleaned_lines.append(line.rstrip())
        
        return '\n'.join(cleaned_lines)

    def is_connected_status(self) -> bool:
        """Check if currently connected to a device"""
        return self.is_connected and self.connection is not None

    def get_device_info(self) -> Optional[dict]:
        """Get basic device information"""
        if not self.is_connected_status():
            return None
            
        try:
            version_output = self.execute_command('show version')
            return {
                'connection_type': 'telnet',
                'host': self.host,
                'port': self.port,
                'device_info': version_output[:200] + '...' if len(version_output) > 200 else version_output
            }
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {
                'connection_type': 'telnet',
                'host': self.host,
                'port': self.port,
                'error': str(e)
            }