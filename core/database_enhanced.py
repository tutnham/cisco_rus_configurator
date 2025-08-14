"""
Enhanced Database Manager with connection pooling and improved error handling
"""

import psycopg2
import psycopg2.extras
import psycopg2.pool
import logging
import json
import time
import threading
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Конфигурация базы данных."""
    host: str = "localhost"
    port: int = 5432
    database: str = "cisco_translator"
    user: str = "cisco_user"
    password: str = "cisco_password_2025"
    min_connections: int = 1
    max_connections: int = 10
    connection_timeout: int = 30
    query_timeout: int = 30
    auto_reconnect: bool = True
    enable_logging: bool = True

class DatabaseConnectionError(Exception):
    """Ошибка подключения к базе данных."""
    pass

class DatabaseQueryError(Exception):
    """Ошибка выполнения запроса."""
    pass

class EnhancedDatabaseManager:
    """
    Улучшенный менеджер базы данных с пулом соединений.
    
    Особенности:
    - Пул соединений для лучшей производительности
    - Автоматическое переподключение при разрыве соединения
    - Мониторинг состояния подключений
    - Детальное логирование
    - Graceful handling ошибок
    """
    
    def __init__(self, config: Union[Dict[str, Any], DatabaseConfig]):
        """
        Инициализация менеджера базы данных.
        
        Args:
            config: Конфигурация базы данных
        """
        if isinstance(config, dict):
            self.config = DatabaseConfig(**config)
        else:
            self.config = config
            
        self.logger = logging.getLogger(__name__)
        self.connection_pool = None
        self.is_connected = False
        self.connection_lock = threading.RLock()
        self.stats = {
            "total_connections": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "reconnection_attempts": 0,
            "last_error": None
        }
        
        self._initialize_connection_pool()
    
    def _initialize_connection_pool(self):
        """Инициализация пула соединений."""
        try:
            connection_string = (
                f"host={self.config.host} "
                f"port={self.config.port} "
                f"dbname={self.config.database} "
                f"user={self.config.user} "
                f"password={self.config.password}"
            )
            
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.min_connections,
                maxconn=self.config.max_connections,
                dsn=connection_string,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            
            self.is_connected = True
            self.stats["total_connections"] += 1
            
            if self.config.enable_logging:
                self.logger.info(
                    f"Database connection pool initialized: "
                    f"{self.config.min_connections}-{self.config.max_connections} connections"
                )
                
        except (psycopg2.Error, Exception) as e:
            self.stats["last_error"] = str(e)
            self.logger.error(f"Failed to initialize connection pool: {e}")
            raise DatabaseConnectionError(f"Cannot connect to database: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager для получения соединения из пула.
        
        Yields:
            psycopg2.connection: Соединение с базой данных
        """
        connection = None
        try:
            with self.connection_lock:
                if not self.is_connected:
                    self._reconnect()
                
                connection = self.connection_pool.getconn()
                
                if connection.closed:
                    self.connection_pool.putconn(connection, close=True)
                    connection = self.connection_pool.getconn()
                
            yield connection
            
        except (psycopg2.Error, Exception) as e:
            self.stats["last_error"] = str(e)
            self.logger.error(f"Connection error: {e}")
            
            if connection and not connection.closed:
                connection.rollback()
            
            # Попытка переподключения при определенных ошибках
            if self._should_reconnect(e):
                self._reconnect()
            
            raise DatabaseConnectionError(f"Database connection failed: {e}")
            
        finally:
            if connection:
                try:
                    self.connection_pool.putconn(connection)
                except Exception as e:
                    self.logger.warning(f"Error returning connection to pool: {e}")
    
    @contextmanager
    def get_cursor(self, connection=None, cursor_factory=None):
        """
        Context manager для получения курсора.
        
        Args:
            connection: Существующее соединение (опционально)
            cursor_factory: Фабрика для создания курсора
            
        Yields:
            psycopg2.cursor: Курсор базы данных
        """
        if connection:
            # Используем переданное соединение
            cursor = None
            try:
                cursor_factory = cursor_factory or psycopg2.extras.RealDictCursor
                cursor = connection.cursor(cursor_factory=cursor_factory)
                yield cursor
            except psycopg2.Error as e:
                self.stats["failed_queries"] += 1
                self.logger.error(f"Cursor error: {e}")
                if connection and not connection.closed:
                    connection.rollback()
                raise DatabaseQueryError(f"Database query failed: {e}")
            finally:
                if cursor:
                    cursor.close()
        else:
            # Получаем соединение из пула
            with self.get_connection() as conn:
                with self.get_cursor(conn, cursor_factory) as cursor:
                    yield cursor
    
    def execute_query(self, query: str, params: tuple = None, 
                     fetch_results: bool = True) -> List[Dict]:
        """
        Выполнить SQL запрос.
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            fetch_results: Возвращать ли результаты
            
        Returns:
            Список результатов в виде словарей
        """
        try:
            with self.get_cursor() as cursor:
                start_time = time.time()
                cursor.execute(query, params)
                execution_time = time.time() - start_time
                
                if self.config.enable_logging and execution_time > 1.0:
                    self.logger.warning(f"Slow query ({execution_time:.2f}s): {query[:100]}...")
                
                if fetch_results and cursor.description:
                    results = [dict(row) for row in cursor.fetchall()]
                    self.stats["successful_queries"] += 1
                    return results
                else:
                    self.stats["successful_queries"] += 1
                    return []
                    
        except (psycopg2.Error, DatabaseConnectionError, DatabaseQueryError) as e:
            self.stats["failed_queries"] += 1
            self.logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
            raise
        except Exception as e:
            self.stats["failed_queries"] += 1
            self.logger.error(f"Unexpected error during query execution: {e}")
            raise DatabaseQueryError(f"Unexpected database error: {e}")
    
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """
        Выполнить несколько запросов в одной транзакции.
        
        Args:
            queries: Список кортежей (query, params)
            
        Returns:
            True если транзакция успешна
        """
        try:
            with self.get_connection() as connection:
                connection.autocommit = False
                
                try:
                    with self.get_cursor(connection) as cursor:
                        for query, params in queries:
                            cursor.execute(query, params)
                    
                    connection.commit()
                    self.stats["successful_queries"] += len(queries)
                    return True
                    
                except Exception as e:
                    connection.rollback()
                    raise e
                finally:
                    connection.autocommit = True
                    
        except (psycopg2.Error, DatabaseConnectionError) as e:
            self.stats["failed_queries"] += len(queries)
            self.logger.error(f"Transaction failed: {e}")
            raise DatabaseQueryError(f"Transaction execution failed: {e}")
    
    def execute_batch(self, query: str, params_list: List[tuple]) -> int:
        """
        Выполнить batch операцию.
        
        Args:
            query: SQL запрос
            params_list: Список параметров для каждого выполнения
            
        Returns:
            Количество обработанных записей
        """
        try:
            with self.get_cursor() as cursor:
                psycopg2.extras.execute_batch(cursor, query, params_list)
                affected_rows = cursor.rowcount
                self.stats["successful_queries"] += 1
                return affected_rows
                
        except (psycopg2.Error, DatabaseConnectionError) as e:
            self.stats["failed_queries"] += 1
            self.logger.error(f"Batch execution failed: {e}")
            raise DatabaseQueryError(f"Batch operation failed: {e}")
    
    def check_connection(self) -> bool:
        """
        Проверить состояние подключения к базе данных.
        
        Returns:
            True если подключение активно
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Получить информацию о базе данных.
        
        Returns:
            Словарь с информацией о БД
        """
        try:
            queries = {
                "version": "SELECT version()",
                "current_database": "SELECT current_database()",
                "current_user": "SELECT current_user",
                "active_connections": """
                    SELECT count(*) as connections 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """,
                "database_size": """
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """
            }
            
            info = {}
            for key, query in queries.items():
                try:
                    result = self.execute_query(query)
                    if result:
                        info[key] = list(result[0].values())[0]
                except Exception as e:
                    info[key] = f"Error: {e}"
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику работы с базой данных.
        
        Returns:
            Словарь со статистикой
        """
        pool_stats = {}
        if self.connection_pool:
            # Получаем статистику пула через приватные атрибуты (осторожно!)
            try:
                pool_stats = {
                    "minconn": self.connection_pool.minconn,
                    "maxconn": self.connection_pool.maxconn,
                    "closed": getattr(self.connection_pool, 'closed', False)
                }
            except Exception:
                pool_stats = {"error": "Cannot get pool statistics"}
        
        return {
            **self.stats,
            "is_connected": self.is_connected,
            "pool_info": pool_stats,
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "database": self.config.database,
                "min_connections": self.config.min_connections,
                "max_connections": self.config.max_connections
            }
        }
    
    def _should_reconnect(self, error: Exception) -> bool:
        """
        Определить, нужно ли выполнять переподключение.
        
        Args:
            error: Произошедшая ошибка
            
        Returns:
            True если нужно переподключение
        """
        if not self.config.auto_reconnect:
            return False
        
        # Ошибки, при которых стоит попробовать переподключение
        reconnect_errors = [
            "server closed the connection unexpectedly",
            "connection to server",
            "could not connect to server",
            "timeout expired",
            "connection timed out"
        ]
        
        error_msg = str(error).lower()
        return any(err in error_msg for err in reconnect_errors)
    
    def _reconnect(self):
        """Выполнить переподключение к базе данных."""
        if not self.config.auto_reconnect:
            return
        
        try:
            self.stats["reconnection_attempts"] += 1
            self.logger.info("Attempting to reconnect to database...")
            
            # Закрываем старый пул
            if self.connection_pool:
                try:
                    self.connection_pool.closeall()
                except Exception:
                    pass
            
            # Создаем новый пул
            self._initialize_connection_pool()
            
            if self.is_connected:
                self.logger.info("Database reconnection successful")
            
        except Exception as e:
            self.is_connected = False
            self.logger.error(f"Reconnection failed: {e}")
            raise DatabaseConnectionError(f"Reconnection failed: {e}")
    
    def close(self):
        """Закрыть все соединения."""
        try:
            if self.connection_pool:
                self.connection_pool.closeall()
                self.connection_pool = None
            
            self.is_connected = False
            self.logger.info("Database connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

# Фабрика для создания менеджера базы данных
def create_database_manager(config_path: Optional[str] = None) -> EnhancedDatabaseManager:
    """
    Создать менеджер базы данных из конфигурационного файла.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Экземпляр EnhancedDatabaseManager
    """
    if config_path:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                postgresql_config = config_data.get('postgresql', {})
                pool_config = config_data.get('connection_pool', {})
                settings_config = config_data.get('settings', {})
                
                # Объединяем все настройки
                combined_config = {**postgresql_config, **pool_config, **settings_config}
                return EnhancedDatabaseManager(combined_config)
        except Exception as e:
            logging.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    # Используем конфигурацию по умолчанию
    return EnhancedDatabaseManager(DatabaseConfig())

# Обновленные менеджеры с использованием нового пула соединений
class EnhancedPostgreSQLCommandManager:
    """Менеджер команд с использованием пула соединений."""
    
    def __init__(self, db_manager: EnhancedDatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_categories(self) -> List[str]:
        """Получить список категорий команд."""
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
    
    def get_commands_by_category(self, category_name: str) -> List[Dict]:
        """Получить команды по категории."""
        category_map = {
            'Команды отображения (Show)': 'show_commands',
            'Настройка интерфейсов': 'interface_config',
            'Маршрутизация': 'routing',
            'Безопасность': 'security',
            'Диагностика': 'diagnostics',
            'Управление устройством': 'device_management'
        }
        
        category_key = category_map.get(category_name)
        if not category_key:
            return []
        
        query = """
        SELECT command, description, category, created_at, updated_at
        FROM commands
        WHERE category = %s
        ORDER BY description
        """
        return self.db.execute_query(query, (category_key,))
    
    def add_command(self, category: str, command: str, description: str) -> bool:
        """Добавить новую команду."""
        try:
            query = """
            INSERT INTO commands (command, description, category, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """
            self.db.execute_query(query, (command, description, category), fetch_results=False)
            self.logger.info(f"Added command '{command}' to category '{category}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add command: {e}")
            return False
    
    def search_commands(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Поиск команд с ограничением результатов."""
        query = """
        SELECT command, description, category, created_at
        FROM commands
        WHERE LOWER(command) LIKE LOWER(%s) OR LOWER(description) LIKE LOWER(%s)
        ORDER BY 
            CASE WHEN LOWER(command) LIKE LOWER(%s) THEN 1 ELSE 2 END,
            description
        LIMIT %s
        """
        search_pattern = f"%{search_term}%"
        exact_pattern = f"{search_term}%"
        return self.db.execute_query(query, (search_pattern, search_pattern, exact_pattern, limit))