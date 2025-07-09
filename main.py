#!/usr/bin/env python3
"""
Cisco Translator - Main Entry Point
A desktop application for Cisco CLI commands with Russian translation interface
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from core.logger import setup_logging

def main():
    """Main entry point for the Cisco Translator application"""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Cisco Translator application")
        
        # Create the main window
        root = tk.Tk()
        root.title("Cisco Translator")
        
        # Set window properties for better visibility
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
        app = MainWindow(root)
        
        # Ensure window is visible
        root.deiconify()
        root.lift()
        root.focus_force()
        
        logger.info("GUI initialized successfully")
        
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
        except:
            print(f"Critical error: {e}")
        logging.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
