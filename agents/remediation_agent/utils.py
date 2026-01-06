
def is_safe_action(action: str) -> bool:
    unsafe = {"terminate_instance", "delete_db"}
    return action not in unsafe
