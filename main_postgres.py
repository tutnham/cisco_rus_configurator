#!/usr/bin/env python3
"""
Cisco Translator - Main Entry Point with PostgreSQL support
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import setup_logging
from core.config_manager import ConfigManager
from core.database import DatabaseManager, PostgreSQLCommandManager, PostgreSQLMacroManager, PostgreSQLHistoryManager

class PostgreSQLMainWindow:
    def __init__(self, root):
        self.root = root
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        
        # Initialize database
        try:
            db_config = self.config_manager.get_database_config()
            self.db_manager = DatabaseManager(db_config)
            
            # Initialize managers with PostgreSQL support
            self.command_manager = PostgreSQLCommandManager(self.db_manager)
            self.macro_manager = PostgreSQLMacroManager(self.db_manager)
            self.history_manager = PostgreSQLHistoryManager(self.db_manager)
            
            self.logger.info("PostgreSQL managers initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL: {e}")
            messagebox.showerror(
                "Ошибка базы данных",
                f"Не удалось подключиться к PostgreSQL:\n{e}\n\nПроверьте настройки подключения."
            )
            sys.exit(1)
        
        # Application state
        self.connected = False
        self.current_connection_id = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Import GUI components
        from gui.main_window import MainWindow
        
        # Create main window with PostgreSQL managers
        self.main_window = MainWindow(self.root)
        
        # Replace managers with PostgreSQL versions
        self.main_window.command_manager = self.command_manager
        self.main_window.macro_manager = self.macro_manager
        
        # Reload data from PostgreSQL
        self.main_window.load_commands()
        self.main_window.load_macros()
        
        self.logger.info("UI setup with PostgreSQL completed")
        
    def on_closing(self):
        """Handle application closing"""
        try:
            if self.db_manager:
                self.db_manager.disconnect()
            self.root.destroy()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            self.root.destroy()

def main():
    """Main entry point for the Cisco Translator application with PostgreSQL"""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Cisco Translator with PostgreSQL support")
        
        # Create the main window
        root = tk.Tk()
        root.title("Cisco Translator (PostgreSQL)")
        
        # Set window properties
        root.geometry("1200x800")
        root.minsize(800, 600)
        
        # Center the window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create and show the main application window
        app = PostgreSQLMainWindow(root)
        
        # Set close handler
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Ensure window is visible
        root.deiconify()
        root.lift()
        root.focus_force()
        
        logger.info("GUI with PostgreSQL initialized successfully")
        
        # Start the GUI event loop
        root.mainloop()
        
    except Exception as e:
        # Show error dialog if application fails to start
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Ошибка запуска",
                f"Не удалось запустить приложение:\n{str(e)}"
            )
        except Exception as dialog_error:
            # Если не удается показать диалог, выводим в консоль
            print(f"Critical error: {e}")
            print(f"Dialog error: {dialog_error}")
        logging.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()