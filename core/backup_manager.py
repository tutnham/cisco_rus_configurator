"""
Backup Manager - автоматическое создание резервных копий конфигураций
"""

import os
import json
import gzip
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

class ConfigBackupManager:
    """
    Менеджер резервных копий конфигураций устройств.
    
    Обеспечивает автоматическое создание, сжатие, версионирование
    и очистку резервных копий конфигураций Cisco устройств.
    """
    
    def __init__(self, backup_dir: str = "backups", max_backups_per_device: int = 10):
        """
        Инициализация менеджера резервных копий.
        
        Args:
            backup_dir: Директория для хранения резервных копий
            max_backups_per_device: Максимальное количество резервных копий на устройство
        """
        self.backup_dir = Path(backup_dir)
        self.max_backups_per_device = max_backups_per_device
        self.logger = logging.getLogger(__name__)
        
        # Создаем директорию если не существует
        self.backup_dir.mkdir(exist_ok=True)
        
        # Создаем поддиректории
        (self.backup_dir / "configs").mkdir(exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)
        (self.backup_dir / "compressed").mkdir(exist_ok=True)
    
    def create_backup(self, hostname: str, config_data: str, 
                     device_info: Optional[Dict] = None, 
                     backup_type: str = "manual") -> str:
        """
        Создать резервную копию конфигурации.
        
        Args:
            hostname: Имя устройства
            config_data: Данные конфигурации
            device_info: Дополнительная информация об устройстве
            backup_type: Тип резервного копирования (manual, scheduled, auto)
            
        Returns:
            Путь к созданной резервной копии
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_hostname = self._sanitize_filename(hostname)
            
            # Создаем директорию для устройства
            device_dir = self.backup_dir / "configs" / safe_hostname
            device_dir.mkdir(exist_ok=True)
            
            # Имя файла резервной копии
            backup_filename = f"{safe_hostname}_{timestamp}.cfg"
            backup_path = device_dir / backup_filename
            
            # Сохраняем конфигурацию
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(config_data)
            
            # Создаем метаданные
            metadata = {
                "hostname": hostname,
                "timestamp": timestamp,
                "backup_type": backup_type,
                "file_size": len(config_data),
                "file_hash": self._calculate_hash(config_data),
                "device_info": device_info or {},
                "backup_path": str(backup_path)
            }
            
            # Сохраняем метаданные
            metadata_path = self.backup_dir / "metadata" / f"{backup_filename}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Создаем сжатую версию для экономии места
            compressed_path = self._compress_backup(backup_path)
            
            # Обновляем метаданные с информацией о сжатии
            if compressed_path:
                metadata["compressed_path"] = str(compressed_path)
                metadata["compressed_size"] = os.path.getsize(compressed_path)
                
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Очищаем старые резервные копии
            self._cleanup_old_backups(safe_hostname)
            
            self.logger.info(f"Created backup for {hostname}: {backup_filename}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {hostname}: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> str:
        """
        Восстановить конфигурацию из резервной копии.
        
        Args:
            backup_path: Путь к резервной копии
            
        Returns:
            Содержимое конфигурации
        """
        try:
            backup_file = Path(backup_path)
            
            if backup_file.suffix == '.gz':
                # Распаковываем сжатую резервную копию
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    config_data = f.read()
            else:
                # Читаем обычную резервную копию
                with open(backup_file, 'r', encoding='utf-8') as f:
                    config_data = f.read()
            
            self.logger.info(f"Restored backup from {backup_path}")
            return config_data
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup from {backup_path}: {e}")
            raise
    
    def list_backups(self, hostname: Optional[str] = None) -> List[Dict]:
        """
        Получить список всех резервных копий.
        
        Args:
            hostname: Имя устройства (если None, возвращает все устройства)
            
        Returns:
            Список метаданных резервных копий
        """
        backups = []
        metadata_dir = self.backup_dir / "metadata"
        
        try:
            for metadata_file in metadata_dir.glob("*.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                if hostname is None or metadata.get("hostname") == hostname:
                    backups.append(metadata)
            
            # Сортируем по времени создания (новые первыми)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def compare_configs(self, config1: str, config2: str) -> Dict:
        """
        Сравнить две конфигурации.
        
        Args:
            config1: Первая конфигурация
            config2: Вторая конфигурация
            
        Returns:
            Результат сравнения
        """
        try:
            lines1 = config1.splitlines()
            lines2 = config2.splitlines()
            
            # Простое сравнение строк
            added_lines = []
            removed_lines = []
            common_lines = []
            
            set1 = set(lines1)
            set2 = set(lines2)
            
            added_lines = list(set2 - set1)
            removed_lines = list(set1 - set2)
            common_lines = list(set1 & set2)
            
            hash1 = self._calculate_hash(config1)
            hash2 = self._calculate_hash(config2)
            
            return {
                "identical": hash1 == hash2,
                "hash1": hash1,
                "hash2": hash2,
                "added_lines": added_lines,
                "removed_lines": removed_lines,
                "common_lines_count": len(common_lines),
                "total_changes": len(added_lines) + len(removed_lines)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to compare configs: {e}")
            return {"error": str(e)}
    
    def get_backup_statistics(self) -> Dict:
        """
        Получить статистику резервных копий.
        
        Returns:
            Статистика резервных копий
        """
        try:
            stats = {
                "total_backups": 0,
                "total_devices": 0,
                "total_size_mb": 0,
                "compressed_size_mb": 0,
                "devices": {},
                "backup_types": {},
                "oldest_backup": None,
                "newest_backup": None
            }
            
            backups = self.list_backups()
            stats["total_backups"] = len(backups)
            
            devices = set()
            backup_types = {}
            timestamps = []
            
            for backup in backups:
                hostname = backup.get("hostname", "unknown")
                devices.add(hostname)
                
                # Статистика по устройствам
                if hostname not in stats["devices"]:
                    stats["devices"][hostname] = {"count": 0, "size_mb": 0}
                stats["devices"][hostname]["count"] += 1
                stats["devices"][hostname]["size_mb"] += backup.get("file_size", 0) / (1024 * 1024)
                
                # Статистика по типам резервных копий
                backup_type = backup.get("backup_type", "unknown")
                backup_types[backup_type] = backup_types.get(backup_type, 0) + 1
                
                # Размеры
                stats["total_size_mb"] += backup.get("file_size", 0) / (1024 * 1024)
                stats["compressed_size_mb"] += backup.get("compressed_size", 0) / (1024 * 1024)
                
                # Временные метки
                timestamps.append(backup["timestamp"])
            
            stats["total_devices"] = len(devices)
            stats["backup_types"] = backup_types
            
            if timestamps:
                stats["oldest_backup"] = min(timestamps)
                stats["newest_backup"] = max(timestamps)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get backup statistics: {e}")
            return {"error": str(e)}
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """
        Очистить старые резервные копии.
        
        Args:
            days_to_keep: Количество дней для хранения резервных копий
            
        Returns:
            Количество удаленных резервных копий
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_timestamp = cutoff_date.strftime("%Y%m%d_%H%M%S")
            
            removed_count = 0
            backups = self.list_backups()
            
            for backup in backups:
                if backup["timestamp"] < cutoff_timestamp:
                    # Удаляем файлы
                    backup_path = Path(backup["backup_path"])
                    if backup_path.exists():
                        backup_path.unlink()
                        removed_count += 1
                    
                    # Удаляем сжатую версию
                    if "compressed_path" in backup:
                        compressed_path = Path(backup["compressed_path"])
                        if compressed_path.exists():
                            compressed_path.unlink()
                    
                    # Удаляем метаданные
                    metadata_path = self.backup_dir / "metadata" / f"{backup_path.name}.json"
                    if metadata_path.exists():
                        metadata_path.unlink()
            
            self.logger.info(f"Cleaned up {removed_count} old backups")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    def _sanitize_filename(self, filename: str) -> str:
        """Очистить имя файла от недопустимых символов."""
        import re
        # Заменяем недопустимые символы на подчеркивание
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    def _calculate_hash(self, data: str) -> str:
        """Вычислить MD5 хеш данных."""
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def _compress_backup(self, backup_path: Path) -> Optional[Path]:
        """Создать сжатую версию резервной копии."""
        try:
            compressed_path = self.backup_dir / "compressed" / f"{backup_path.name}.gz"
            
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return compressed_path
            
        except Exception as e:
            self.logger.error(f"Failed to compress backup {backup_path}: {e}")
            return None
    
    def _cleanup_old_backups(self, hostname: str) -> None:
        """Очистить старые резервные копии для конкретного устройства."""
        try:
            backups = self.list_backups(hostname)
            
            if len(backups) > self.max_backups_per_device:
                # Сортируем по времени (старые первыми)
                backups.sort(key=lambda x: x["timestamp"])
                
                # Удаляем самые старые
                to_remove = backups[:-self.max_backups_per_device]
                
                for backup in to_remove:
                    backup_path = Path(backup["backup_path"])
                    if backup_path.exists():
                        backup_path.unlink()
                    
                    # Удаляем сжатую версию
                    if "compressed_path" in backup:
                        compressed_path = Path(backup["compressed_path"])
                        if compressed_path.exists():
                            compressed_path.unlink()
                    
                    # Удаляем метаданные
                    metadata_path = self.backup_dir / "metadata" / f"{backup_path.name}.json"
                    if metadata_path.exists():
                        metadata_path.unlink()
                
                self.logger.info(f"Removed {len(to_remove)} old backups for {hostname}")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups for {hostname}: {e}")

class ScheduledBackupManager:
    """
    Планировщик автоматических резервных копий.
    """
    
    def __init__(self, backup_manager: ConfigBackupManager):
        self.backup_manager = backup_manager
        self.logger = logging.getLogger(__name__)
        self.scheduled_devices = {}
    
    def add_scheduled_device(self, hostname: str, ssh_client, 
                           interval_hours: int = 24) -> None:
        """
        Добавить устройство в расписание автоматических резервных копий.
        
        Args:
            hostname: Имя устройства
            ssh_client: SSH клиент для подключения
            interval_hours: Интервал резервного копирования в часах
        """
        self.scheduled_devices[hostname] = {
            "ssh_client": ssh_client,
            "interval_hours": interval_hours,
            "last_backup": None
        }
        
        self.logger.info(f"Added {hostname} to scheduled backups (every {interval_hours}h)")
    
    def run_scheduled_backups(self) -> Dict[str, bool]:
        """
        Выполнить запланированные резервные копии.
        
        Returns:
            Результаты выполнения резервного копирования
        """
        results = {}
        current_time = datetime.now()
        
        for hostname, config in self.scheduled_devices.items():
            try:
                # Проверяем нужно ли создавать резервную копию
                if self._should_backup(hostname, config, current_time):
                    ssh_client = config["ssh_client"]
                    
                    # Получаем конфигурацию
                    running_config = ssh_client.execute_command("show running-config")
                    
                    # Создаем резервную копию
                    backup_path = self.backup_manager.create_backup(
                        hostname=hostname,
                        config_data=running_config,
                        backup_type="scheduled"
                    )
                    
                    # Обновляем время последней резервной копии
                    config["last_backup"] = current_time
                    
                    results[hostname] = True
                    self.logger.info(f"Scheduled backup completed for {hostname}")
                else:
                    results[hostname] = False  # Не требуется
                    
            except Exception as e:
                results[hostname] = False
                self.logger.error(f"Scheduled backup failed for {hostname}: {e}")
        
        return results
    
    def _should_backup(self, hostname: str, config: Dict, current_time: datetime) -> bool:
        """Проверить нужно ли создавать резервную копию."""
        if config["last_backup"] is None:
            return True
        
        time_diff = current_time - config["last_backup"]
        return time_diff.total_seconds() >= config["interval_hours"] * 3600