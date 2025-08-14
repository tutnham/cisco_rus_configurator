#!/bin/bash

echo "🚀 Cisco Translator - Запуск приложения"
echo "================================================"

python3 run.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Приложение завершено успешно"
else
    echo ""
    echo "❌ Приложение завершилось с ошибкой"
    read -p "Нажмите Enter для продолжения..."
fi