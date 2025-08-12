"""
Unit тесты для SSH клиента
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import socket
import paramiko
from core.ssh_client import SSHClient

class TestSSHClient(unittest.TestCase):
    """Тесты для SSH клиента."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        self.ssh_client = SSHClient()
    
    def tearDown(self):
        """Очистка после каждого теста."""
        if self.ssh_client.connected:
            self.ssh_client.disconnect()
    
    @patch('paramiko.SSHClient')
    def test_successful_connection(self, mock_ssh_class):
        """Тест успешного подключения."""
        # Настройка мока
        mock_ssh = Mock()
        mock_shell = Mock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.invoke_shell.return_value = mock_shell
        mock_shell.recv_ready.return_value = False
        
        # Тест подключения
        result = self.ssh_client.connect("192.168.1.1", "admin", "password")
        
        # Проверки
        self.assertTrue(result)
        self.assertTrue(self.ssh_client.connected)
        mock_ssh.set_missing_host_key_policy.assert_called_once()
        mock_ssh.connect.assert_called_once_with(
            hostname="192.168.1.1",
            port=22,
            username="admin",
            password="password",
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
    
    @patch('paramiko.SSHClient')
    def test_authentication_failure(self, mock_ssh_class):
        """Тест неудачной аутентификации."""
        mock_ssh = Mock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.connect.side_effect = paramiko.AuthenticationException("Auth failed")
        
        result = self.ssh_client.connect("192.168.1.1", "admin", "wrong_password")
        
        self.assertFalse(result)
        self.assertFalse(self.ssh_client.connected)
    
    @patch('paramiko.SSHClient')
    def test_network_error(self, mock_ssh_class):
        """Тест сетевой ошибки."""
        mock_ssh = Mock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.connect.side_effect = socket.error("Network unreachable")
        
        result = self.ssh_client.connect("192.168.1.1", "admin", "password")
        
        self.assertFalse(result)
        self.assertFalse(self.ssh_client.connected)
    
    def test_command_execution_without_connection(self):
        """Тест выполнения команды без подключения."""
        with self.assertRaises(Exception) as context:
            self.ssh_client.execute_command("show version")
        
        self.assertIn("Not connected", str(context.exception))
    
    @patch('paramiko.SSHClient')
    def test_command_execution_with_connection(self, mock_ssh_class):
        """Тест выполнения команды при установленном подключении."""
        # Настройка моков
        mock_ssh = Mock()
        mock_shell = Mock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.invoke_shell.return_value = mock_shell
        
        # Настройка ответа команды
        mock_shell.recv_ready.side_effect = [False, True, False]
        mock_shell.recv.return_value = b"show version\nCisco IOS Software\nRouter#"
        
        # Подключение
        self.ssh_client.connect("192.168.1.1", "admin", "password")
        
        # Выполнение команды
        result = self.ssh_client.execute_command("show version")
        
        # Проверки
        self.assertIsInstance(result, str)
        mock_shell.send.assert_called()
    
    def test_disconnect(self):
        """Тест отключения."""
        # Настройка моков
        self.ssh_client.client = Mock()
        self.ssh_client.shell = Mock()
        self.ssh_client.connected = True
        
        # Отключение
        self.ssh_client.disconnect()
        
        # Проверки
        self.assertFalse(self.ssh_client.connected)
        self.ssh_client.shell.close.assert_called_once()
        self.ssh_client.client.close.assert_called_once()
    
    def test_context_manager(self):
        """Тест использования как context manager."""
        with patch('paramiko.SSHClient') as mock_ssh_class:
            mock_ssh = Mock()
            mock_shell = Mock()
            mock_ssh_class.return_value = mock_ssh
            mock_ssh.invoke_shell.return_value = mock_shell
            mock_shell.recv_ready.return_value = False
            
            with SSHClient() as client:
                result = client.connect("192.168.1.1", "admin", "password")
                self.assertTrue(result)
            
            # Проверяем что disconnect был вызван
            mock_shell.close.assert_called()
            mock_ssh.close.assert_called()
    
    def test_is_connected(self):
        """Тест проверки состояния подключения."""
        # Изначально не подключен
        self.assertFalse(self.ssh_client.is_connected())
        
        # Имитируем подключение
        self.ssh_client.connected = True
        self.ssh_client.client = Mock()
        self.ssh_client.shell = Mock()
        
        self.assertTrue(self.ssh_client.is_connected())
    
    @patch('paramiko.SSHClient')
    def test_get_device_info(self, mock_ssh_class):
        """Тест получения информации об устройстве."""
        # Настройка моков
        mock_ssh = Mock()
        mock_shell = Mock()
        mock_ssh_class.return_value = mock_ssh
        mock_ssh.invoke_shell.return_value = mock_shell
        mock_shell.recv_ready.return_value = False
        
        # Имитируем выполнение команд
        with patch.object(self.ssh_client, 'execute_command') as mock_execute:
            mock_execute.side_effect = [
                "hostname Router1",
                "Cisco IOS Software, Version 15.1(4)M"
            ]
            
            # Подключение
            self.ssh_client.connect("192.168.1.1", "admin", "password")
            
            # Получение информации
            device_info = self.ssh_client.get_device_info()
            
            # Проверки
            self.assertIsNotNone(device_info)
            self.assertEqual(device_info['hostname'], 'Router1')
            self.assertIn('Software', device_info['software'])
    
    def test_clean_output(self):
        """Тест очистки вывода команды."""
        raw_output = "show version\nCisco IOS Software\nVersion 15.1\nRouter#"
        command = "show version"
        
        cleaned = self.ssh_client._clean_output(raw_output, command)
        
        # Проверяем что команда и промпт удалены
        self.assertNotIn("show version", cleaned)
        self.assertNotIn("Router#", cleaned)
        self.assertIn("Cisco IOS Software", cleaned)
    
    def test_is_prompt_ready(self):
        """Тест определения готовности промпта."""
        # Тестируем различные промпты
        test_cases = [
            ("Router#", True),
            ("Switch>", True),
            ("Router(config)#", True),
            ("Router(config-if)#", True),
            ("show version output", False),
            ("", False)
        ]
        
        for output, expected in test_cases:
            with self.subTest(output=output):
                result = self.ssh_client._is_prompt_ready(output)
                self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()