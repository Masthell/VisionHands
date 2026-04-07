@echo off
echo ==========================================
echo   GESTURE CONTROLLER - Build Script
echo ==========================================

REM Активируем виртуальное окружение если есть
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Проверяем наличие PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Устанавливаю PyInstaller...
    pip install pyinstaller
)

echo.
echo [INFO] Начинаю сборку .exe...
echo.

pyinstaller ^
    --onefile ^
    --noconsole ^
    --name GestureControl ^
    --add-data "models/hand_landmarker.task;models" ^
    --hidden-import mediapipe ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import pyautogui ^
    main.py

echo.
if exist "dist\GestureControl.exe" (
    echo ==========================================
    echo   ГОТОВО!
    echo   Файл: dist\GestureControl.exe
    echo ==========================================
    echo.
    echo Скопируй на флешку:
    echo   1. dist\GestureControl.exe
    echo   2. При первом запуске файл user_settings.db
    echo      создастся автоматически рядом с .exe
) else (
    echo [ОШИБКА] Сборка не удалась! Проверь логи выше.
)

pause
