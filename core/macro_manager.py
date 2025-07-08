"""
Macro Manager for handling frequently used command sets
"""

import json
import os
import logging
from typing import List, Dict, Optional

class MacroManager:
    def __init__(self, macros_file: str = "data/macros.json"):
        self.macros_file = macros_file
        self.macros = {}
        self.logger = logging.getLogger(__name__)
        self.load_macros()
        
    def load_macros(self):
        """Load macros from JSON file"""
        try:
            if os.path.exists(self.macros_file):
                with open(self.macros_file, 'r', encoding='utf-8') as f:
                    self.macros = json.load(f)
                self.logger.info(f"Loaded {len(self.macros)} macros")
            else:
                self.logger.info("Macros file not found, creating default macros")
                self._create_default_macros()
        except Exception as e:
            self.logger.error(f"Failed to load macros: {e}")
            self._create_default_macros()
            
    def _create_default_macros(self):
        """Create default macros"""
        self.macros = {
            "basic_info": {
                "name": "Базовая информация",
                "description": "Получить основную информацию об устройстве",
                "commands": [
                    "show version",
                    "show ip interface brief",
                    "show running-config | include hostname"
                ],
                "created_date": "2025-01-01",
                "author": "system"
            },
            "interface_status": {
                "name": "Статус интерфейсов",
                "description": "Проверить состояние всех интерфейсов",
                "commands": [
                    "show interfaces",
                    "show ip interface brief",
                    "show interfaces status"
                ],
                "created_date": "2025-01-01",
                "author": "system"
            },
            "routing_info": {
                "name": "Информация о маршрутизации",
                "description": "Получить информацию о маршрутизации",
                "commands": [
                    "show ip route",
                    "show ip protocols",
                    "show arp"
                ],
                "created_date": "2025-01-01",
                "author": "system"
            },
            "security_check": {
                "name": "Проверка безопасности",
                "description": "Проверить настройки безопасности",
                "commands": [
                    "show running-config | include username",
                    "show running-config | include enable",
                    "show running-config | include access-list",
                    "show line"
                ],
                "created_date": "2025-01-01",
                "author": "system"
            },
            "save_config": {
                "name": "Сохранить конфигурацию",
                "description": "Сохранить текущую конфигурацию",
                "commands": [
                    "copy running-config startup-config"
                ],
                "created_date": "2025-01-01",
                "author": "system"
            }
        }
        
        self.save_macros()
        
    def save_macros(self):
        """Save macros to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.macros_file), exist_ok=True)
            with open(self.macros_file, 'w', encoding='utf-8') as f:
                json.dump(self.macros, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Macros saved to {self.macros_file}")
        except Exception as e:
            self.logger.error(f"Failed to save macros: {e}")
            
    def get_all_macros(self) -> Dict:
        """Get all macros"""
        return self.macros
        
    def get_macro(self, macro_name: str) -> Optional[Dict]:
        """Get a specific macro by name"""
        return self.macros.get(macro_name)
        
    def create_macro(self, name: str, description: str, commands: List[str], author: str = "user") -> bool:
        """
        Create a new macro
        
        Args:
            name: Macro name (must be unique)
            description: Macro description
            commands: List of commands to execute
            author: Macro author
            
        Returns:
            bool: True if created successfully, False if name already exists
        """
        if name in self.macros:
            self.logger.warning(f"Macro '{name}' already exists")
            return False
            
        from datetime import datetime
        
        self.macros[name] = {
            "name": name,
            "description": description,
            "commands": commands,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "author": author
        }
        
        self.save_macros()
        self.logger.info(f"Created macro '{name}' with {len(commands)} commands")
        return True
        
    def update_macro(self, name: str, description: str = None, commands: List[str] = None) -> bool:
        """
        Update an existing macro
        
        Args:
            name: Macro name
            description: New description (optional)
            commands: New command list (optional)
            
        Returns:
            bool: True if updated successfully, False if macro doesn't exist
        """
        if name not in self.macros:
            self.logger.warning(f"Macro '{name}' not found")
            return False
            
        if description is not None:
            self.macros[name]["description"] = description
            
        if commands is not None:
            self.macros[name]["commands"] = commands
            
        from datetime import datetime
        self.macros[name]["modified_date"] = datetime.now().strftime("%Y-%m-%d")
        
        self.save_macros()
        self.logger.info(f"Updated macro '{name}'")
        return True
        
    def delete_macro(self, name: str) -> bool:
        """
        Delete a macro
        
        Args:
            name: Macro name
            
        Returns:
            bool: True if deleted successfully, False if macro doesn't exist
        """
        if name not in self.macros:
            self.logger.warning(f"Macro '{name}' not found")
            return False
            
        del self.macros[name]
        self.save_macros()
        self.logger.info(f"Deleted macro '{name}'")
        return True
        
    def duplicate_macro(self, original_name: str, new_name: str) -> bool:
        """
        Duplicate an existing macro with a new name
        
        Args:
            original_name: Name of macro to duplicate
            new_name: Name for the new macro
            
        Returns:
            bool: True if duplicated successfully, False otherwise
        """
        if original_name not in self.macros:
            self.logger.warning(f"Original macro '{original_name}' not found")
            return False
            
        if new_name in self.macros:
            self.logger.warning(f"Macro '{new_name}' already exists")
            return False
            
        original_macro = self.macros[original_name]
        
        return self.create_macro(
            name=new_name,
            description=f"Copy of {original_macro['description']}",
            commands=original_macro["commands"].copy(),
            author=original_macro.get("author", "user")
        )
        
    def get_macro_names(self) -> List[str]:
        """Get list of all macro names"""
        return list(self.macros.keys())
        
    def search_macros(self, search_term: str) -> List[str]:
        """
        Search for macros by name or description
        
        Args:
            search_term: Term to search for
            
        Returns:
            List[str]: List of matching macro names
        """
        search_term = search_term.lower()
        results = []
        
        for name, macro in self.macros.items():
            if (search_term in name.lower() or 
                search_term in macro["description"].lower()):
                results.append(name)
                
        return results
        
    def export_macro(self, name: str, filepath: str) -> bool:
        """
        Export a macro to a file
        
        Args:
            name: Macro name
            filepath: Path to save the macro
            
        Returns:
            bool: True if exported successfully, False otherwise
        """
        if name not in self.macros:
            self.logger.warning(f"Macro '{name}' not found")
            return False
            
        try:
            macro_data = {name: self.macros[name]}
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(macro_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Exported macro '{name}' to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export macro '{name}': {e}")
            return False
            
    def import_macro(self, filepath: str) -> bool:
        """
        Import a macro from a file
        
        Args:
            filepath: Path to the macro file
            
        Returns:
            bool: True if imported successfully, False otherwise
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
                
            imported_count = 0
            for name, macro_data in imported_data.items():
                if name not in self.macros:
                    self.macros[name] = macro_data
                    imported_count += 1
                else:
                    self.logger.warning(f"Macro '{name}' already exists, skipping")
                    
            if imported_count > 0:
                self.save_macros()
                self.logger.info(f"Imported {imported_count} macros from {filepath}")
                return True
            else:
                self.logger.info("No new macros to import")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to import macros from {filepath}: {e}")
            return False
            
    def validate_macro(self, macro_data: Dict) -> bool:
        """
        Validate macro data structure
        
        Args:
            macro_data: Macro data dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["name", "description", "commands"]
        
        for field in required_fields:
            if field not in macro_data:
                self.logger.error(f"Macro validation failed: missing field '{field}'")
                return False
                
        if not isinstance(macro_data["commands"], list):
            self.logger.error("Macro validation failed: 'commands' must be a list")
            return False
            
        if not macro_data["commands"]:
            self.logger.error("Macro validation failed: 'commands' list cannot be empty")
            return False
            
        return True
