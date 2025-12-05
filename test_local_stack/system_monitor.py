import psutil
import time
from remediation_agent import remediation_agent
import threading

metric_queue = []

def monitor_system():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        print(f"CPU: {cpu}% | Memory: {mem}% | Disk: {disk}%")
        metric_queue.append((cpu, mem, disk))
        time.sleep(2)

if __name__ == "__main__":
    # Start remediation agent
    threading.Thread(target=remediation_agent, args=([], metric_queue), daemon=True).start()
    # Start system monitoring
    monitor_system()
