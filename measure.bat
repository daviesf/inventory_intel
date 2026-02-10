@echo off
setlocal
set "VENV_PYTHON=.venv\Scripts\python.exe"
start "" /B %VENV_PYTHON% demo_engine.py
timeout /t 3 > nul
for /f "tokens=2 delims=," %%A in ('tasklist /nh /fi "imagename eq python.exe" /fo csv') do (
    set "PID=%%~A"
)
tasklist /fi "pid eq %PID%" /v
taskkill /f /pid %PID% > nul
