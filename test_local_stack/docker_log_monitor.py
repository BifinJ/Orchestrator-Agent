import docker
from remediation_agent import remediation_agent
import threading

log_queue = []

def stream_logs(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    print(f"Streaming logs from: {container_name}")
    for line in container.logs(stream=True, follow=True):
        log_line = line.decode().strip()
        print("LOG:", log_line)
        log_queue.append(log_line)  # send log to remediation agent

if __name__ == "__main__":
    # Start remediation agent
    threading.Thread(target=remediation_agent, args=(log_queue, []), daemon=True).start()
    # Start log streaming
    stream_logs("test-backend-1")
