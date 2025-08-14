"""
Device Detector - автоматическое определение типа и модели устройства Cisco
"""

import re
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

@dataclass
class DeviceInfo:
    """Информация об устройстве."""
    vendor: str
    model: str
    ios_version: str
    hostname: str
    serial_number: str
    uptime: str
    device_type: str  # router, switch, firewall, etc.
    capabilities: List[str]

class CiscoDeviceDetector:
    """
    Автоматическое определение типа и возможностей устройства Cisco.
    
    Анализирует вывод команд и определяет модель, версию IOS,
    тип устройства и доступные функции.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Паттерны для определения типов устройств
        self.device_patterns = {
            'router': [
                r'cisco.*router',
                r'ISR\d+',
                r'c\d+[rR]',
                r'cisco.*gateway'
            ],
            'switch': [
                r'catalyst.*switch',
                r'WS-C\d+',
                r'cisco.*switch',
                r'c\d+[sS]'
            ],
            'firewall': [
                r'ASA\d+',
                r'PIX\d+',
                r'cisco.*security.*appliance'
            ],
            'wireless': [
                r'AIR-.*-K9',
                r'cisco.*wireless',
                r'WLC\d+'
            ]
        }
        
        # Паттерны для извлечения информации
        self.info_patterns = {
            'model': [
                r'cisco\s+(\S+)\s+\(',
                r'Model\s+number\s*:\s*(\S+)',
                r'Product\s+ID\s*:\s*(\S+)'
            ],
            'ios_version': [
                r'Version\s+([0-9]+\.[0-9]+[^\s,]*)',
                r'IOS.*Version\s+([0-9]+\.[0-9]+[^\s,]*)',
                r'Software.*Version\s+([0-9]+\.[0-9]+[^\s,]*)'
            ],
            'hostname': [
                r'hostname\s+(\S+)',
                r'^(\S+)[#>]',
                r'System\s+ID\s*:\s*(\S+)'
            ],
            'serial': [
                r'Processor\s+board\s+ID\s+(\S+)',
                r'System\s+serial\s+number\s*:\s*(\S+)',
                r'Serial\s+Number\s*:\s*(\S+)'
            ],
            'uptime': [
                r'uptime\s+is\s+(.+)',
                r'System\s+uptime\s*:\s*(.+)'
            ]
        }
    
    def detect_device(self, version_output: str, running_config: str = "") -> DeviceInfo:
        """
        Определить информацию об устройстве по выводу команд.
        
        Args:
            version_output: Вывод команды 'show version'
            running_config: Вывод команды 'show running-config' (опционально)
            
        Returns:
            DeviceInfo: Информация об устройстве
        """
        try:
            device_info = DeviceInfo(
                vendor="Cisco",
                model=self._extract_model(version_output),
                ios_version=self._extract_ios_version(version_output),
                hostname=self._extract_hostname(version_output, running_config),
                serial_number=self._extract_serial(version_output),
                uptime=self._extract_uptime(version_output),
                device_type=self._detect_device_type(version_output),
                capabilities=self._detect_capabilities(version_output, running_config)
            )
            
            self.logger.info(f"Detected device: {device_info.model} ({device_info.device_type})")
            return device_info
            
        except Exception as e:
            self.logger.error(f"Error detecting device: {e}")
            return DeviceInfo(
                vendor="Unknown",
                model="Unknown",
                ios_version="Unknown",
                hostname="Unknown",
                serial_number="Unknown",
                uptime="Unknown",
                device_type="unknown",
                capabilities=[]
            )
    
    def _extract_model(self, version_output: str) -> str:
        """Извлечь модель устройства."""
        for pattern in self.info_patterns['model']:
            match = re.search(pattern, version_output, re.IGNORECASE)
            if match:
                return match.group(1)
        return "Unknown"
    
    def _extract_ios_version(self, version_output: str) -> str:
        """Извлечь версию IOS."""
        for pattern in self.info_patterns['ios_version']:
            match = re.search(pattern, version_output, re.IGNORECASE)
            if match:
                return match.group(1)
        return "Unknown"
    
    def _extract_hostname(self, version_output: str, running_config: str) -> str:
        """Извлечь имя устройства."""
        # Сначала попробуем из running-config
        if running_config:
            for pattern in self.info_patterns['hostname']:
                match = re.search(pattern, running_config, re.IGNORECASE | re.MULTILINE)
                if match:
                    return match.group(1)
        
        # Затем из version
        for pattern in self.info_patterns['hostname']:
            match = re.search(pattern, version_output, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1)
        
        return "Unknown"
    
    def _extract_serial(self, version_output: str) -> str:
        """Извлечь серийный номер."""
        for pattern in self.info_patterns['serial']:
            match = re.search(pattern, version_output, re.IGNORECASE)
            if match:
                return match.group(1)
        return "Unknown"
    
    def _extract_uptime(self, version_output: str) -> str:
        """Извлечь время работы."""
        for pattern in self.info_patterns['uptime']:
            match = re.search(pattern, version_output, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Unknown"
    
    def _detect_device_type(self, version_output: str) -> str:
        """Определить тип устройства."""
        version_lower = version_output.lower()
        
        for device_type, patterns in self.device_patterns.items():
            for pattern in patterns:
                if re.search(pattern, version_lower):
                    return device_type
        
        return "unknown"
    
    def _detect_capabilities(self, version_output: str, running_config: str) -> List[str]:
        """Определить возможности устройства."""
        capabilities = []
        combined_output = (version_output + " " + running_config).lower()
        
        capability_patterns = {
            'routing': [r'ip\s+routing', r'router\s+\w+', r'ip\s+route'],
            'switching': [r'vlan', r'switchport', r'spanning-tree'],
            'wireless': [r'wireless', r'wifi', r'wlan'],
            'security': [r'firewall', r'access-list', r'crypto'],
            'qos': [r'quality.*service', r'traffic.*shaping', r'priority-queue'],
            'vpn': [r'vpn', r'tunnel', r'ipsec'],
            'nat': [r'ip\s+nat', r'translation'],
            'dhcp': [r'dhcp\s+server', r'ip\s+helper'],
            'snmp': [r'snmp-server', r'snmp\s+community'],
            'ssh': [r'ip\s+ssh', r'transport\s+input\s+ssh'],
            'voice': [r'voice', r'telephony', r'dial-peer'],
            'multicast': [r'ip\s+multicast', r'pim', r'igmp']
        }
        
        for capability, patterns in capability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_output):
                    capabilities.append(capability)
                    break
        
        return capabilities
    
    def get_recommended_commands(self, device_info: DeviceInfo) -> List[Dict[str, str]]:
        """
        Получить рекомендованные команды для данного типа устройства.
        
        Args:
            device_info: Информация об устройстве
            
        Returns:
            Список рекомендованных команд
        """
        base_commands = [
            {"command": "show version", "description": "Информация о версии"},
            {"command": "show running-config", "description": "Текущая конфигурация"},
            {"command": "show ip interface brief", "description": "Статус интерфейсов"}
        ]
        
        device_specific_commands = {
            'router': [
                {"command": "show ip route", "description": "Таблица маршрутизации"},
                {"command": "show ip protocols", "description": "Протоколы маршрутизации"},
                {"command": "show interface", "description": "Детали интерфейсов"}
            ],
            'switch': [
                {"command": "show vlan", "description": "Информация о VLAN"},
                {"command": "show mac address-table", "description": "Таблица MAC адресов"},
                {"command": "show spanning-tree", "description": "Spanning Tree Protocol"}
            ],
            'firewall': [
                {"command": "show access-list", "description": "Списки доступа"},
                {"command": "show xlate", "description": "Трансляции адресов"},
                {"command": "show conn", "description": "Активные соединения"}
            ]
        }
        
        commands = base_commands.copy()
        
        if device_info.device_type in device_specific_commands:
            commands.extend(device_specific_commands[device_info.device_type])
        
        # Добавляем команды на основе возможностей
        capability_commands = {
            'routing': [{"command": "show ip route summary", "description": "Сводка маршрутов"}],
            'switching': [{"command": "show interfaces status", "description": "Статус портов"}],
            'wireless': [{"command": "show wireless summary", "description": "Сводка беспроводной сети"}],
            'vpn': [{"command": "show crypto session", "description": "VPN сессии"}],
            'voice': [{"command": "show voice port summary", "description": "Голосовые порты"}]
        }
        
        for capability in device_info.capabilities:
            if capability in capability_commands:
                commands.extend(capability_commands[capability])
        
        return commands
    
    def export_device_info(self, device_info: DeviceInfo, filepath: str) -> bool:
        """
        Экспортировать информацию об устройстве в файл.
        
        Args:
            device_info: Информация об устройстве
            filepath: Путь к файлу
            
        Returns:
            True если успешно, False иначе
        """
        try:
            import json
            
            device_dict = {
                'vendor': device_info.vendor,
                'model': device_info.model,
                'ios_version': device_info.ios_version,
                'hostname': device_info.hostname,
                'serial_number': device_info.serial_number,
                'uptime': device_info.uptime,
                'device_type': device_info.device_type,
                'capabilities': device_info.capabilities,
                'recommended_commands': self.get_recommended_commands(device_info)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(device_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Device info exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export device info: {e}")
            return False