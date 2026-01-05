import math
from datetime import datetime
from collections import deque
from .config import TIME_WINDOW_MINUTES
from .dependency_graph import DEPENDENCY_GRAPH

def parse_timestamp(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

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
