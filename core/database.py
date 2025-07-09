"""
Database connection and management for PostgreSQL
"""

import psycopg2
import psycopg2.extras
import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

class DatabaseManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self.connect()
        
    def connect(self):
        """Подключение к базе данных PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database', 'cisco_translator'),
                user=self.config.get('user', 'cisco_user'),
                password=self.config.get('password', 'cisco_password_2025')
            )
            self.connection.autocommit = True
            self.logger.info("Подключение к PostgreSQL установлено")
        except Exception as e:
            self.logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise
            
    def disconnect(self):
        """Отключение от базы данных"""
        if self.connection:
            self.connection.close()
            self.logger.info("Отключение от PostgreSQL")
            
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Выполнение SQL запроса"""
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []
        except Exception as e:
            self.logger.error(f"Ошибка выполнения запроса: {e}")
            raise
            
    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """Выполнение запроса без возврата данных"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Ошибка выполнения запроса: {e}")
            raise

class PostgreSQLCommandManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
    def get_categories(self) -> List[str]:
        """Получить список категорий команд"""
        query = """
        SELECT DISTINCT category,
               CASE category
                   WHEN 'show_commands' THEN 'Команды отображения (Show)'
                   WHEN 'interface_config' THEN 'Настройка интерфейсов'
                   WHEN 'routing' THEN 'Маршрутизация'
                   WHEN 'security' THEN 'Безопасность'
                   WHEN 'diagnostics' THEN 'Диагностика'
                   WHEN 'device_management' THEN 'Управление устройством'
                   ELSE category
               END as display_name
        FROM commands
        ORDER BY display_name
        """
        results = self.db.execute_query(query)
        return [row['display_name'] for row in results]
        
    def get_category_key_by_name(self, category_name: str) -> Optional[str]:
        """Получить ключ категории по отображаемому имени"""
        category_map = {
            'Команды отображения (Show)': 'show_commands',
            'Настройка интерфейсов': 'interface_config',
            'Маршрутизация': 'routing',
            'Безопасность': 'security',
            'Диагностика': 'diagnostics',
            'Управление устройством': 'device_management'
        }
        return category_map.get(category_name)
        
    def get_commands_by_category(self, category_name: str) -> List[Dict]:
        """Получить команды по категории"""
        category_key = self.get_category_key_by_name(category_name)
        if not category_key:
            return []
            
        query = """
        SELECT command, description, category
        FROM commands
        WHERE category = %s
        ORDER BY description
        """
        return self.db.execute_query(query, (category_key,))
        
    def add_command(self, category: str, command: str, description: str):
        """Добавить новую команду"""
        query = """
        INSERT INTO commands (command, description, category)
        VALUES (%s, %s, %s)
        """
        self.db.execute_non_query(query, (command, description, category))
        self.logger.info(f"Добавлена команда '{command}' в категорию '{category}'")
        
    def remove_command(self, category: str, command: str):
        """Удалить команду"""
        query = """
        DELETE FROM commands
        WHERE category = %s AND command = %s
        """
        rows_affected = self.db.execute_non_query(query, (category, command))
        if rows_affected > 0:
            self.logger.info(f"Удалена команда '{command}' из категории '{category}'")
        
    def search_commands(self, search_term: str) -> List[Dict]:
        """Поиск команд"""
        query = """
        SELECT command, description, category
        FROM commands
        WHERE LOWER(command) LIKE LOWER(%s) OR LOWER(description) LIKE LOWER(%s)
        ORDER BY description
        """
        search_pattern = f"%{search_term}%"
        return self.db.execute_query(query, (search_pattern, search_pattern))

class PostgreSQLMacroManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
    def get_all_macros(self) -> Dict:
        """Получить все макросы"""
        query = """
        SELECT m.name, m.display_name, m.description, m.author, m.created_date,
               ARRAY_AGG(mc.command ORDER BY mc.order_index) as commands
        FROM macros m
        LEFT JOIN macro_commands mc ON m.id = mc.macro_id
        GROUP BY m.id, m.name, m.display_name, m.description, m.author, m.created_date
        ORDER BY m.display_name
        """
        results = self.db.execute_query(query)
        
        macros = {}
        for row in results:
            macros[row['name']] = {
                'name': row['display_name'],
                'description': row['description'],
                'commands': [cmd for cmd in row['commands'] if cmd],
                'created_date': row['created_date'].strftime('%Y-%m-%d') if row['created_date'] else None,
                'author': row['author']
            }
        return macros
        
    def get_macro(self, macro_name: str) -> Optional[Dict]:
        """Получить конкретный макрос"""
        query = """
        SELECT m.name, m.display_name, m.description, m.author, m.created_date,
               ARRAY_AGG(mc.command ORDER BY mc.order_index) as commands
        FROM macros m
        LEFT JOIN macro_commands mc ON m.id = mc.macro_id
        WHERE m.name = %s
        GROUP BY m.id, m.name, m.display_name, m.description, m.author, m.created_date
        """
        results = self.db.execute_query(query, (macro_name,))
        
        if results:
            row = results[0]
            return {
                'name': row['display_name'],
                'description': row['description'],
                'commands': [cmd for cmd in row['commands'] if cmd],
                'created_date': row['created_date'].strftime('%Y-%m-%d') if row['created_date'] else None,
                'author': row['author']
            }
        return None
        
    def create_macro(self, name: str, description: str, commands: List[str], author: str = "user") -> bool:
        """Создать новый макрос"""
        try:
            # Проверить, существует ли макрос
            check_query = "SELECT id FROM macros WHERE name = %s"
            existing = self.db.execute_query(check_query, (name,))
            if existing:
                return False
                
            # Создать макрос
            insert_macro_query = """
            INSERT INTO macros (name, display_name, description, author)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
            result = self.db.execute_query(insert_macro_query, (name, name, description, author))
            macro_id = result[0]['id']
            
            # Добавить команды
            for i, command in enumerate(commands):
                insert_command_query = """
                INSERT INTO macro_commands (macro_id, command, order_index)
                VALUES (%s, %s, %s)
                """
                self.db.execute_non_query(insert_command_query, (macro_id, command, i + 1))
                
            self.logger.info(f"Создан макрос '{name}' с {len(commands)} командами")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка создания макроса: {e}")
            return False
            
    def delete_macro(self, name: str) -> bool:
        """Удалить макрос"""
        try:
            query = "DELETE FROM macros WHERE name = %s"
            rows_affected = self.db.execute_non_query(query, (name,))
            if rows_affected > 0:
                self.logger.info(f"Удален макрос '{name}'")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка удаления макроса: {e}")
            return False

class PostgreSQLHistoryManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
    def log_connection(self, host: str, username: str, connection_type: str, port: int = None) -> int:
        """Записать подключение в историю"""
        query = """
        INSERT INTO connection_history (host, username, connection_type, port)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """
        result = self.db.execute_query(query, (host, username, connection_type, port))
        return result[0]['id']
        
    def log_disconnection(self, connection_id: int):
        """Записать отключение"""
        query = """
        UPDATE connection_history
        SET disconnected_at = CURRENT_TIMESTAMP, status = 'disconnected'
        WHERE id = %s
        """
        self.db.execute_non_query(query, (connection_id,))
        
    def log_command_execution(self, connection_id: int, command: str, description: str, 
                            result: str, execution_time: float = None, success: bool = True):
        """Записать выполнение команды"""
        query = """
        INSERT INTO command_history (connection_id, command, description, result, execution_time, success)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.db.execute_non_query(query, (connection_id, command, description, result, execution_time, success))
        
    def get_command_history(self, limit: int = 100) -> List[Dict]:
        """Получить историю команд"""
        query = """
        SELECT ch.command, ch.description, ch.result, ch.executed_at, ch.success,
               conn.host, conn.username, conn.connection_type
        FROM command_history ch
        JOIN connection_history conn ON ch.connection_id = conn.id
        ORDER BY ch.executed_at DESC
        LIMIT %s
        """
        return self.db.execute_query(query, (limit,))