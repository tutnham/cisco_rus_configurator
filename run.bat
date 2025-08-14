@echo off
chcp 65001 >nul
title Cisco Translator

echo 🚀 Cisco Translator - Запуск приложения
echo ================================================

python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Приложение завершилось с ошибкой
    pause
) else (
    echo.
    echo ✅ Приложение завершено успешно
)