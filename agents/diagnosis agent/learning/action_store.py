from collections import defaultdict

ACTION_STATS = defaultdict(lambda: {
    "success": 0,
    "failure": 0,
    "total_recovery_time": 0
})

def record_action(action, success, recovery_time):
    stats = ACTION_STATS[action]
    if success:
        stats["success"] += 1
    else:
        stats["failure"] += 1

    stats["total_recovery_time"] += recovery_time

def get_action_stats(action):
    stats = ACTION_STATS[action]
    total = stats["success"] + stats["failure"]
    if total == 0:
        return None

    return {
        "success_rate": stats["success"] / total,
        "avg_recovery_time": stats["total_recovery_time"] / max(stats["success"], 1)
    }
