
import time


def execute_action(action: str) -> dict:
    """
    Simulated remediation execution.
    Replace with AWS calls later.
    """

    start = time.time()

    print(f"[EXECUTOR] Running action: {action}")
    time.sleep(2)  # simulate delay

    # Deterministic demo behavior
    success_actions = {
        "restart_api",
        "restart_db",
        "clear_cache",
        "scale_api"
    }

    success = action in success_actions

    return {
        "success": success,
        "recovery_time": int(time.time() - start)
    }
