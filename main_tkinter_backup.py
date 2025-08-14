#!/usr/bin/env python3
"""
Cisco Translator - Main Entry Point
Modern desktop application for Cisco CLI commands with Russian translation interface using Flet
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flet version
from main_flet import main as flet_main
from core.logger import setup_logging

def main():
    """Main entry point for the Cisco Translator application"""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Cisco Translator Flet application")
        
        # Run Flet application
        flet_main()
        
    except Exception as e:
        logging.error(f"Failed to start Flet application: {e}")
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
