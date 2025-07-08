"""
Main Window GUI for Cisco Translator
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import threading
import logging
from datetime import datetime

from gui.connection_dialog import ConnectionDialog
from gui.themes import ThemeManager
from core.ssh_client import SSHClient
from core.command_manager import CommandManager
from core.macro_manager import MacroManager
from core.security import SecureStorage

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers
        self.theme_manager = ThemeManager()
        self.command_manager = CommandManager()
        self.macro_manager = MacroManager()
        self.secure_storage = SecureStorage()
        self.ssh_client = None
        
        # Application state
        self.connected = False
        self.current_connection = None
        self.command_history = []
        self.last_command = None
        
        self.setup_ui()
        self.setup_bindings()
        self.load_commands()
        self.load_macros()
        
    def setup_ui(self):
        """Setup the main user interface"""
        self.root.title("Cisco Translator v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.theme_manager.apply_theme(self.style, "light")
        
        # Create main menu
        self.create_menu()
        
        # Create main layout
        self.create_main_layout()
        
        # Apply initial theme
        self.apply_current_theme()
        
        # Show window
        self.root.deiconify()
        
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Connection menu
        connection_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Подключение", menu=connection_menu)
        connection_menu.add_command(label="Новое подключение", command=self.show_connection_dialog)
        connection_menu.add_separator()
        connection_menu.add_command(label="Отключиться", command=self.disconnect)
        
        # Commands menu
        commands_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Команды", menu=commands_menu)
        commands_menu.add_command(label="Повторить последнюю команду", command=self.repeat_last_command)
        commands_menu.add_separator()
        commands_menu.add_command(label="Экспорт истории", command=self.export_history)
        commands_menu.add_command(label="Очистить историю", command=self.clear_history)
        
        # Macros menu
        macros_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Макросы", menu=macros_menu)
        macros_menu.add_command(label="Создать макрос", command=self.create_macro)
        macros_menu.add_command(label="Управление макросами", command=self.manage_macros)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)
        view_menu.add_command(label="Светлая тема", command=lambda: self.change_theme("light"))
        view_menu.add_command(label="Тёмная тема", command=lambda: self.change_theme("dark"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        
    def create_main_layout(self):
        """Create the main application layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top frame - connection status and controls
        self.create_top_frame(main_frame)
        
        # Middle frame - commands and macros
        self.create_middle_frame(main_frame)
        
        # Bottom frame - output and history
        self.create_bottom_frame(main_frame)
        
    def create_top_frame(self, parent):
        """Create top frame with connection controls"""
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Connection status
        status_frame = ttk.LabelFrame(top_frame, text="Статус подключения")
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.status_label = ttk.Label(status_frame, text="Не подключено", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Connection controls
        controls_frame = ttk.Frame(top_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        self.connect_btn = ttk.Button(controls_frame, text="Подключиться", command=self.show_connection_dialog)
        self.connect_btn.pack(side=tk.LEFT, padx=2)
        
        self.disconnect_btn = ttk.Button(controls_frame, text="Отключиться", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=2)
        
    def create_middle_frame(self, parent):
        """Create middle frame with commands and macros"""
        middle_frame = ttk.Frame(parent)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Left panel - commands
        left_frame = ttk.LabelFrame(middle_frame, text="Доступные команды")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Command categories
        categories_frame = ttk.Frame(left_frame)
        categories_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(categories_frame, text="Категория:").pack(side=tk.LEFT)
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(categories_frame, textvariable=self.category_var, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        # Commands listbox
        commands_list_frame = ttk.Frame(left_frame)
        commands_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        self.commands_listbox = tk.Listbox(commands_list_frame)
        commands_scrollbar = ttk.Scrollbar(commands_list_frame, orient=tk.VERTICAL, command=self.commands_listbox.yview)
        self.commands_listbox.config(yscrollcommand=commands_scrollbar.set)
        
        self.commands_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        commands_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Execute button
        self.execute_btn = ttk.Button(left_frame, text="Выполнить команду", command=self.execute_command, state=tk.DISABLED)
        self.execute_btn.pack(pady=5)
        
        # Right panel - macros
        right_frame = ttk.LabelFrame(middle_frame, text="Макросы")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_frame.config(width=250)
        right_frame.pack_propagate(False)
        
        # Macros listbox
        macros_list_frame = ttk.Frame(right_frame)
        macros_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.macros_listbox = tk.Listbox(macros_list_frame)
        macros_scrollbar = ttk.Scrollbar(macros_list_frame, orient=tk.VERTICAL, command=self.macros_listbox.yview)
        self.macros_listbox.config(yscrollcommand=macros_scrollbar.set)
        
        self.macros_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        macros_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Macro buttons
        macro_buttons_frame = ttk.Frame(right_frame)
        macro_buttons_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.execute_macro_btn = ttk.Button(macro_buttons_frame, text="Выполнить", command=self.execute_macro, state=tk.DISABLED)
        self.execute_macro_btn.pack(fill=tk.X, pady=1)
        
        ttk.Button(macro_buttons_frame, text="Создать", command=self.create_macro).pack(fill=tk.X, pady=1)
        ttk.Button(macro_buttons_frame, text="Редактировать", command=self.edit_macro).pack(fill=tk.X, pady=1)
        ttk.Button(macro_buttons_frame, text="Удалить", command=self.delete_macro).pack(fill=tk.X, pady=1)
        
    def create_bottom_frame(self, parent):
        """Create bottom frame with output and history"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(bottom_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Output tab
        output_frame = ttk.Frame(notebook)
        notebook.add(output_frame, text="Вывод команд")
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # History tab
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="История команд")
        
        self.history_text = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_bindings(self):
        """Setup event bindings"""
        self.commands_listbox.bind('<Double-Button-1>', lambda e: self.execute_command())
        self.macros_listbox.bind('<Double-Button-1>', lambda e: self.execute_macro())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_commands(self):
        """Load commands from the command manager"""
        try:
            categories = self.command_manager.get_categories()
            self.category_combo['values'] = categories
            if categories:
                self.category_combo.set(categories[0])
                self.on_category_change()
        except Exception as e:
            self.logger.error(f"Failed to load commands: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить команды: {e}")
            
    def load_macros(self):
        """Load macros from the macro manager"""
        try:
            macros = self.macro_manager.get_all_macros()
            self.macros_listbox.delete(0, tk.END)
            for macro_name in macros.keys():
                self.macros_listbox.insert(tk.END, macro_name)
        except Exception as e:
            self.logger.error(f"Failed to load macros: {e}")
            
    def on_category_change(self, event=None):
        """Handle category selection change"""
        category = self.category_var.get()
        if category:
            commands = self.command_manager.get_commands_by_category(category)
            self.commands_listbox.delete(0, tk.END)
            for cmd_info in commands:
                self.commands_listbox.insert(tk.END, cmd_info['description'])
                
    def show_connection_dialog(self):
        """Show connection configuration dialog"""
        dialog = ConnectionDialog(self.root, self.secure_storage)
        if dialog.result:
            self.connect_to_device(dialog.result)
            
    def connect_to_device(self, connection_info):
        """Connect to Cisco device"""
        def connect_thread():
            try:
                self.ssh_client = SSHClient()
                success = self.ssh_client.connect(
                    connection_info['host'],
                    connection_info['username'],
                    connection_info['password'],
                    connection_info.get('port', 22)
                )
                
                if success:
                    self.root.after(0, self.on_connection_success, connection_info)
                else:
                    self.root.after(0, self.on_connection_failure, "Connection failed")
                    
            except Exception as e:
                self.root.after(0, self.on_connection_failure, str(e))
                
        # Disable connect button and show connecting status
        self.connect_btn.config(state=tk.DISABLED, text="Подключение...")
        self.status_label.config(text="Подключение...", foreground="orange")
        
        # Start connection in separate thread
        threading.Thread(target=connect_thread, daemon=True).start()
        
    def on_connection_success(self, connection_info):
        """Handle successful connection"""
        self.connected = True
        self.current_connection = connection_info
        
        self.status_label.config(text=f"Подключено к {connection_info['host']}", foreground="green")
        self.connect_btn.config(state=tk.NORMAL, text="Подключиться")
        self.disconnect_btn.config(state=tk.NORMAL)
        self.execute_btn.config(state=tk.NORMAL)
        self.execute_macro_btn.config(state=tk.NORMAL)
        
        self.add_to_output(f"Успешно подключено к {connection_info['host']}\n")
        self.logger.info(f"Connected to {connection_info['host']}")
        
    def on_connection_failure(self, error_msg):
        """Handle connection failure"""
        self.connected = False
        self.current_connection = None
        
        self.status_label.config(text="Не подключено", foreground="red")
        self.connect_btn.config(state=tk.NORMAL, text="Подключиться")
        
        messagebox.showerror("Ошибка подключения", f"Не удалось подключиться:\n{error_msg}")
        self.logger.error(f"Connection failed: {error_msg}")
        
    def disconnect(self):
        """Disconnect from device"""
        if self.ssh_client:
            self.ssh_client.disconnect()
            self.ssh_client = None
            
        self.connected = False
        self.current_connection = None
        
        self.status_label.config(text="Не подключено", foreground="red")
        self.disconnect_btn.config(state=tk.DISABLED)
        self.execute_btn.config(state=tk.DISABLED)
        self.execute_macro_btn.config(state=tk.DISABLED)
        
        self.add_to_output("Отключено от устройства\n")
        self.logger.info("Disconnected from device")
        
    def execute_command(self):
        """Execute selected command"""
        if not self.connected or not self.ssh_client:
            messagebox.showwarning("Предупреждение", "Нет подключения к устройству")
            return
            
        selection = self.commands_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите команду для выполнения")
            return
            
        # Get selected command
        category = self.category_var.get()
        commands = self.command_manager.get_commands_by_category(category)
        selected_index = selection[0]
        
        if selected_index < len(commands):
            command_info = commands[selected_index]
            command = command_info['command']
            description = command_info['description']
            
            self.execute_command_async(command, description)
            
    def execute_command_async(self, command, description):
        """Execute command asynchronously"""
        def execute_thread():
            try:
                result = self.ssh_client.execute_command(command)
                self.root.after(0, self.on_command_result, command, description, result)
            except Exception as e:
                self.root.after(0, self.on_command_error, command, description, str(e))
                
        threading.Thread(target=execute_thread, daemon=True).start()
        
    def on_command_result(self, command, description, result):
        """Handle command execution result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to output
        output_text = f"[{timestamp}] {description}\n"
        output_text += f"Команда: {command}\n"
        output_text += f"Результат:\n{result}\n"
        output_text += "-" * 50 + "\n"
        
        self.add_to_output(output_text)
        
        # Add to history
        history_entry = f"[{timestamp}] {description} -> {command}"
        self.command_history.append(history_entry)
        self.add_to_history(history_entry + "\n")
        
        # Store last command
        self.last_command = (command, description)
        
        self.logger.info(f"Executed command: {command}")
        
    def on_command_error(self, command, description, error_msg):
        """Handle command execution error"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        error_text = f"[{timestamp}] ОШИБКА: {description}\n"
        error_text += f"Команда: {command}\n"
        error_text += f"Ошибка: {error_msg}\n"
        error_text += "-" * 50 + "\n"
        
        self.add_to_output(error_text)
        self.logger.error(f"Command execution failed: {command} - {error_msg}")
        
    def execute_macro(self):
        """Execute selected macro"""
        if not self.connected or not self.ssh_client:
            messagebox.showwarning("Предупреждение", "Нет подключения к устройству")
            return
            
        selection = self.macros_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите макрос для выполнения")
            return
            
        macro_name = self.macros_listbox.get(selection[0])
        macro = self.macro_manager.get_macro(macro_name)
        
        if macro:
            self.execute_macro_async(macro_name, macro)
            
    def execute_macro_async(self, macro_name, macro):
        """Execute macro asynchronously"""
        def execute_thread():
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.root.after(0, self.add_to_output, f"[{timestamp}] Выполнение макроса: {macro_name}\n")
                
                for command in macro['commands']:
                    result = self.ssh_client.execute_command(command)
                    self.root.after(0, self.on_command_result, command, f"Макрос: {macro_name}", result)
                    
                self.root.after(0, self.add_to_output, f"Макрос {macro_name} выполнен\n")
                
            except Exception as e:
                self.root.after(0, self.on_command_error, f"Макрос: {macro_name}", macro_name, str(e))
                
        threading.Thread(target=execute_thread, daemon=True).start()
        
    def repeat_last_command(self):
        """Repeat the last executed command"""
        if self.last_command:
            command, description = self.last_command
            self.execute_command_async(command, description)
        else:
            messagebox.showinfo("Информация", "Нет команд для повтора")
            
    def add_to_output(self, text):
        """Add text to output window"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        
    def add_to_history(self, text):
        """Add text to history window"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.insert(tk.END, text)
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)
        
    def export_history(self):
        """Export command history to file"""
        if not self.command_history:
            messagebox.showinfo("Информация", "История команд пуста")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("История команд Cisco Translator\n")
                    f.write("=" * 40 + "\n\n")
                    for entry in self.command_history:
                        f.write(entry + "\n")
                        
                messagebox.showinfo("Успех", f"История экспортирована в {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать историю:\n{e}")
                
    def clear_history(self):
        """Clear command history"""
        if messagebox.askyesno("Подтверждение", "Очистить историю команд?"):
            self.command_history.clear()
            self.history_text.config(state=tk.NORMAL)
            self.history_text.delete(1.0, tk.END)
            self.history_text.config(state=tk.DISABLED)
            
    def create_macro(self):
        """Create new macro"""
        # This would open a macro creation dialog
        messagebox.showinfo("Информация", "Функция создания макросов будет реализована в следующей версии")
        
    def manage_macros(self):
        """Open macro management dialog"""
        messagebox.showinfo("Информация", "Функция управления макросами будет реализована в следующей версии")
        
    def edit_macro(self):
        """Edit selected macro"""
        messagebox.showinfo("Информация", "Функция редактирования макросов будет реализована в следующей версии")
        
    def delete_macro(self):
        """Delete selected macro"""
        selection = self.macros_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите макрос для удаления")
            return
            
        macro_name = self.macros_listbox.get(selection[0])
        if messagebox.askyesno("Подтверждение", f"Удалить макрос '{macro_name}'?"):
            try:
                self.macro_manager.delete_macro(macro_name)
                self.load_macros()
                messagebox.showinfo("Успех", f"Макрос '{macro_name}' удален")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить макрос:\n{e}")
                
    def change_theme(self, theme_name):
        """Change application theme"""
        self.theme_manager.apply_theme(self.style, theme_name)
        self.apply_current_theme()
        
    def apply_current_theme(self):
        """Apply current theme to all widgets"""
        # This method would apply theme-specific styling
        pass
        
    def show_about(self):
        """Show about dialog"""
        about_text = """Cisco Translator v1.0

Приложение для работы с Cisco CLI командами
с русским интерфейсом и поддержкой SSH.

Функции:
• SSH подключение к устройствам Cisco
• Русский интерфейс для CLI команд
• Выполнение команд с выводом результатов
• Система макросов для частых команд
• История команд и экспорт логов
• Поддержка светлой и тёмной темы

© 2025 Cisco Translator"""
        
        messagebox.showinfo("О программе", about_text)
        
    def on_closing(self):
        """Handle application closing"""
        if self.connected:
            if messagebox.askyesno("Подтверждение", "Активно подключение к устройству. Закрыть приложение?"):
                self.disconnect()
                self.root.destroy()
        else:
            self.root.destroy()
