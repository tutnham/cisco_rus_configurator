#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к базе данных PostgreSQL
"""

import sys
import os
import json
import time
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_connection():
    """Тест базового подключения к PostgreSQL."""
    print("🔍 Тестирование базового подключения к PostgreSQL...")
    
    try:
        from core.database import DatabaseManager
        from core.config_manager import ConfigManager
        
        # Загружаем конфигурацию
        config_manager = ConfigManager()
        db_config = config_manager.get_database_config()
        
        print(f"📋 Конфигурация:")
        print(f"   Host: {db_config.get('host', 'localhost')}")
        print(f"   Port: {db_config.get('port', 5432)}")
        print(f"   Database: {db_config.get('database', 'cisco_translator')}")
        print(f"   User: {db_config.get('user', 'cisco_user')}")
        
        # Создаем подключение
        db_manager = DatabaseManager(db_config)
        
        # Тестируем простой запрос
        result = db_manager.execute_query("SELECT current_database(), current_user, version()")
        
        if result:
            print("✅ Подключение успешно!")
            print(f"   Текущая БД: {result[0]['current_database']}")
            print(f"   Пользователь: {result[0]['current_user']}")
            print(f"   Версия PostgreSQL: {result[0]['version'][:50]}...")
            return True
        else:
            print("❌ Не удалось получить данные из БД")
            return False
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_enhanced_connection():
    """Тест улучшенного подключения с пулом соединений."""
    print("\n🚀 Тестирование улучшенного подключения с пулом соединений...")
    
    try:
        from core.database_enhanced import create_database_manager, DatabaseConfig
        
        # Создаем менеджер из конфига
        db_manager = create_database_manager("config/database.json")
        
        # Проверяем статистику
        stats = db_manager.get_statistics()
        print(f"📊 Статистика пула:")
        print(f"   Подключено: {stats['is_connected']}")
        print(f"   Мин. соединений: {stats['config']['min_connections']}")
        print(f"   Макс. соединений: {stats['config']['max_connections']}")
        
        # Проверяем подключение
        if db_manager.check_connection():
            print("✅ Пул соединений работает!")
            
            # Получаем информацию о БД
            db_info = db_manager.get_database_info()
            print(f"📄 Информация о БД:")
            for key, value in db_info.items():
                if 'error' not in str(value).lower():
                    print(f"   {key}: {value}")
            
            return True
        else:
            print("❌ Пул соединений не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка с пулом соединений: {e}")
        return False

def test_tables():
    """Тест наличия и структуры таблиц."""
    print("\n📋 Проверка структуры базы данных...")
    
    try:
        from core.database_enhanced import create_database_manager
        
        with create_database_manager("config/database.json") as db_manager:
            # Список ожидаемых таблиц
            expected_tables = [
                'commands', 'macros', 'macro_commands', 
                'connection_history', 'command_history', 'app_settings'
            ]
            
            # Проверяем наличие таблиц
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
            
            result = db_manager.execute_query(query)
            existing_tables = [row['table_name'] for row in result]
            
            print(f"🗃️ Найденные таблицы ({len(existing_tables)}):")
            for table in existing_tables:
                status = "✅" if table in expected_tables else "⚠️"
                print(f"   {status} {table}")
            
            # Проверяем отсутствующие таблицы
            missing_tables = set(expected_tables) - set(existing_tables)
            if missing_tables:
                print(f"❌ Отсутствующие таблицы: {', '.join(missing_tables)}")
                return False
            
            # Проверяем содержимое таблиц
            print(f"\n📊 Содержимое таблиц:")
            for table in expected_tables:
                try:
                    count_result = db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                    count = count_result[0]['count'] if count_result else 0
                    print(f"   {table}: {count} записей")
                except Exception as e:
                    print(f"   {table}: ошибка - {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        return False

def test_performance():
    """Тест производительности подключения."""
    print("\n⚡ Тестирование производительности...")
    
    try:
        from core.database_enhanced import create_database_manager
        
        with create_database_manager("config/database.json") as db_manager:
            # Тест множественных запросов
            num_queries = 10
            start_time = time.time()
            
            for i in range(num_queries):
                db_manager.execute_query("SELECT $1 as test_value", (i,))
            
            total_time = time.time() - start_time
            avg_time = total_time / num_queries
            
            print(f"📈 Результаты производительности:")
            print(f"   Количество запросов: {num_queries}")
            print(f"   Общее время: {total_time:.3f}с")
            print(f"   Среднее время на запрос: {avg_time:.3f}с")
            print(f"   Запросов в секунду: {num_queries/total_time:.1f}")
            
            # Проверяем статистику
            stats = db_manager.get_statistics()
            print(f"   Успешных запросов: {stats['successful_queries']}")
            print(f"   Неудачных запросов: {stats['failed_queries']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования производительности: {e}")
        return False

def test_managers():
    """Тест работы менеджеров базы данных."""
    print("\n🔧 Тестирование менеджеров...")
    
    try:
        from core.database import PostgreSQLCommandManager, DatabaseManager
        from core.config_manager import ConfigManager
        
        # Создаем менеджеры
        config_manager = ConfigManager()
        db_config = config_manager.get_database_config()
        db_manager = DatabaseManager(db_config)
        command_manager = PostgreSQLCommandManager(db_manager)
        
        # Тестируем получение категорий
        categories = command_manager.get_categories()
        print(f"📂 Категории команд ({len(categories)}):")
        for category in categories[:5]:  # Показываем первые 5
            print(f"   • {category}")
        
        # Тестируем поиск команд
        if categories:
            first_category = categories[0]
            commands = command_manager.get_commands_by_category(first_category)
            print(f"\n🔍 Команды в категории '{first_category}' ({len(commands)}):")
            for cmd in commands[:3]:  # Показываем первые 3
                print(f"   • {cmd['command']} - {cmd['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования менеджеров: {e}")
        return False

def create_test_report():
    """Создать отчет о тестировании."""
    print("\n" + "="*60)
    print("📋 ОТЧЕТ О ТЕСТИРОВАНИИ БАЗЫ ДАННЫХ")
    print("="*60)
    
    tests = [
        ("Базовое подключение", test_basic_connection),
        ("Пул соединений", test_enhanced_connection), 
        ("Структура БД", test_tables),
        ("Производительность", test_performance),
        ("Менеджеры", test_managers)
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            result = test_func()
            results[test_name] = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            if result:
                passed_tests += 1
        except Exception as e:
            results[test_name] = f"❌ ОШИБКА: {e}"
    
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("="*60)
    
    for test_name, result in results.items():
        print(f"{test_name:.<30} {result}")
    
    print(f"\n🎯 Общий результат: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! База данных работает отлично!")
        return True
    elif passed_tests >= total_tests * 0.8:
        print("⚠️  Большинство тестов пройдено, но есть проблемы.")
        return False
    else:
        print("❌ Серьезные проблемы с базой данных!")
        return False

def print_connection_instructions():
    """Вывести инструкции по настройке подключения."""
    print("\n" + "="*60)
    print("📖 ИНСТРУКЦИИ ПО НАСТРОЙКЕ БАЗЫ ДАННЫХ")
    print("="*60)
    
    print("""
1. 🐘 Установка PostgreSQL:
   sudo apt-get install postgresql postgresql-contrib

2. 🔧 Создание базы данных и пользователя:
   sudo -u postgres psql
   CREATE DATABASE cisco_translator;
   CREATE USER cisco_user WITH PASSWORD 'cisco_password_2025';
   GRANT ALL PRIVILEGES ON DATABASE cisco_translator TO cisco_user;
   \\q

3. 📊 Выполнение миграций:
   psql -U cisco_user -d cisco_translator -f supabase/migrations/20250709083505_throbbing_brook.sql

4. ⚙️ Настройка конфигурации:
   Отредактируйте файл config/database.json

5. 🔍 Проверка подключения:
   python3 test_database_connection.py

6. 🌐 Альтернативно - использование Docker:
   docker run --name postgres-cisco \\
     -e POSTGRES_DB=cisco_translator \\
     -e POSTGRES_USER=cisco_user \\
     -e POSTGRES_PASSWORD=cisco_password_2025 \\
     -p 5432:5432 -d postgres:13
""")

def main():
    """Главная функция."""
    print("🔍 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ CISCO TRANSLATOR")
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Проверяем наличие конфигурационного файла
        config_path = "config/database.json"
        if not os.path.exists(config_path):
            print(f"❌ Конфигурационный файл не найден: {config_path}")
            print_connection_instructions()
            return False
        
        # Проверяем наличие psycopg2
        try:
            import psycopg2
            print(f"✅ psycopg2 версия: {psycopg2.__version__}")
        except ImportError:
            print("❌ psycopg2 не установлен! Установите: pip install psycopg2-binary")
            return False
        
        # Запускаем тесты
        success = create_test_report()
        
        if not success:
            print_connection_instructions()
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
        return False
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)