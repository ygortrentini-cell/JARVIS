@echo off
cd /d "%~dp0"
set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"
"%PYTHON%" -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo As dependencias do JARVIS ainda nao estao instaladas.
    echo Instale os pacotes listados em requirements.txt e tente novamente.
    pause
    exit /b 1
)
"%PYTHON%" main.py
pause
