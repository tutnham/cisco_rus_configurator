"""
SSH Client for connecting to Cisco devices
"""

import paramiko
import socket
import time
import logging
import threading
from typing import Optional, Tuple

class SSHClient:
    def __init__(self):
        self.client = None
        self.shell = None
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        
    def connect(self, hostname: str, username: str, password: str, port: int = 22, timeout: int = 10) -> bool:
        """
        Connect to SSH device
        
        Args:
            hostname: Device IP address or hostname
            username: SSH username
            password: SSH password
            port: SSH port (default 22)
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.logger.info(f"Connecting to {hostname}:{port}")
            
            # Connect to the device
            self.client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Create interactive shell
            self.shell = self.client.invoke_shell()
            self.shell.settimeout(timeout)
            
            # Wait for initial prompt
            time.sleep(2)
            
            # Clear initial output
            if self.shell.recv_ready():
                self.shell.recv(4096)
                
            # Disable paging
            self._send_command_raw("terminal length 0")
            time.sleep(1)
            
            # Clear output after terminal length command
            if self.shell.recv_ready():
                self.shell.recv(4096)
            
            self.connected = True
            self.logger.info(f"Successfully connected to {hostname}")
            return True
            
        except (paramiko.AuthenticationException, 
                paramiko.SSHException, 
                socket.error, 
                Exception) as e:
            self.logger.error(f"Failed to connect to {hostname}: {e}")
            self.disconnect()
            return False
            
    def disconnect(self):
        """Disconnect from the device"""
        with self.lock:
            try:
                if self.shell:
                    self.shell.close()
                    self.shell = None
                    
                if self.client:
                    self.client.close()
                    self.client = None
                    
                self.connected = False
                self.logger.info("Disconnected from device")
                
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
                
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
        if not self.connected or not self.shell:
            raise Exception("Not connected to device")
            
        with self.lock:
            try:
                self.logger.debug(f"Executing command: {command}")
                
                # Send command
                self._send_command_raw(command)
                
                # Wait for command to complete and collect output
                output = self._receive_output(timeout)
                
                # Clean up the output
                cleaned_output = self._clean_output(output, command)
                
                self.logger.debug(f"Command executed successfully, output length: {len(cleaned_output)}")
                return cleaned_output
                
            except Exception as e:
                self.logger.error(f"Failed to execute command '{command}': {e}")
                raise Exception(f"Command execution failed: {e}")
                
    def _send_command_raw(self, command: str):
        """Send raw command to the device"""
        if self.shell:
            self.shell.send(command + '\n')
            
    def _receive_output(self, timeout: int) -> str:
        """Receive output from the device"""
        output = ""
        end_time = time.time() + timeout
        last_receive_time = time.time()
        
        while time.time() < end_time:
            if self.shell.recv_ready():
                try:
                    data = self.shell.recv(4096).decode('utf-8', errors='ignore')
                    output += data
                    last_receive_time = time.time()
                    
                    # Check for command prompt (indicating command completion)
                    if self._is_prompt_ready(output):
                        break
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error receiving data: {e}")
                    break
            else:
                # If no data for 2 seconds and we have some output, consider it complete
                if time.time() - last_receive_time > 2 and output.strip():
                    break
                time.sleep(0.1)
                
        return output
        
    def _is_prompt_ready(self, output: str) -> bool:
        """Check if the output contains a command prompt indicating completion"""
        # Common Cisco prompts
        prompt_indicators = [
            '#',    # Privileged mode
            '>',    # User mode
            '(config)#',  # Configuration mode
            '(config-if)#',  # Interface configuration
            '(config-router)#',  # Router configuration
        ]
        
        lines = output.strip().split('\n')
        if lines:
            last_line = lines[-1].strip()
            # Check if last line ends with a prompt
            for indicator in prompt_indicators:
                if last_line.endswith(indicator):
                    return True
                    
        return False
        
    def _clean_output(self, output: str, command: str) -> str:
        """Clean and format command output"""
        if not output:
            return ""
            
        lines = output.split('\n')
        cleaned_lines = []
        
        # Remove echo of the command and empty lines at start/end
        skip_command_echo = True
        
        for line in lines:
            line = line.strip('\r')
            
            # Skip the command echo (first occurrence of the command)
            if skip_command_echo and command.strip() in line:
                skip_command_echo = False
                continue
                
            # Skip prompts and empty lines at the beginning
            if not cleaned_lines and (not line.strip() or 
                                    line.strip().endswith('#') or 
                                    line.strip().endswith('>')):
                continue
                
            cleaned_lines.append(line)
            
        # Remove trailing prompt lines
        while cleaned_lines and (cleaned_lines[-1].strip().endswith('#') or 
                               cleaned_lines[-1].strip().endswith('>') or
                               not cleaned_lines[-1].strip()):
            cleaned_lines.pop()
            
        return '\n'.join(cleaned_lines)
        
    def is_connected(self) -> bool:
        """Check if currently connected to a device"""
        return self.connected and self.client and self.shell
        
    def get_device_info(self) -> Optional[dict]:
        """Get basic device information"""
        if not self.is_connected():
            return None
            
        try:
            # Try to get hostname and version
            hostname_output = self.execute_command("show running-config | include hostname")
            version_output = self.execute_command("show version | include Software")
            
            info = {
                'hostname': 'Unknown',
                'software': 'Unknown'
            }
            
            # Parse hostname
            if hostname_output:
                for line in hostname_output.split('\n'):
                    if 'hostname' in line.lower():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            info['hostname'] = parts[1]
                            break
                            
            # Parse software version
            if version_output:
                for line in version_output.split('\n'):
                    if 'software' in line.lower():
                        info['software'] = line.strip()
                        break
                        
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get device info: {e}")
            return None
