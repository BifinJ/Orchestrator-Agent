# agents/remediation_agent/book.py

# Algorithm line 1: A ← Retrievebook(C)
# Maps root cause → list of candidate actions WITH full scoring metadata
BOOK = {
    "api": [
        {"action": "restart_api",  "reversible": True,  "cost": 0.1, "blast_radius": 0.2},
        {"action": "scale_api",    "reversible": True,  "cost": 0.4, "blast_radius": 0.1},
    ],
    "AUTH": [
        {"action": "restart_auth", "reversible": True,  "cost": 0.3, "blast_radius": 0.5},
    ],
    "database": [
        {"action": "restart_db",        "reversible": True,  "cost": 0.5, "blast_radius": 0.7},
        {"action": "increase_db_pool",  "reversible": True,  "cost": 0.2, "blast_radius": 0.2},
    ],
    "CACHE": [
        {"action": "restart_cache", "reversible": True,  "cost": 0.1, "blast_radius": 0.3},
    ],
    "STORAGE": [
        {"action": "check_storage_latency", "reversible": False, "cost": 0.6, "blast_radius": 0.8},
    ],
}