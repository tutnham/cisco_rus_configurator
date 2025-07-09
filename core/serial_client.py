"""
Serial Client for connecting to Cisco devices via COM port
"""
import serial
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SerialClient:
    def __init__(self):
        self.connection = None
        self.is_connected = False
        self.port = None
        self.baudrate = None

    def connect(self, port: str, baudrate: int = 115200, timeout: int = 10) -> bool:
        """
        Connect to device via serial port
        
        Args:
            port: COM port (e.g., 'COM1', '/dev/ttyUSB0')
            baudrate: Serial baudrate (default 115200)
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )
            
            if self.connection.is_open:
                self.is_connected = True
                self.port = port
                self.baudrate = baudrate
                logger.info(f"Connected to {port} at {baudrate} baud")
                
                # Send initial command to wake up device
                self.connection.write(b'\r\n')
                time.sleep(0.5)
                
                return True
            else:
                logger.error(f"Failed to open serial port {port}")
                return False
                
        except Exception as e:
            logger.error(f"Serial connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from the device"""
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                logger.info(f"Disconnected from {self.port}")
            
            self.is_connected = False
            self.connection = None
            self.port = None
            self.baudrate = None
            
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
            # Clear input buffer
            self.connection.reset_input_buffer()
            
            # Send command
            command_bytes = (command + '\r\n').encode('utf-8')
            self.connection.write(command_bytes)
            
            # Wait for response
            output = self._receive_output(timeout)
            
            # Clean and return output
            return self._clean_output(output, command)
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise Exception(f"Failed to execute command '{command}': {str(e)}")

    def _receive_output(self, timeout: int) -> str:
        """Receive output from the device"""
        start_time = time.time()
        output = ""
        
        while time.time() - start_time < timeout:
            if self.connection.in_waiting > 0:
                try:
                    data = self.connection.read(self.connection.in_waiting)
                    chunk = data.decode('utf-8', errors='ignore')
                    output += chunk
                    
                    # Check for prompt completion
                    if self._is_prompt_ready(output):
                        break
                        
                except Exception as e:
                    logger.warning(f"Error reading serial data: {e}")
                    
            time.sleep(0.1)
            
        return output

    def _is_prompt_ready(self, output: str) -> bool:
        """Check if the output contains a command prompt indicating completion"""
        prompt_indicators = ['#', '>', '(config)#', '(config-if)#']
        lines = output.strip().split('\n')
        
        if lines:
            last_line = lines[-1].strip()
            return any(last_line.endswith(indicator) for indicator in prompt_indicators)
            
        return False

    def _clean_output(self, output: str, command: str) -> str:
        """Clean and format command output"""
        lines = output.split('\n')
        cleaned_lines = []
        
        # Remove echo of the command and empty lines
        for line in lines:
            stripped = line.strip()
            if stripped and stripped != command and not stripped.endswith('#') and not stripped.endswith('>'):
                cleaned_lines.append(line.rstrip())
        
        return '\n'.join(cleaned_lines)

    def is_connected_status(self) -> bool:
        """Check if currently connected to a device"""
        return self.is_connected and self.connection and self.connection.is_open

    def get_device_info(self) -> Optional[dict]:
        """Get basic device information"""
        if not self.is_connected_status():
            return None
            
        try:
            version_output = self.execute_command('show version')
            return {
                'connection_type': 'serial',
                'port': self.port,
                'baudrate': self.baudrate,
                'device_info': version_output[:200] + '...' if len(version_output) > 200 else version_output
            }
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {
                'connection_type': 'serial',
                'port': self.port,
                'baudrate': self.baudrate,
                'error': str(e)
            }

    @staticmethod
    def get_available_ports():
        """Get list of available serial ports"""
        try:
            import serial.tools.list_ports
            ports = []
            for port in serial.tools.list_ports.comports():
                ports.append({
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid
                })
            return ports
        except Exception as e:
            logger.error(f"Error getting available ports: {e}")
            return []