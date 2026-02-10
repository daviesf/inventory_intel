import subprocess
import psutil
import time

def measure():
    # Start the demo engine
    proc = subprocess.Popen(['.venv\\Scripts\\python.exe', 'demo_engine.py'], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE)
    
    ps = psutil.Process(proc.pid)
    
    max_mem = 0
    max_cpu = 0
    
    # Sample for 5 seconds
    start = time.time()
    while time.time() - start < 5:
        if proc.poll() is not None:
            break
        try:
            mem = ps.memory_info().rss / (1024 * 1024)
            cpu = ps.cpu_percent(interval=0.1)
            if mem > max_mem: max_mem = mem
            if cpu > max_cpu: max_cpu = cpu
        except:
            break
            
    proc.terminate()
    return max_mem, max_cpu

mem, cpu = measure()
print(f"Max RAM (MB): {mem:.2f}")
print(f"Max CPU (%): {cpu:.2f}")
