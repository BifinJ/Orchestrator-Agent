ROOT_CAUSE_ACTIONS = {
    "API": ["restart_api", "scale_api"],
    "AUTH": ["restart_auth"],
    "DB": ["restart_db", "increase_db_pool"],
    "CACHE": ["restart_cache"],
    "STORAGE": ["check_storage_latency"]
}

ACTION_RISK = {
    "restart_api": "low",
    "scale_api": "low",
    "restart_auth": "medium",
    "restart_db": "medium",
    "increase_db_pool": "medium",
    "restart_cache": "low",
    "check_storage_latency": "high"
}
