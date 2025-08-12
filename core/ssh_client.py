"""
SSH Client for connecting to Cisco devices
"""

import paramiko
import socket
import time
import logging
import threading
from typing import Optional, Tuple, Union

class SSHClient:
    def __init__(self, initial_wait: float = 2.0, disable_paging_wait: float = 1.0):
        """
        Initialize SSH client
        
        Args:
            initial_wait: Time to wait after shell creation (default: 2.0s)
            disable_paging_wait: Time to wait after disabling paging (default: 1.0s)
        """
        self.client = None
        self.shell = None
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        self.device_type = None  # Will be detected automatically
        
        # Configurable timeouts for better performance tuning
        self.initial_wait = initial_wait
        self.disable_paging_wait = disable_paging_wait
        
        # Paging disable commands for different vendors
        self.paging_commands = {
            'cisco': 'terminal length 0',
            'eltex': 'terminal length 0',  # Eltex uses Cisco-like commands
            'juniper': 'set cli screen-length 0',
            'huawei': 'screen-length 0 temporary',
            'hp': 'terminal length 0',
            'aruba': 'no paging',
            'mikrotik': ':put [/system resource print]',  # Different approach for MikroTik
            'fortinet': 'config system console\nset output standard\nend',
            'generic': 'terminal length 0'  # Default fallback
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        
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
            
            # Wait for initial prompt - configurable timeout
            time.sleep(self.initial_wait)
            
            # Clear initial output and detect device type
            initial_output = ""
            if self.shell.recv_ready():
                initial_output = self.shell.recv(4096).decode('utf-8', errors='ignore')
                
            # Auto-detect device type from initial prompt/banner
            self.device_type = self._detect_device_type(initial_output)
            self.logger.info(f"Detected device type: {self.device_type}")
            
            # Disable paging with vendor-specific command
            self._disable_paging()
            
            self.connected = True
            self.logger.info(f"Successfully connected to {hostname} (Type: {self.device_type})")
            return True
            
        except paramiko.AuthenticationException as e:
            self.logger.error(f"Authentication failed for {hostname}: {e}")
            self.disconnect()
            return False
        except paramiko.SSHException as e:
            self.logger.error(f"SSH error connecting to {hostname}: {e}")
            self.disconnect()
            return False
        except socket.error as e:
            self.logger.error(f"Network error connecting to {hostname}: {e}")
            self.disconnect()
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to {hostname}: {e}")
            self.disconnect()
            return False
    
    def _detect_device_type(self, initial_output: str) -> str:
        """
        Auto-detect device type from initial output/banner
        
        Args:
            initial_output: Initial banner/prompt from device
            
        Returns:
            str: Detected device type
        """
        output_lower = initial_output.lower()
        
        # Detection patterns for different vendors
        if any(pattern in output_lower for pattern in ['cisco', 'ios', 'nx-os', 'asa']):
            return 'cisco'
        elif any(pattern in output_lower for pattern in ['eltex', 'mes-', 'ltp-', 'tau-']):
            return 'eltex'
        elif any(pattern in output_lower for pattern in ['junos', 'juniper', 'ex-', 'srx-', 'mx-']):
            return 'juniper'
        elif any(pattern in output_lower for pattern in ['huawei', 'vrp', 'versatile routing platform']):
            return 'huawei'
        elif any(pattern in output_lower for pattern in ['hp ', 'hewlett-packard', 'procurve', 'provision']):
            return 'hp'
        elif any(pattern in output_lower for pattern in ['aruba', 'arubaos']):
            return 'aruba'
        elif any(pattern in output_lower for pattern in ['mikrotik', 'routeros']):
            return 'mikrotik'
        elif any(pattern in output_lower for pattern in ['fortinet', 'fortigate', 'fortios']):
            return 'fortinet'
        else:
            self.logger.warning(f"Unknown device type from output: {initial_output[:100]}...")
            return 'generic'
    
    def _disable_paging(self):
        """Disable paging using vendor-specific command"""
        try:
            paging_cmd = self.paging_commands.get(self.device_type, self.paging_commands['generic'])
            
            # Special handling for some vendors
            if self.device_type == 'fortinet':
                # FortiGate requires multiple commands
                for cmd in paging_cmd.split('\n'):
                    if cmd.strip():
                        self._send_command_raw(cmd.strip())
                        time.sleep(0.5)
            elif self.device_type == 'mikrotik':
                # MikroTik doesn't have traditional paging disable
                self.logger.info("MikroTik detected - no paging disable needed")
                return
            else:
                self._send_command_raw(paging_cmd)
                
            time.sleep(self.disable_paging_wait)
            
            # Clear output after paging disable command
            if self.shell.recv_ready():
                self.shell.recv(4096)
                
            self.logger.debug(f"Disabled paging using: {paging_cmd}")
            
        except Exception as e:
            self.logger.warning(f"Failed to disable paging: {e}")
            # Continue anyway - this shouldn't break the connection
            
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
                self.device_type = None
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
                output = self._wait_for_output(timeout)
                
                # Clean and return output
                cleaned_output = self._clean_output(output, command)
                return cleaned_output
                
            except Exception as e:
                self.logger.error(f"Failed to execute command '{command}': {e}")
                raise

    def _send_command_raw(self, command: str):
        """Send raw command to the device"""
        try:
            self.shell.send(command + '\n')
        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
            raise
            
    def _wait_for_output(self, timeout: int) -> str:
        """Wait for command output with timeout"""
        output = ""
        start_time = time.time()
        last_data_time = start_time
        
        while (time.time() - start_time) < timeout:
            if self.shell.recv_ready():
                try:
                    data = self.shell.recv(4096).decode('utf-8', errors='ignore')
                    output += data
                    last_data_time = time.time()
                    
                    # Check for command prompt (indicating command completion)
                    if self._is_prompt_ready(output):
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error receiving data: {e}")
                    break
            else:
                time.sleep(0.1)
                # If no data for 2 seconds and we have some output, consider it complete
                if output and (time.time() - last_data_time) > 2:
                    break
                    
        return output

    def _is_prompt_ready(self, output: str) -> bool:
        """Check if the output contains a command prompt indicating completion"""
        # Common prompt patterns for different vendors
        prompt_patterns = {
            'cisco': ['#', '>', '(config)#', '(config-if)#'],
            'eltex': ['#', '>', '(config)#', '(config-if)#'],
            'juniper': ['>', '#', '% '],
            'huawei': ['<', '>', ']', '#'],
            'hp': ['#', '>', '% '],
            'aruba': ['#', '>', '% '],
            'mikrotik': ['>', '] '],
            'fortinet': ['#', '$ '],
            'generic': ['#', '>', '$ ']
        }
        
        patterns = prompt_patterns.get(self.device_type, prompt_patterns['generic'])
        
        # Check last few lines for prompt
        lines = output.strip().split('\n')
        if lines:
            last_line = lines[-1].strip()
            return any(last_line.endswith(pattern) for pattern in patterns)
        
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
            line = line.strip()
            
            # Skip the command echo (first occurrence of the command)
            if skip_command_echo and command in line:
                skip_command_echo = False
                continue
                
            # Skip empty lines at the beginning
            if not cleaned_lines and not line:
                continue
                
            # Skip common prompt lines
            if any(prompt in line for prompt in ['#', '>', '$ ', '] ']):
                continue
                
            cleaned_lines.append(line)
        
        # Remove empty lines at the end
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
            
        return '\n'.join(cleaned_lines)

    def get_device_info(self) -> dict:
        """
        Get basic device information
        
        Returns:
            dict: Device information including type, version, etc.
        """
        if not self.connected:
            return {"error": "Not connected"}
            
        try:
            # Use appropriate version command based on device type
            version_commands = {
                'cisco': 'show version',
                'eltex': 'show version',
                'juniper': 'show version',
                'huawei': 'display version',
                'hp': 'show version',
                'aruba': 'show version',
                'mikrotik': '/system resource print',
                'fortinet': 'get system status',
                'generic': 'show version'
            }
            
            version_cmd = version_commands.get(self.device_type, 'show version')
            version_output = self.execute_command(version_cmd)
            
            return {
                "device_type": self.device_type,
                "version_command": version_cmd,
                "version_output": version_output,
                "connected": self.connected
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get device info: {e}")
            return {"error": str(e)}

    def execute_vendor_command(self, generic_command: str) -> str:
        """
        Execute a command with vendor-specific translation
        
        Args:
            generic_command: Generic command (e.g., 'show_interfaces')
            
        Returns:
            str: Command output
        """
        # Command translation table
        command_translations = {
            'show_interfaces': {
                'cisco': 'show ip interface brief',
                'eltex': 'show interface brief', 
                'juniper': 'show interfaces terse',
                'huawei': 'display ip interface brief',
                'hp': 'show ip interface brief',
                'aruba': 'show ip interface brief',
                'mikrotik': '/interface print',
                'fortinet': 'get system interface',
                'generic': 'show interfaces'
            },
            'show_routing': {
                'cisco': 'show ip route',
                'eltex': 'show ip route',
                'juniper': 'show route',
                'huawei': 'display ip routing-table',
                'hp': 'show ip route',
                'aruba': 'show ip route',
                'mikrotik': '/ip route print',
                'fortinet': 'get router info routing-table',
                'generic': 'show ip route'
            }
        }
        
        if generic_command in command_translations:
            vendor_command = command_translations[generic_command].get(
                self.device_type, 
                command_translations[generic_command]['generic']
            )
            return self.execute_command(vendor_command)
        else:
            # If no translation available, try the command as-is
            return self.execute_command(generic_command)
