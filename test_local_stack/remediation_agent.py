import threading
import time

# ---------- Configuration ----------
CPU_THRESHOLD = 80      # %
MEMORY_THRESHOLD = 80   # %
DISK_THRESHOLD = 90     # %
ERROR_KEYWORDS = ["ERROR", "CRASH", "FAIL", "TIMEOUT"]
WARNING_KEYWORDS = ["WARNING", "SLOW", "HIGH USAGE"]

# ---------- Remediation Functions ----------
def handle_cpu_overload():
    print("[REMEDIATION] CPU too high! Consider scaling service or restarting worker.")

def handle_memory_overload():
    print("[REMEDIATION] Memory usage too high! Consider cleaning cache or restarting service.")

def handle_disk_overload():
    print("[REMEDIATION] Disk usage too high! Consider deleting temp files or expanding disk.")

def handle_error_log(message):
    print(f"[REMEDIATION] Detected error log: '{message}'. Suggesting fix/restart.")

def handle_warning_log(message):
    print(f"[REMEDIATION] Detected warning log: '{message}'. Suggesting monitoring.")

# ---------- Monitoring Threads ----------
def monitor_logs(log_queue):
    while True:
        if log_queue:
            message = log_queue.pop(0)
            if any(keyword in message for keyword in ERROR_KEYWORDS):
                handle_error_log(message)
            elif any(keyword in message for keyword in WARNING_KEYWORDS):
                handle_warning_log(message)
        time.sleep(1)

def monitor_metrics(metric_queue):
    while True:
        if metric_queue:
            metrics = metric_queue.pop(0)
            cpu, mem, disk = metrics
            if cpu > CPU_THRESHOLD:
                handle_cpu_overload()
            if mem > MEMORY_THRESHOLD:
                handle_memory_overload()
            if disk > DISK_THRESHOLD:
                handle_disk_overload()
        time.sleep(1)

# ---------- Main Orchestrator ----------
def remediation_agent(log_queue, metric_queue):
    # Run log and metric monitors in separate threads
    threading.Thread(target=monitor_logs, args=(log_queue,), daemon=True).start()
    threading.Thread(target=monitor_metrics, args=(metric_queue,), daemon=True).start()
    print("Remediation agent running...")

    while True:
        time.sleep(1)  # Keep main thread alive
