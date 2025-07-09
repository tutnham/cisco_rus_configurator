#!/usr/bin/env python3
"""
Simple GUI test for Cisco Translator
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

def test_gui():
    """Test basic GUI functionality"""
    root = tk.Tk()
    root.title("Cisco Translator - Тест")
    root.geometry("800x600")
    
    # Main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Title
    title_label = ttk.Label(main_frame, text="Cisco Translator", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)
    
    # Status
    status_frame = ttk.LabelFrame(main_frame, text="Статус подключения")
    status_frame.pack(fill=tk.X, pady=5)
    
    status_label = ttk.Label(status_frame, text="Не подключено", foreground="red")
    status_label.pack(pady=5)
    
    # Connect button
    connect_btn = ttk.Button(main_frame, text="Подключиться", 
                            command=lambda: messagebox.showinfo("Тест", "Кнопка работает!"))
    connect_btn.pack(pady=5)
    
    # Commands
    commands_frame = ttk.LabelFrame(main_frame, text="Доступные команды")
    commands_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    commands_list = tk.Listbox(commands_frame)
    commands_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Add sample commands
    sample_commands = [
        "Показать версию ПО и информацию об устройстве",
        "Показать текущую конфигурацию",
        "Показать краткую информацию об IP интерфейсах",
        "Показать состояние всех интерфейсов"
    ]
    
    for cmd in sample_commands:
        commands_list.insert(tk.END, cmd)
    
    # Execute button
    execute_btn = ttk.Button(main_frame, text="Выполнить команду",
                            command=lambda: messagebox.showinfo("Тест", "Команда выполнена!"))
    execute_btn.pack(pady=5)
    
    # Output
    output_frame = ttk.LabelFrame(main_frame, text="Вывод команд")
    output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    output_text = tk.Text(output_frame, height=6)
    output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    output_text.insert('1.0', "Добро пожаловать в Cisco Translator!\nВыберите команду и нажмите 'Выполнить команду'.")
    
    print("GUI создан успешно. Запуск главного цикла...")
    
    # Ensure window is visible
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(lambda: root.attributes('-topmost', False))
    
    root.mainloop()

if __name__ == "__main__":
    print("Запуск тестового GUI...")
    try:
        test_gui()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()