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
        root.withdraw()  # Hide root window initially
        
        # Create and show the main application window
        app = MainWindow(root)
        
        # Start the GUI event loop
        root.mainloop()
        
    except Exception as e:
        # Show error dialog if application fails to start
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Ошибка запуска",
            f"Не удалось запустить приложение:\n{str(e)}"
        )
        logging.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
