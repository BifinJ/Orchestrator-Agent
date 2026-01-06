import math
from datetime import datetime
from collections import deque
from .config import TIME_WINDOW_MINUTES
from .dependency_graph import DEPENDENCY_GRAPH

# In your utils.py file
from datetime import datetime, timezone

def parse_timestamp(timestamp_str):
    """
    Parse timestamp string and ensure it's timezone-aware (UTC).
    Handles both ISO format with timezone and without.
    """
    try:
        # Try parsing with timezone info first
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # If naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
    except Exception as e:
        raise ValueError(f"Cannot parse timestamp: {timestamp_str}") from e

def temporal_decay(event_time, anomaly_time):
    delta = abs((anomaly_time - event_time).total_seconds())
    return math.exp(-delta / (TIME_WINDOW_MINUTES * 60))

def dependency_distance(source, target):
    if source == target:
        return 0

    visited = set()
    queue = deque([(source, 0)])

    while queue:
        node, dist = queue.popleft()
        if node == target:
            return dist
        for dep in DEPENDENCY_GRAPH.get(node, []):
            if dep not in visited:
                visited.add(dep)
                queue.append((dep, dist + 1))

    return float("inf")

def dependency_score(source, target):
    dist = dependency_distance(source, target)
    if dist == float("inf"):
        return 0.0
    return max(0.0, 1.0 - (0.3 * dist))
