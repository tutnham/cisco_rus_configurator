"""
Connection Dialog for SSH/Telnet/COM connections
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

class ConnectionDialog:
    def __init__(self, parent, secure_storage):
        self.parent = parent
        self.secure_storage = secure_storage
        self.result = None
        self.logger = logging.getLogger(__name__)
        
        self.create_dialog()
        
    def create_dialog(self):
        """Create connection configuration dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Настройка подключения")
        self.dialog.geometry("400x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Connection type frame
        type_frame = ttk.LabelFrame(self.dialog, text="Тип подключения")
        type_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.connection_type = tk.StringVar(value="ssh")
        
        ttk.Radiobutton(type_frame, text="SSH", variable=self.connection_type, 
                       value="ssh", command=self.on_type_change).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(type_frame, text="Telnet", variable=self.connection_type, 
                       value="telnet", command=self.on_type_change).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(type_frame, text="COM Port", variable=self.connection_type, 
                       value="com", command=self.on_type_change).pack(anchor=tk.W, padx=5, pady=2)
        
        # Connection parameters frame
        params_frame = ttk.LabelFrame(self.dialog, text="Параметры подключения")
        params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create input fields
        self.create_input_fields(params_frame)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(buttons_frame, text="Подключиться", command=self.connect).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(buttons_frame, text="Отмена", command=self.cancel).pack(side=tk.RIGHT)
        
        # Load saved connections
        self.load_saved_connections()
        
        # Set initial focus
        self.host_entry.focus()
        
    def create_input_fields(self, parent):
        """Create input fields for connection parameters"""
        # Host/IP
        ttk.Label(parent, text="Хост/IP адрес:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.host_var = tk.StringVar()
        self.host_entry = ttk.Entry(parent, textvariable=self.host_var, width=30)
        self.host_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Port
        ttk.Label(parent, text="Порт:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_var = tk.StringVar(value="22")
        self.port_entry = ttk.Entry(parent, textvariable=self.port_var, width=30)
        self.port_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Username
        ttk.Label(parent, text="Имя пользователя:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(parent, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Password
        ttk.Label(parent, text="Пароль:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(parent, textvariable=self.password_var, show="*", width=30)
        self.password_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # COM Port specific fields (initially hidden)
        self.com_label = ttk.Label(parent, text="COM порт:")
        self.com_var = tk.StringVar()
        self.com_combo = ttk.Combobox(parent, textvariable=self.com_var, values=self.get_com_ports(), width=28)
        
        self.baud_label = ttk.Label(parent, text="Скорость (бод):")
        self.baud_var = tk.StringVar(value="9600")
        self.baud_combo = ttk.Combobox(parent, textvariable=self.baud_var, 
                                      values=["9600", "19200", "38400", "57600", "115200"], width=28)
        
        # Save credentials checkbox
        self.save_var = tk.BooleanVar()
        self.save_check = ttk.Checkbutton(parent, text="Сохранить учетные данные", variable=self.save_var)
        self.save_check.grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Configure grid weights
        parent.columnconfigure(1, weight=1)
        
    def get_com_ports(self):
        """Get available COM ports"""
        try:
            import serial.tools.list_ports
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return ports if ports else ["COM1", "COM2", "COM3", "/dev/ttyUSB0", "/dev/ttyS0"]
        except ImportError:
            # Fallback if pyserial is not available
            return ["COM1", "COM2", "COM3", "/dev/ttyUSB0", "/dev/ttyS0"]
        
    def on_type_change(self):
        """Handle connection type change"""
        conn_type = self.connection_type.get()
        
        if conn_type == "ssh":
            self.port_var.set("22")
            self.show_network_fields()
        elif conn_type == "telnet":
            self.port_var.set("23")
            self.show_network_fields()
        elif conn_type == "com":
            self.show_com_fields()
            
    def show_network_fields(self):
        """Show network connection fields"""
        # Hide COM fields
        self.com_label.grid_remove()
        self.com_combo.grid_remove()
        self.baud_label.grid_remove()
        self.baud_combo.grid_remove()
        
        # Show network fields
        self.host_entry.grid()
        self.port_entry.grid()
        self.username_entry.grid()
        self.password_entry.grid()
        
    def show_com_fields(self):
        """Show COM port connection fields"""
        # Show COM fields
        self.com_label.grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.com_combo.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        self.baud_label.grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.baud_combo.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
        
    def load_saved_connections(self):
        """Load saved connection information"""
        try:
            saved_data = self.secure_storage.load_connection_data()
            if saved_data:
                self.host_var.set(saved_data.get('host', ''))
                self.username_var.set(saved_data.get('username', ''))
                if saved_data.get('save_credentials', False):
                    self.save_var.set(True)
        except Exception as e:
            self.logger.warning(f"Could not load saved connections: {e}")
            
    def save_connection(self, connection_info):
        """Save connection information if requested"""
        if self.save_var.get():
            try:
                save_data = {
                    'host': connection_info['host'],
                    'username': connection_info['username'],
                    'save_credentials': True
                }
                self.secure_storage.save_connection_data(save_data)
            except Exception as e:
                self.logger.error(f"Failed to save connection data: {e}")
                
    def validate_input(self):
        """Validate user input"""
        conn_type = self.connection_type.get()
        
        if conn_type in ["ssh", "telnet"]:
            if not self.host_var.get().strip():
                messagebox.showerror("Ошибка", "Укажите хост или IP адрес")
                return False
                
            if not self.port_var.get().strip():
                messagebox.showerror("Ошибка", "Укажите порт")
                return False
                
            try:
                port = int(self.port_var.get())
                if port < 1 or port > 65535:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный номер порта")
                return False
                
            if not self.username_var.get().strip():
                messagebox.showerror("Ошибка", "Укажите имя пользователя")
                return False
                
            if not self.password_var.get():
                messagebox.showerror("Ошибка", "Укажите пароль")
                return False
                
        elif conn_type == "com":
            if not self.com_var.get().strip():
                messagebox.showerror("Ошибка", "Выберите COM порт")
                return False
                
            if not self.baud_var.get().strip():
                messagebox.showerror("Ошибка", "Выберите скорость передачи")
                return False
                
        return True
        
    def connect(self):
        """Handle connect button click"""
        if not self.validate_input():
            return
            
        conn_type = self.connection_type.get()
        
        if conn_type in ["ssh", "telnet"]:
            connection_info = {
                'type': conn_type,
                'host': self.host_var.get().strip(),
                'port': int(self.port_var.get()),
                'username': self.username_var.get().strip(),
                'password': self.password_var.get()
            }
        else:  # COM
            connection_info = {
                'type': 'com',
                'port': self.com_var.get().strip(),
                'baudrate': int(self.baud_var.get())
            }
            
        # Save connection if requested
        self.save_connection(connection_info)
        
        self.result = connection_info
        self.dialog.destroy()
        
    def cancel(self):
        """Handle cancel button click"""
        self.result = None
        self.dialog.destroy()
