#!/usr/bin/env python3
"""
Test script to verify Flet installation and basic functionality
"""

try:
    import flet as ft
    print("✅ Flet imported successfully")
    
    def main(page: ft.Page):
        page.title = "Flet Test"
        page.add(ft.Text("Flet работает!"))
        
    print("✅ Starting Flet test app...")
    ft.app(target=main, view=ft.AppView.FLET_APP)
    
except ImportError as e:
    print(f"❌ Flet not installed: {e}")
    print("Run: pip install flet")
except Exception as e:
    print(f"❌ Error: {e}")