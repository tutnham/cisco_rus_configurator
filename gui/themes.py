"""
Theme Management for Cisco Translator
"""

import tkinter as tk
from tkinter import ttk

class ThemeManager:
    def __init__(self):
        self.themes = {
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'entry_bg': '#ffffff',
                'entry_fg': '#000000',
                'button_bg': '#f0f0f0',
                'button_fg': '#000000',
                'frame_bg': '#f8f8f8',
                'text_bg': '#ffffff',
                'text_fg': '#000000'
            },
            'dark': {
                'bg': '#2d2d2d',
                'fg': '#ffffff',
                'select_bg': '#404040',
                'select_fg': '#ffffff',
                'entry_bg': '#404040',
                'entry_fg': '#ffffff',
                'button_bg': '#404040',
                'button_fg': '#ffffff',
                'frame_bg': '#3d3d3d',
                'text_bg': '#2d2d2d',
                'text_fg': '#ffffff'
            }
        }
        self.current_theme = 'light'
        
    def apply_theme(self, style, theme_name):
        """Apply theme to ttk styles"""
        if theme_name not in self.themes:
            theme_name = 'light'
            
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # Configure ttk styles
        style.theme_use('clam')
        
        # Configure frame styles
        style.configure('TFrame', 
                       background=theme['frame_bg'])
        
        style.configure('TLabelFrame', 
                       background=theme['frame_bg'],
                       foreground=theme['fg'])
        
        style.configure('TLabelFrame.Label',
                       background=theme['frame_bg'],
                       foreground=theme['fg'])
        
        # Configure label styles
        style.configure('TLabel',
                       background=theme['frame_bg'],
                       foreground=theme['fg'])
        
        # Configure button styles
        style.configure('TButton',
                       background=theme['button_bg'],
                       foreground=theme['button_fg'],
                       borderwidth=1,
                       focuscolor='none')
        
        style.map('TButton',
                 background=[('active', theme['select_bg']),
                            ('pressed', theme['select_bg'])],
                 foreground=[('active', theme['select_fg']),
                            ('pressed', theme['select_fg'])])
        
        # Configure entry styles
        style.configure('TEntry',
                       fieldbackground=theme['entry_bg'],
                       foreground=theme['entry_fg'],
                       borderwidth=1)
        
        style.map('TEntry',
                 focuscolor=[('!focus', theme['entry_bg'])])
        
        # Configure combobox styles
        style.configure('TCombobox',
                       fieldbackground=theme['entry_bg'],
                       foreground=theme['entry_fg'],
                       background=theme['button_bg'],
                       borderwidth=1)
        
        style.map('TCombobox',
                 fieldbackground=[('readonly', theme['entry_bg'])],
                 selectbackground=[('readonly', theme['select_bg'])],
                 selectforeground=[('readonly', theme['select_fg'])])
        
        # Configure notebook styles
        style.configure('TNotebook',
                       background=theme['frame_bg'],
                       borderwidth=0)
        
        style.configure('TNotebook.Tab',
                       background=theme['button_bg'],
                       foreground=theme['fg'],
                       padding=[10, 5])
        
        style.map('TNotebook.Tab',
                 background=[('selected', theme['select_bg']),
                            ('active', theme['button_bg'])],
                 foreground=[('selected', theme['select_fg']),
                            ('active', theme['fg'])])
        
        # Configure checkbutton styles
        style.configure('TCheckbutton',
                       background=theme['frame_bg'],
                       foreground=theme['fg'],
                       focuscolor='none')
        
        style.map('TCheckbutton',
                 background=[('active', theme['frame_bg'])])
        
        # Configure radiobutton styles
        style.configure('TRadiobutton',
                       background=theme['frame_bg'],
                       foreground=theme['fg'],
                       focuscolor='none')
        
        style.map('TRadiobutton',
                 background=[('active', theme['frame_bg'])])
        
        # Configure scrollbar styles
        style.configure('TScrollbar',
                       background=theme['button_bg'],
                       troughcolor=theme['frame_bg'],
                       borderwidth=1,
                       arrowcolor=theme['fg'])
        
        style.map('TScrollbar',
                 background=[('active', theme['select_bg'])])
        
    def get_theme_colors(self, theme_name=None):
        """Get colors for the specified theme"""
        if theme_name is None:
            theme_name = self.current_theme
            
        return self.themes.get(theme_name, self.themes['light'])
        
    def configure_widget_theme(self, widget, theme_name=None):
        """Configure a specific widget with theme colors"""
        colors = self.get_theme_colors(theme_name)
        
        try:
            if isinstance(widget, tk.Listbox):
                widget.configure(
                    bg=colors['text_bg'],
                    fg=colors['text_fg'],
                    selectbackground=colors['select_bg'],
                    selectforeground=colors['select_fg'],
                    highlightbackground=colors['frame_bg'],
                    highlightcolor=colors['select_bg']
                )
            elif isinstance(widget, tk.Text):
                widget.configure(
                    bg=colors['text_bg'],
                    fg=colors['text_fg'],
                    selectbackground=colors['select_bg'],
                    selectforeground=colors['select_fg'],
                    insertbackground=colors['text_fg'],
                    highlightbackground=colors['frame_bg'],
                    highlightcolor=colors['select_bg']
                )
            elif isinstance(widget, tk.Menu):
                widget.configure(
                    bg=colors['frame_bg'],
                    fg=colors['fg'],
                    activebackground=colors['select_bg'],
                    activeforeground=colors['select_fg']
                )
        except tk.TclError:
            # Some widgets might not support all options
            pass
