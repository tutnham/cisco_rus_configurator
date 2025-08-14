"""
Network Monitoring - мониторинг состояния сетевых устройств
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import socket
import subprocess
import platform

class MonitoringStatus(Enum):
    """Статусы мониторинга."""
    UP = "up"
    DOWN = "down"
    WARNING = "warning"
    UNKNOWN = "unknown"

@dataclass
class MonitoringEvent:
    """Событие мониторинга."""
    device_id: str
    hostname: str
    event_type: str
    status: MonitoringStatus
    message: str
    timestamp: datetime
    details: Dict[str, Any]

@dataclass
class DeviceStatus:
    """Статус устройства."""
    device_id: str
    hostname: str
    ip_address: str
    status: MonitoringStatus
    last_seen: datetime
    response_time: Optional[float]
    consecutive_failures: int
    uptime_percentage: float
    details: Dict[str, Any]

class NetworkMonitor:
    """
    Система мониторинга сетевых устройств.
    
    Обеспечивает постоянный мониторинг доступности устройств,
    отслеживание времени отклика и отправку уведомлений.
    """
    
    def __init__(self, check_interval: int = 60, max_failures: int = 3):
        """
        Инициализация мониторинга.
        
        Args:
            check_interval: Интервал проверки в секундах
            max_failures: Максимальное количество неудачных попыток
        """
        self.check_interval = check_interval
        self.max_failures = max_failures
        self.logger = logging.getLogger(__name__)
        
        self.devices: Dict[str, Dict] = {}
        self.device_status: Dict[str, DeviceStatus] = {}
        self.monitoring_enabled = False
        self.monitoring_thread = None
        
        self.event_handlers: List[Callable[[MonitoringEvent], None]] = []
        self.events_history: List[MonitoringEvent] = []
        
        # Статистика
        self.total_checks = 0
        self.successful_checks = 0
        
    def add_device(self, device_id: str, hostname: str, ip_address: str, 
                   monitoring_type: str = "ping", **kwargs) -> None:
        """
        Добавить устройство для мониторинга.
        
        Args:
            device_id: Уникальный идентификатор устройства
            hostname: Имя устройства
            ip_address: IP адрес
            monitoring_type: Тип мониторинга (ping, ssh, snmp)
            **kwargs: Дополнительные параметры
        """
        device_config = {
            "hostname": hostname,
            "ip_address": ip_address,
            "monitoring_type": monitoring_type,
            "enabled": True,
            "ssh_port": kwargs.get("ssh_port", 22),
            "snmp_community": kwargs.get("snmp_community", "public"),
            "timeout": kwargs.get("timeout", 5),
            "custom_params": kwargs
        }
        
        self.devices[device_id] = device_config
        
        # Инициализируем статус
        self.device_status[device_id] = DeviceStatus(
            device_id=device_id,
            hostname=hostname,
            ip_address=ip_address,
            status=MonitoringStatus.UNKNOWN,
            last_seen=datetime.now(),
            response_time=None,
            consecutive_failures=0,
            uptime_percentage=0.0,
            details={}
        )
        
        self.logger.info(f"Added device {hostname} ({ip_address}) for monitoring")
    
    def remove_device(self, device_id: str) -> bool:
        """
        Удалить устройство из мониторинга.
        
        Args:
            device_id: Идентификатор устройства
            
        Returns:
            True если устройство было удалено
        """
        if device_id in self.devices:
            del self.devices[device_id]
            del self.device_status[device_id]
            self.logger.info(f"Removed device {device_id} from monitoring")
            return True
        return False
    
    def start_monitoring(self) -> None:
        """Запустить мониторинг."""
        if not self.monitoring_enabled:
            self.monitoring_enabled = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Network monitoring started")
    
    def stop_monitoring(self) -> None:
        """Остановить мониторинг."""
        self.monitoring_enabled = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Network monitoring stopped")
    
    def add_event_handler(self, handler: Callable[[MonitoringEvent], None]) -> None:
        """
        Добавить обработчик событий.
        
        Args:
            handler: Функция-обработчик событий
        """
        self.event_handlers.append(handler)
    
    def get_device_status(self, device_id: str) -> Optional[DeviceStatus]:
        """
        Получить статус устройства.
        
        Args:
            device_id: Идентификатор устройства
            
        Returns:
            Статус устройства или None
        """
        return self.device_status.get(device_id)
    
    def get_all_statuses(self) -> Dict[str, DeviceStatus]:
        """Получить статусы всех устройств."""
        return self.device_status.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику мониторинга.
        
        Returns:
            Словарь со статистикой
        """
        total_devices = len(self.devices)
        up_devices = sum(1 for status in self.device_status.values() 
                        if status.status == MonitoringStatus.UP)
        down_devices = sum(1 for status in self.device_status.values() 
                          if status.status == MonitoringStatus.DOWN)
        warning_devices = sum(1 for status in self.device_status.values() 
                             if status.status == MonitoringStatus.WARNING)
        
        success_rate = (self.successful_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        
        return {
            "total_devices": total_devices,
            "up_devices": up_devices,
            "down_devices": down_devices,
            "warning_devices": warning_devices,
            "total_checks": self.total_checks,
            "successful_checks": self.successful_checks,
            "success_rate": round(success_rate, 2),
            "monitoring_enabled": self.monitoring_enabled,
            "check_interval": self.check_interval
        }
    
    def get_events_history(self, limit: int = 100) -> List[MonitoringEvent]:
        """
        Получить историю событий.
        
        Args:
            limit: Максимальное количество событий
            
        Returns:
            Список событий
        """
        return self.events_history[-limit:]
    
    def _monitoring_loop(self) -> None:
        """Основной цикл мониторинга."""
        while self.monitoring_enabled:
            try:
                for device_id, device_config in self.devices.items():
                    if device_config.get("enabled", True):
                        self._check_device(device_id, device_config)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Короткая пауза при ошибке
    
    def _check_device(self, device_id: str, device_config: Dict) -> None:
        """
        Проверить состояние устройства.
        
        Args:
            device_id: Идентификатор устройства
            device_config: Конфигурация устройства
        """
        try:
            current_status = self.device_status[device_id]
            monitoring_type = device_config["monitoring_type"]
            
            self.total_checks += 1
            
            # Выполняем проверку в зависимости от типа
            if monitoring_type == "ping":
                result = self._ping_check(device_config)
            elif monitoring_type == "ssh":
                result = self._ssh_check(device_config)
            elif monitoring_type == "snmp":
                result = self._snmp_check(device_config)
            else:
                result = {"success": False, "error": f"Unknown monitoring type: {monitoring_type}"}
            
            # Обновляем статус
            self._update_device_status(device_id, result)
            
            if result["success"]:
                self.successful_checks += 1
            
        except Exception as e:
            self.logger.error(f"Error checking device {device_id}: {e}")
            self._update_device_status(device_id, {"success": False, "error": str(e)})
    
    def _ping_check(self, device_config: Dict) -> Dict[str, Any]:
        """Проверка доступности через ping."""
        ip_address = device_config["ip_address"]
        timeout = device_config.get("timeout", 5)
        
        try:
            # Определяем команду ping в зависимости от ОС
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip_address]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), ip_address]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, timeout=timeout + 2)
            response_time = (time.time() - start_time) * 1000  # в миллисекундах
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "response_time": response_time,
                    "details": {"ping_output": result.stdout.decode()}
                }
            else:
                return {
                    "success": False,
                    "error": "Ping failed",
                    "details": {"ping_output": result.stderr.decode()}
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Ping timeout"}
        except Exception as e:
            return {"success": False, "error": f"Ping error: {e}"}
    
    def _ssh_check(self, device_config: Dict) -> Dict[str, Any]:
        """Проверка доступности через SSH."""
        ip_address = device_config["ip_address"]
        port = device_config.get("ssh_port", 22)
        timeout = device_config.get("timeout", 5)
        
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_address, port))
            response_time = (time.time() - start_time) * 1000
            sock.close()
            
            if result == 0:
                return {
                    "success": True,
                    "response_time": response_time,
                    "details": {"port": port, "connection": "successful"}
                }
            else:
                return {
                    "success": False,
                    "error": f"SSH port {port} not accessible",
                    "details": {"port": port, "error_code": result}
                }
                
        except Exception as e:
            return {"success": False, "error": f"SSH check error: {e}"}
    
    def _snmp_check(self, device_config: Dict) -> Dict[str, Any]:
        """Проверка доступности через SNMP."""
        # Базовая реализация - можно расширить с помощью pysnmp
        ip_address = device_config["ip_address"]
        community = device_config.get("snmp_community", "public")
        
        try:
            # Для простоты используем проверку UDP порта 161
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(device_config.get("timeout", 5))
            start_time = time.time()
            
            # Отправляем простой SNMP запрос (упрощенно)
            result = sock.connect_ex((ip_address, 161))
            response_time = (time.time() - start_time) * 1000
            sock.close()
            
            return {
                "success": result == 0,
                "response_time": response_time if result == 0 else None,
                "error": "SNMP port not accessible" if result != 0 else None,
                "details": {"community": community, "port": 161}
            }
            
        except Exception as e:
            return {"success": False, "error": f"SNMP check error: {e}"}
    
    def _update_device_status(self, device_id: str, check_result: Dict) -> None:
        """
        Обновить статус устройства.
        
        Args:
            device_id: Идентификатор устройства
            check_result: Результат проверки
        """
        current_status = self.device_status[device_id]
        previous_status = current_status.status
        
        if check_result["success"]:
            new_status = MonitoringStatus.UP
            current_status.consecutive_failures = 0
            current_status.last_seen = datetime.now()
            current_status.response_time = check_result.get("response_time")
        else:
            current_status.consecutive_failures += 1
            
            if current_status.consecutive_failures >= self.max_failures:
                new_status = MonitoringStatus.DOWN
            else:
                new_status = MonitoringStatus.WARNING
        
        # Обновляем статус
        current_status.status = new_status
        current_status.details = check_result.get("details", {})
        
        # Создаем событие если статус изменился
        if previous_status != new_status:
            event = MonitoringEvent(
                device_id=device_id,
                hostname=current_status.hostname,
                event_type="status_change",
                status=new_status,
                message=f"Device status changed from {previous_status.value} to {new_status.value}",
                timestamp=datetime.now(),
                details={
                    "previous_status": previous_status.value,
                    "new_status": new_status.value,
                    "consecutive_failures": current_status.consecutive_failures,
                    "check_result": check_result
                }
            )
            
            self._handle_event(event)
    
    def _handle_event(self, event: MonitoringEvent) -> None:
        """
        Обработать событие мониторинга.
        
        Args:
            event: Событие мониторинга
        """
        # Добавляем в историю
        self.events_history.append(event)
        
        # Ограничиваем размер истории
        if len(self.events_history) > 1000:
            self.events_history = self.events_history[-500:]
        
        # Логируем событие
        level = logging.INFO
        if event.status == MonitoringStatus.DOWN:
            level = logging.ERROR
        elif event.status == MonitoringStatus.WARNING:
            level = logging.WARNING
        
        self.logger.log(level, f"Monitoring event: {event.hostname} - {event.message}")
        
        # Вызываем обработчики событий
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler: {e}")

# Примеры обработчиков событий
def email_notification_handler(event: MonitoringEvent) -> None:
    """Обработчик для отправки email уведомлений."""
    if event.status in [MonitoringStatus.DOWN, MonitoringStatus.WARNING]:
        # Здесь можно добавить отправку email
        print(f"EMAIL ALERT: {event.hostname} is {event.status.value}")

def log_file_handler(event: MonitoringEvent) -> None:
    """Обработчик для записи в файл лога."""
    log_message = f"{event.timestamp.isoformat()} - {event.hostname} - {event.message}\n"
    
    try:
        with open("monitoring_events.log", "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception as e:
        logging.error(f"Failed to write to monitoring log: {e}")

def webhook_notification_handler(event: MonitoringEvent) -> None:
    """Обработчик для отправки webhook уведомлений."""
    if event.status == MonitoringStatus.DOWN:
        # Здесь можно добавить отправку webhook
        print(f"WEBHOOK: Device {event.hostname} is down!")