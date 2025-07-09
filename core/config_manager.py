"""
Configuration Manager for database and application settings
"""

import json
import os
import logging
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        self.database_config = None
        self.app_config = None
        self.load_configs()
        
    def load_configs(self):
        """Загрузить все конфигурационные файлы"""
        try:
            # Загрузить конфигурацию базы данных
            db_config_path = os.path.join(self.config_dir, "database.json")
            if os.path.exists(db_config_path):
                with open(db_config_path, 'r', encoding='utf-8') as f:
                    self.database_config = json.load(f)
            else:
                self.logger.warning(f"Database config not found: {db_config_path}")
                self.database_config = self.get_default_database_config()
                
            # Загрузить конфигурацию приложения
            app_config_path = os.path.join(self.config_dir, "settings.json")
            if os.path.exists(app_config_path):
                with open(app_config_path, 'r', encoding='utf-8') as f:
                    self.app_config = json.load(f)
            else:
                self.logger.warning(f"App config not found: {app_config_path}")
                self.app_config = self.get_default_app_config()
                
        except Exception as e:
            self.logger.error(f"Error loading configs: {e}")
            self.database_config = self.get_default_database_config()
            self.app_config = self.get_default_app_config()
            
    def get_database_config(self) -> Dict[str, Any]:
        """Получить конфигурацию базы данных"""
        return self.database_config.get('postgresql', {})
        
    def get_app_config(self) -> Dict[str, Any]:
        """Получить конфигурацию приложения"""
        return self.app_config
        
    def get_default_database_config(self) -> Dict[str, Any]:
        """Конфигурация базы данных по умолчанию"""
        return {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "database": "cisco_translator",
                "user": "cisco_user",
                "password": "cisco_password_2025"
            }
        }
        
    def get_default_app_config(self) -> Dict[str, Any]:
        """Конфигурация приложения по умолчанию"""
        return {
            "application": {
                "name": "Cisco Translator",
                "version": "1.0.0",
                "description": "Desktop application for Cisco CLI commands with Russian translation interface"
            },
            "ui": {
                "theme": "light",
                "window_geometry": "1200x800",
                "font_family": "Consolas",
                "font_size": 10
            },
            "connection": {
                "default_ssh_port": 22,
                "default_telnet_port": 23,
                "connection_timeout": 10,
                "command_timeout": 30
            },
            "logging": {
                "log_level": "INFO",
                "enable_session_logging": True
            }
        }
        
    def save_config(self, config_type: str, config_data: Dict[str, Any]):
        """Сохранить конфигурацию"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            
            if config_type == "database":
                config_path = os.path.join(self.config_dir, "database.json")
                self.database_config = config_data
            elif config_type == "app":
                config_path = os.path.join(self.config_dir, "settings.json")
                self.app_config = config_data
            else:
                raise ValueError(f"Unknown config type: {config_type}")
                
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Saved {config_type} configuration")
            
        except Exception as e:
            self.logger.error(f"Error saving {config_type} config: {e}")
            raise