@echo off
cd /d "%~dp0\.."
echo Starting IntelliStock Desktop...
.venv\Scripts\python.exe desktop_pywebview\app.py
pause
