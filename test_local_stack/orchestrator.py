import threading
import time
import docker
import psutil

# ----------------- Queues -----------------
log_queue = []
metric_queue = []

# ----------------- Monitoring Agent -----------------
def monitor_logs():
    while True:
        if log_queue:
            message = log_queue.pop(0)
            print("[LOG MONITOR]", message)
        time.sleep(0.5)

def monitor_metrics():
    while True:
        if metric_queue:
            cpu, mem, disk = metric_queue.pop(0)
            print(f"[METRICS] CPU: {cpu}% | Memory: {mem}% | Disk: {disk}%")
        time.sleep(1)

def monitoring_agent():
    threading.Thread(target=monitor_logs, daemon=True).start()
    threading.Thread(target=monitor_metrics, daemon=True).start()
    print("Monitoring agent running...")

# ----------------- Docker Log Monitor -----------------
def stream_logs(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    print(f"Streaming logs from container: {container_name}")
    for line in container.logs(stream=True, follow=True):
        log_line = line.decode().strip()
        log_queue.append(log_line)

# ----------------- System Metrics Monitor -----------------
def monitor_system():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        metric_queue.append((cpu, mem, disk))
        time.sleep(2)

# ----------------- Main -----------------
if __name__ == "__main__":
    # Start monitoring agent
    threading.Thread(target=monitoring_agent, daemon=True).start()

    # Start Docker log streaming (replace with your container name)
    threading.Thread(target=stream_logs, args=("flask-backend",), daemon=True).start()

    # Start system monitoring
    threading.Thread(target=monitor_system, daemon=True).start()

    # Keep main thread alive
    while True:
        time.sleep(1)
