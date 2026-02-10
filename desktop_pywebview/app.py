"""
IntelliStock Desktop App
Lightweight wrapper using PyWebView
"""
import webview
import subprocess
import requests
import time
import sys
import os
from pathlib import Path

# Configuration
CONFIG = {
    "engine_port": 8000,
    "dashboard_url": "http://127.0.0.1:8000/dashboard",
    "health_endpoint": "http://127.0.0.1:8000/metrics",
    "auto_start_engine": True,
    "max_retries": 30,
    "retry_delay_sec": 1.0,
}

engine_process = None


def check_engine_health() -> bool:
    """Check if engine is responding."""
    try:
        response = requests.get(CONFIG["health_endpoint"], timeout=2)
        return response.ok
    except Exception:
        return False


def start_engine():
    """Start the engine subprocess."""
    global engine_process
    
    # Get the project root (parent of desktop_pywebview)
    project_root = Path(__file__).parent.parent
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print(f"Python not found at {venv_python}")
        return False
    
    # Start uvicorn
    cmd = [
        str(venv_python),
        "-m", "uvicorn",
        "local_api.app:app",
        "--host", "127.0.0.1",
        "--port", str(CONFIG["engine_port"])
    ]
    
    engine_process = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return True


def wait_for_engine() -> bool:
    """Wait for engine to be ready."""
    for i in range(CONFIG["max_retries"]):
        if check_engine_health():
            return True
        time.sleep(CONFIG["retry_delay_sec"])
    return False


def cleanup():
    """Clean up engine process on exit."""
    global engine_process
    if engine_process:
        engine_process.terminate()
        try:
            engine_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            engine_process.kill()


def main():
    # Check if engine is already running
    if check_engine_health():
        print("Engine already running.")
    elif CONFIG["auto_start_engine"]:
        print("Starting engine...")
        if not start_engine():
            print("Failed to start engine.")
            sys.exit(1)
        
        print("Waiting for engine...")
        if not wait_for_engine():
            print("Engine did not start in time.")
            cleanup()
            sys.exit(1)
        print("Engine ready!")
    else:
        print("Engine not running and auto-start disabled.")
        sys.exit(1)
    
    # Create window
    window = webview.create_window(
        title="IntelliStock Desktop",
        url=CONFIG["dashboard_url"],
        width=1280,
        height=720,
        min_size=(800, 600),
        resizable=True,
    )
    
    # Start webview (blocking)
    webview.start()
    
    # Cleanup on exit
    cleanup()


if __name__ == "__main__":
    main()
