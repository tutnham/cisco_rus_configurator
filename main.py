#!/usr/bin/env python3
"""
Cisco Translator - Flet Desktop Application
Modern desktop application for Cisco CLI commands with Russian translation interface
"""

import flet as ft
import asyncio
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any

from core.command_manager import CommandManager
from core.macro_manager import MacroManager
from core.ssh_client import SSHClient
from core.security import SecureStorage
from core.logger import setup_logging

class CiscoTranslatorApp:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers
        self.command_manager = CommandManager()
        self.macro_manager = MacroManager()
        self.secure_storage = SecureStorage()
        self.ssh_client = None
        
        # Application state
        self.connected = False
        self.current_connection = None
        self.command_history = []
        self.is_executing = False
        
        # UI components
        self.page = None
        self.status_text = None
        self.connect_btn = None
        self.disconnect_btn = None
        self.category_dropdown = None
        self.commands_list = None
        self.macros_list = None
        self.output_text = None
        self.command_input = None
        self.host_input = None
        self.username_input = None
        self.password_input = None
        self.port_input = None
        
    def main(self, page: ft.Page):
        """Main application entry point"""
        self.page = page
        self.page.title = "Cisco Translator"
        self.page.window.width = 1200
        self.page.window.height = 800
        self.page.window.min_width = 800
        self.page.window.min_height = 600
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 10
        
        # Add keyboard shortcuts
        self.page.on_keyboard_event = self.on_keyboard_event
        
        # Load data
        self.load_commands()
        self.load_macros()
        
        # Build UI
        self.build_ui()
        
        self.logger.info("Flet GUI initialized successfully")
        
    def build_ui(self):
        """Build the user interface"""
        # Header with connection status
        header = self.build_header()
        
        # Main content area
        content = self.build_content()
        
        # Add to page
        self.page.add(
            ft.Column([
                header,
                ft.Divider(),
                content
            ], expand=True)
        )
        
    def build_header(self):
        """Build header with connection controls"""
        self.status_text = ft.Text(
            "Не подключено",
            color=ft.Colors.RED,
            weight=ft.FontWeight.BOLD
        )
        
        self.connect_btn = ft.ElevatedButton(
            "Подключиться",
            icon=ft.Icons.WIFI,
            on_click=self.show_connection_dialog
        )
        
        self.disconnect_btn = ft.ElevatedButton(
            "Отключиться",
            icon=ft.Icons.LINK_OFF,
            on_click=self.disconnect,
            disabled=True
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ROUTER, color=ft.Colors.BLUE),
                ft.Text("Cisco Translator", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.status_text,
                self.connect_btn,
                self.disconnect_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=10,
            bgcolor=ft.Colors.SURFACE_VARIANT,
            border_radius=10
        )
        
    def build_content(self):
        """Build main content area"""
        # Left panel - Commands and Macros
        left_panel = self.build_left_panel()
        
        # Right panel - Terminal and Output
        right_panel = self.build_right_panel()
        
        return ft.Row([
            ft.Container(
                content=left_panel,
                width=400,
                expand=False
            ),
            ft.VerticalDivider(),
            ft.Container(
                content=right_panel,
                expand=True
            )
        ], expand=True)
        
    def build_left_panel(self):
        """Build left panel with commands and macros"""
        # Category selection
        self.category_dropdown = ft.Dropdown(
            label="Категория команд",
            options=[],
            on_change=self.on_category_change,
            width=350
        )
        
        # Commands list
        self.commands_list = ft.ListView(
            height=250,
            spacing=5
        )
        
        # Macros list
        self.macros_list = ft.ListView(
            height=200,
            spacing=5
        )
        
        # Populate dropdowns
        self.populate_categories()
        self.populate_macros()
        
        return ft.Column([
            ft.Text("Команды", size=18, weight=ft.FontWeight.BOLD),
            self.category_dropdown,
            ft.Container(
                content=self.commands_list,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=5
            ),
            ft.Divider(),
            ft.Text("Макросы", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=self.macros_list,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=5
            )
        ], spacing=10)
        
    def build_right_panel(self):
        """Build right panel with terminal"""
        # Command input
        self.command_input = ft.TextField(
            label="Введите команду",
            multiline=False,
            on_submit=self.execute_command,
            disabled=True,
            expand=True
        )
        
        self.execute_btn = ft.ElevatedButton(
            "Выполнить",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.execute_command,
            disabled=True
        )
        
        clear_btn = ft.ElevatedButton(
            "Очистить",
            icon=ft.icons.CLEAR,
            on_click=self.clear_output
        )
        
        # Output area
        self.output_text = ft.TextField(
            label="Вывод команд",
            multiline=True,
            read_only=True,
            min_lines=20,
            max_lines=20,
            expand=True
        )
        
        # Shortcuts info
        shortcuts_info = ft.Container(
            content=ft.Text(
                "Горячие клавиши: F5 - Подключение, F9 - Выполнить, F12/Ctrl+L - Очистить",
                size=10,
                color=ft.Colors.GREY_600
            ),
            padding=ft.padding.only(bottom=5)
        )
        
        return ft.Column([
            ft.Text("Терминал", size=18, weight=ft.FontWeight.BOLD),
            shortcuts_info,
            ft.Row([
                self.command_input,
                self.execute_btn,
                clear_btn
            ]),
            ft.Container(
                content=self.output_text,
                expand=True
            )
        ], expand=True, spacing=10)
        
    def populate_categories(self):
        """Populate command categories"""
        try:
            categories = self.command_manager.get_categories()
            self.category_dropdown.options = [
                ft.dropdown.Option(cat) for cat in categories
            ]
            self.page.update()
        except Exception as e:
            self.logger.error(f"Error loading categories: {e}")
            
    def populate_macros(self):
        """Populate macros list"""
        try:
            macros = self.macro_manager.get_all_macros()
            self.macros_list.controls.clear()
            
            for macro_name, macro_data in macros.items():
                macro_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(macro_name, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                macro_data.get('description', 'Нет описания'),
                                size=12,
                                color=ft.Colors.GREY_700
                            ),
                            ft.ElevatedButton(
                                "Выполнить",
                                icon=ft.icons.PLAY_ARROW,
                                on_click=lambda e, name=macro_name: self.execute_macro(name),
                                disabled=True,
                                data=macro_name
                            )
                        ], spacing=5),
                        padding=10
                    )
                )
                self.macros_list.controls.append(macro_card)
                
            self.page.update()
        except Exception as e:
            self.logger.error(f"Error loading macros: {e}")
            
    def on_category_change(self, e):
        """Handle category selection change"""
        if not self.category_dropdown.value:
            return
            
        try:
            commands = self.command_manager.get_commands_by_category(
                self.category_dropdown.value
            )
            
            self.commands_list.controls.clear()
            
            for cmd_data in commands:
                command = cmd_data.get('command', '')
                description = cmd_data.get('description', command)
                
                cmd_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(description, weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(command, size=10, color=ft.Colors.GREY_700),
                            ft.ElevatedButton(
                                "Использовать",
                                icon=ft.icons.CONTENT_COPY,
                                on_click=lambda e, cmd=command: self.use_command(cmd),
                                size=ft.ControlSize.SMALL
                            )
                        ], spacing=3),
                        padding=8
                    )
                )
                self.commands_list.controls.append(cmd_card)
                
            self.page.update()
        except Exception as e:
            self.logger.error(f"Error loading commands: {e}")
            
    def use_command(self, command):
        """Use selected command"""
        self.command_input.value = command
        self.page.update()
        
    def show_connection_dialog(self, e=None):
        """Show connection dialog"""
        self.host_input = ft.TextField(label="IP адрес/Hostname", width=300)
        self.username_input = ft.TextField(label="Имя пользователя", width=300)
        self.password_input = ft.TextField(label="Пароль", password=True, width=300)
        self.port_input = ft.TextField(label="Порт", value="22", width=300)
        
        connection_type = ft.Dropdown(
            label="Тип подключения",
            options=[
                ft.dropdown.Option("ssh", "SSH"),
                ft.dropdown.Option("telnet", "Telnet")
            ],
            value="ssh",
            width=300
        )
        
        def connect_action(e):
            self.connect_to_device(
                self.host_input.value,
                self.username_input.value,
                self.password_input.value,
                int(self.port_input.value or 22),
                connection_type.value
            )
            dialog.open = False
            self.page.update()
            
        dialog = ft.AlertDialog(
            title=ft.Text("Подключение к устройству"),
            content=ft.Column([
                self.host_input,
                self.username_input,
                self.password_input,
                self.port_input,
                connection_type
            ], height=300, spacing=10),
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Подключиться", on_click=connect_action)
            ]
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
        
    def close_dialog(self, dialog):
        """Close dialog"""
        dialog.open = False
        self.page.update()
        
    def connect_to_device(self, host, username, password, port, conn_type):
        """Connect to network device"""
        try:
            self.ssh_client = SSHClient()
            
            def connect_thread():
                success = self.ssh_client.connect(host, username, password, port)
                
                def update_ui():
                    if success:
                        self.connected = True
                        self.current_connection = {
                            'host': host,
                            'username': username,
                            'type': conn_type,
                            'port': port
                        }
                        
                        self.status_text.value = f"Подключено к {host}"
                        self.status_text.color = ft.Colors.GREEN
                        self.connect_btn.disabled = True
                        self.disconnect_btn.disabled = False
                        self.command_input.disabled = False
                        self.execute_btn.disabled = False
                        
                        # Enable execute buttons
                        for control in self.macros_list.controls:
                            if hasattr(control, 'content'):
                                for child in control.content.content.controls:
                                    if isinstance(child, ft.ElevatedButton):
                                        child.disabled = False
                        
                        self.add_output(f"✓ Успешно подключено к {host}:{port}")
                    else:
                        self.add_output(f"✗ Ошибка подключения к {host}:{port}")
                        
                    self.page.update()
                
                # Schedule UI update on main thread
                self.page.run_thread(update_ui)
            
            threading.Thread(target=connect_thread, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.add_output(f"✗ Ошибка подключения: {str(e)}")
            
    def disconnect(self, e=None):
        """Disconnect from device"""
        try:
            if self.ssh_client:
                self.ssh_client.disconnect()
                
            self.connected = False
            self.current_connection = None
            self.ssh_client = None
            
            self.status_text.value = "Не подключено"
            self.status_text.color = ft.Colors.RED
            self.connect_btn.disabled = False
            self.disconnect_btn.disabled = True
            self.command_input.disabled = True
            self.execute_btn.disabled = True
            
            # Disable execute buttons
            for control in self.macros_list.controls:
                if hasattr(control, 'content'):
                    for child in control.content.content.controls:
                        if isinstance(child, ft.ElevatedButton):
                            child.disabled = True
            
            self.add_output("✓ Отключено от устройства")
            self.page.update()
            
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
            
    def execute_command(self, e=None):
        """Execute command on device"""
        if not self.connected or not self.ssh_client:
            self.add_output("✗ Нет подключения к устройству")
            return
            
        command = self.command_input.value.strip()
        if not command:
            return
            
        if self.is_executing:
            return
            
        try:
            # Show loading state
            self.is_executing = True
            self.execute_btn.disabled = True
            self.execute_btn.text = "Выполняется..."
            self.page.update()
            
            def execute_thread():
                try:
                    result = self.ssh_client.execute_command(command)
                    
                    def update_ui():
                        self.add_output(f"$ {command}")
                        self.add_output(result)
                        self.add_output("-" * 50)
                        self.command_history.append({
                            'command': command,
                            'result': result,
                            'timestamp': datetime.now().strftime('%H:%M:%S')
                        })
                        self.command_input.value = ""
                        
                        # Reset loading state
                        self.is_executing = False
                        self.execute_btn.disabled = False
                        self.execute_btn.text = "Выполнить"
                        self.page.update()
                    
                    self.page.run_thread(update_ui)
                    
                except Exception as e:
                    def update_error():
                        self.add_output(f"✗ Ошибка выполнения команды: {str(e)}")
                        
                        # Reset loading state
                        self.is_executing = False
                        self.execute_btn.disabled = False
                        self.execute_btn.text = "Выполнить"
                        self.page.update()
                    
                    self.page.run_thread(update_error)
            
            threading.Thread(target=execute_thread, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            self.add_output(f"✗ Ошибка: {str(e)}")
            
            # Reset loading state
            self.is_executing = False
            self.execute_btn.disabled = False
            self.execute_btn.text = "Выполнить"
            self.page.update()
            
    def execute_macro(self, macro_name):
        """Execute macro"""
        if not self.connected or not self.ssh_client:
            self.add_output("✗ Нет подключения к устройству")
            return
            
        try:
            macro = self.macro_manager.get_macro(macro_name)
            if not macro:
                self.add_output(f"✗ Макрос '{macro_name}' не найден")
                return
                
            def execute_macro_thread():
                try:
                    def update_start():
                        self.add_output(f"▶ Выполнение макроса: {macro_name}")
                        self.page.update()
                    
                    self.page.run_thread(update_start)
                    
                    for command in macro['commands']:
                        result = self.ssh_client.execute_command(command)
                        
                        def update_command(cmd=command, res=result):
                            self.add_output(f"$ {cmd}")
                            self.add_output(res)
                            self.add_output("-" * 30)
                            self.page.update()
                        
                        self.page.run_thread(update_command)
                    
                    def update_complete():
                        self.add_output(f"✓ Макрос '{macro_name}' выполнен успешно")
                        self.add_output("=" * 50)
                        self.page.update()
                    
                    self.page.run_thread(update_complete)
                    
                except Exception as e:
                    def update_error():
                        self.add_output(f"✗ Ошибка выполнения макроса: {str(e)}")
                        self.page.update()
                    
                    self.page.run_thread(update_error)
            
            threading.Thread(target=execute_macro_thread, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Macro execution error: {e}")
            self.add_output(f"✗ Ошибка: {str(e)}")
            
    def add_output(self, text):
        """Add text to output area"""
        current = self.output_text.value or ""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.output_text.value = f"{current}[{timestamp}] {text}\n"
        
    def clear_output(self, e=None):
        """Clear output area"""
        self.output_text.value = ""
        self.page.update()
        
    def load_commands(self):
        """Load commands from manager"""
        try:
            categories = self.command_manager.get_categories()
            self.logger.info(f"Loaded {len(categories)} command categories")
        except Exception as e:
            self.logger.error(f"Error loading commands: {e}")
            
    def load_macros(self):
        """Load macros from manager"""
        try:
            macros = self.macro_manager.get_all_macros()
            self.logger.info(f"Loaded {len(macros)} macros")
        except Exception as e:
            self.logger.error(f"Error loading macros: {e}")
            
    def on_keyboard_event(self, e: ft.KeyboardEvent):
        """Handle keyboard shortcuts"""
        if e.key == "F5":
            # F5 - Connect/Disconnect
            if self.connected:
                self.disconnect()
            else:
                self.show_connection_dialog()
        elif e.key == "F9" and self.connected:
            # F9 - Execute command
            self.execute_command()
        elif e.key == "F12":
            # F12 - Clear output
            self.clear_output()
        elif e.ctrl and e.key == "l":
            # Ctrl+L - Clear output
            self.clear_output()

def main():
    """Main entry point"""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Cisco Translator Flet application")
        
        # Create and run app
        app = CiscoTranslatorApp()
        ft.app(target=app.main, view=ft.AppView.FLET_APP)
        
    except Exception as e:
        logging.error(f"Failed to start Flet application: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()