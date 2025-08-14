#!/usr/bin/env python3
"""
Cisco Translator - Enhanced Launcher
Проверяет зависимости и запускает приложение
"""

import sys
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"   Текущая версия: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependency(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
        
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        return False
    return True

def install_dependencies():
    """Install missing dependencies"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ Файл requirements.txt не найден")
        return False
        
    print("📦 Устанавливаем зависимости...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def main():
    """Main launcher function"""
    print("🚀 Cisco Translator - Запуск приложения")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check critical dependencies
    dependencies = [
        ("flet", "flet"),
        ("paramiko", "paramiko"),
        ("cryptography", "cryptography"),
    ]
    
    missing_deps = []
    for pkg_name, import_name in dependencies:
        if check_dependency(pkg_name, import_name):
            print(f"✅ {pkg_name}")
        else:
            print(f"❌ {pkg_name} - не установлен")
            missing_deps.append(pkg_name)
    
    # Install missing dependencies
    if missing_deps:
        print(f"\n📦 Найдены отсутствующие зависимости: {', '.join(missing_deps)}")
        response = input("Установить автоматически? (y/n): ").lower().strip()
        
        if response in ['y', 'yes', 'да', 'д']:
            if not install_dependencies():
                return 1
        else:
            print("❌ Невозможно запустить приложение без зависимостей")
            print("   Выполните: pip install -r requirements.txt")
            return 1
    
    # Launch application
    print("\n🎯 Запуск Cisco Translator...")
    try:
        from main import main as app_main
        app_main()
        print("✅ Приложение завершено")
        return 0
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return 1
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())