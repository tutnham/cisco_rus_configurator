"""
Command Manager for handling Cisco CLI commands with Russian translations
"""

import json
import os
import logging
from typing import List, Dict, Optional

class CommandManager:
    def __init__(self, commands_file: str = "data/commands.json"):
        self.commands_file = commands_file
        self.commands = {}
        self.logger = logging.getLogger(__name__)
        self.load_commands()
        
    def load_commands(self):
        """Load commands from JSON file"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r', encoding='utf-8') as f:
                    self.commands = json.load(f)
                self.logger.info(f"Loaded {len(self.commands)} command categories")
            else:
                self.logger.warning(f"Commands file not found: {self.commands_file}")
                self._create_default_commands()
        except Exception as e:
            self.logger.error(f"Failed to load commands: {e}")
            self._create_default_commands()
            
    def _create_default_commands(self):
        """Create default command structure if file doesn't exist"""
        self.commands = {
            "show_commands": {
                "name": "Команды отображения (Show)",
                "description": "Команды для просмотра информации об устройстве",
                "commands": [
                    {
                        "command": "show version",
                        "description": "Показать версию ПО и информацию об устройстве",
                        "category": "show_commands"
                    },
                    {
                        "command": "show running-config",
                        "description": "Показать текущую конфигурацию",
                        "category": "show_commands"
                    },
                    {
                        "command": "show ip interface brief",
                        "description": "Показать краткую информацию об IP интерфейсах",
                        "category": "show_commands"
                    },
                    {
                        "command": "show interfaces",
                        "description": "Показать состояние всех интерфейсов",
                        "category": "show_commands"
                    },
                    {
                        "command": "show ip route",
                        "description": "Показать таблицу маршрутизации",
                        "category": "show_commands"
                    },
                    {
                        "command": "show arp",
                        "description": "Показать ARP таблицу",
                        "category": "show_commands"
                    },
                    {
                        "command": "show mac address-table",
                        "description": "Показать таблицу MAC адресов",
                        "category": "show_commands"
                    },
                    {
                        "command": "show vlan",
                        "description": "Показать информацию о VLAN",
                        "category": "show_commands"
                    }
                ]
            },
            "interface_config": {
                "name": "Настройка интерфейсов",
                "description": "Команды для настройки сетевых интерфейсов",
                "commands": [
                    {
                        "command": "configure terminal",
                        "description": "Войти в режим глобальной конфигурации",
                        "category": "interface_config"
                    },
                    {
                        "command": "interface GigabitEthernet0/0",
                        "description": "Войти в настройку интерфейса GigabitEthernet0/0",
                        "category": "interface_config"
                    },
                    {
                        "command": "ip address 192.168.1.1 255.255.255.0",
                        "description": "Назначить IP адрес интерфейсу",
                        "category": "interface_config"
                    },
                    {
                        "command": "no shutdown",
                        "description": "Включить интерфейс",
                        "category": "interface_config"
                    },
                    {
                        "command": "shutdown",
                        "description": "Выключить интерфейс",
                        "category": "interface_config"
                    },
                    {
                        "command": "description CONNECTION_TO_ROUTER",
                        "description": "Добавить описание интерфейса",
                        "category": "interface_config"
                    },
                    {
                        "command": "duplex full",
                        "description": "Установить полный дуплекс",
                        "category": "interface_config"
                    },
                    {
                        "command": "speed 100",
                        "description": "Установить скорость 100 Мбит/с",
                        "category": "interface_config"
                    }
                ]
            },
            "routing": {
                "name": "Маршрутизация",
                "description": "Команды для настройки маршрутизации",
                "commands": [
                    {
                        "command": "ip route 0.0.0.0 0.0.0.0 192.168.1.1",
                        "description": "Добавить маршрут по умолчанию",
                        "category": "routing"
                    },
                    {
                        "command": "router ospf 1",
                        "description": "Настроить OSPF процесс 1",
                        "category": "routing"
                    },
                    {
                        "command": "router eigrp 100",
                        "description": "Настроить EIGRP процесс 100",
                        "category": "routing"
                    },
                    {
                        "command": "network 192.168.1.0 0.0.0.255 area 0",
                        "description": "Объявить сеть в OSPF area 0",
                        "category": "routing"
                    },
                    {
                        "command": "redistribute connected",
                        "description": "Перераспределить подключенные маршруты",
                        "category": "routing"
                    },
                    {
                        "command": "show ip protocols",
                        "description": "Показать протоколы маршрутизации",
                        "category": "routing"
                    }
                ]
            },
            "security": {
                "name": "Безопасность",
                "description": "Команды для настройки безопасности",
                "commands": [
                    {
                        "command": "username admin privilege 15 secret cisco123",
                        "description": "Создать пользователя admin с привилегиями",
                        "category": "security"
                    },
                    {
                        "command": "enable secret cisco123",
                        "description": "Установить пароль привилегированного режима",
                        "category": "security"
                    },
                    {
                        "command": "service password-encryption",
                        "description": "Включить шифрование паролей",
                        "category": "security"
                    },
                    {
                        "command": "access-list 1 permit 192.168.1.0 0.0.0.255",
                        "description": "Создать ACL для разрешения сети",
                        "category": "security"
                    },
                    {
                        "command": "banner motd # Unauthorized access prohibited #",
                        "description": "Установить баннер при входе",
                        "category": "security"
                    },
                    {
                        "command": "line vty 0 4",
                        "description": "Настроить виртуальные терминалы",
                        "category": "security"
                    },
                    {
                        "command": "transport input ssh",
                        "description": "Разрешить только SSH подключения",
                        "category": "security"
                    }
                ]
            },
            "diagnostics": {
                "name": "Диагностика",
                "description": "Команды для диагностики и устранения неисправностей",
                "commands": [
                    {
                        "command": "ping 8.8.8.8",
                        "description": "Проверить связность с 8.8.8.8",
                        "category": "diagnostics"
                    },
                    {
                        "command": "traceroute 8.8.8.8",
                        "description": "Проследить маршрут до 8.8.8.8",
                        "category": "diagnostics"
                    },
                    {
                        "command": "show logging",
                        "description": "Показать системные логи",
                        "category": "diagnostics"
                    },
                    {
                        "command": "show processes cpu",
                        "description": "Показать использование CPU",
                        "category": "diagnostics"
                    },
                    {
                        "command": "show memory",
                        "description": "Показать использование памяти",
                        "category": "diagnostics"
                    },
                    {
                        "command": "debug ip packet",
                        "description": "Включить отладку IP пакетов",
                        "category": "diagnostics"
                    },
                    {
                        "command": "undebug all",
                        "description": "Выключить всю отладку",
                        "category": "diagnostics"
                    },
                    {
                        "command": "show tech-support",
                        "description": "Собрать техническую информацию",
                        "category": "diagnostics"
                    }
                ]
            },
            "device_management": {
                "name": "Управление устройством",
                "description": "Команды для управления устройством",
                "commands": [
                    {
                        "command": "copy running-config startup-config",
                        "description": "Сохранить конфигурацию",
                        "category": "device_management"
                    },
                    {
                        "command": "erase startup-config",
                        "description": "Очистить сохраненную конфигурацию",
                        "category": "device_management"
                    },
                    {
                        "command": "reload",
                        "description": "Перезагрузить устройство",
                        "category": "device_management"
                    },
                    {
                        "command": "clock set 14:30:00 15 Dec 2023",
                        "description": "Установить дату и время",
                        "category": "device_management"
                    },
                    {
                        "command": "hostname Router1",
                        "description": "Установить имя устройства",
                        "category": "device_management"
                    },
                    {
                        "command": "copy tftp running-config",
                        "description": "Загрузить конфигурацию по TFTP",
                        "category": "device_management"
                    },
                    {
                        "command": "show flash",
                        "description": "Показать содержимое flash памяти",
                        "category": "device_management"
                    }
                ]
            }
        }
        
        # Save default commands to file
        self.save_commands()
        
    def save_commands(self):
        """Save commands to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.commands_file), exist_ok=True)
            with open(self.commands_file, 'w', encoding='utf-8') as f:
                json.dump(self.commands, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Commands saved to {self.commands_file}")
        except Exception as e:
            self.logger.error(f"Failed to save commands: {e}")
            
    def get_categories(self) -> List[str]:
        """Get list of command categories"""
        return [self.commands[cat]["name"] for cat in self.commands.keys()]
        
    def get_category_key_by_name(self, category_name: str) -> Optional[str]:
        """Get category key by display name"""
        for key, value in self.commands.items():
            if value["name"] == category_name:
                return key
        return None
        
    def get_commands_by_category(self, category_name: str) -> List[Dict]:
        """Get commands for a specific category"""
        category_key = self.get_category_key_by_name(category_name)
        if category_key and category_key in self.commands:
            return self.commands[category_key]["commands"]
        return []
        
    def get_all_commands(self) -> Dict:
        """Get all commands"""
        return self.commands
        
    def add_command(self, category: str, command: str, description: str):
        """Add a new command to a category"""
        if category not in self.commands:
            self.commands[category] = {
                "name": category,
                "description": f"Команды категории {category}",
                "commands": []
            }
            
        new_command = {
            "command": command,
            "description": description,
            "category": category
        }
        
        self.commands[category]["commands"].append(new_command)
        self.save_commands()
        self.logger.info(f"Added command '{command}' to category '{category}'")
        
    def remove_command(self, category: str, command: str):
        """Remove a command from a category"""
        if category in self.commands:
            commands_list = self.commands[category]["commands"]
            self.commands[category]["commands"] = [
                cmd for cmd in commands_list if cmd["command"] != command
            ]
            self.save_commands()
            self.logger.info(f"Removed command '{command}' from category '{category}'")
            
    def search_commands(self, search_term: str) -> List[Dict]:
        """Search for commands containing the search term"""
        results = []
        search_term = search_term.lower()
        
        for category_data in self.commands.values():
            for command in category_data["commands"]:
                if (search_term in command["command"].lower() or 
                    search_term in command["description"].lower()):
                    results.append(command)
                    
        return results
        
    def get_command_by_description(self, description: str) -> Optional[Dict]:
        """Get command by its description"""
        for category_data in self.commands.values():
            for command in category_data["commands"]:
                if command["description"] == description:
                    return command
        return None
