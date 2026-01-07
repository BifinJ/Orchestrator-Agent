# agents/diagnosis_agent/dependency_graph.py

from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque


class DependencyGraph:
    """
    Advanced dependency graph with bidirectional relationships,
    health tracking, and impact analysis capabilities.
    """
    
    def __init__(self):
        # Forward dependencies (service -> what it depends on)
        self.dependencies: Dict[str, List[Dict]] = {
            "api": [
                {"service": "auth", "type": "required", "latency_impact": "high"},
                {"service": "cache", "type": "optional", "latency_impact": "medium"},
                {"service": "database", "type": "required", "latency_impact": "high"},
                {"service": "queue", "type": "optional", "latency_impact": "low"}
            ],
            "auth": [
                {"service": "database", "type": "required", "latency_impact": "high"},
                {"service": "cache", "type": "optional", "latency_impact": "medium"}
            ],
            "database": [
                {"service": "storage", "type": "required", "latency_impact": "high"},
                {"service": "network", "type": "required", "latency_impact": "high"}
            ],
            "cache": [
                {"service": "network", "type": "required", "latency_impact": "high"},
                {"service": "storage", "type": "optional", "latency_impact": "low"}
            ],
            "queue": [
                {"service": "network", "type": "required", "latency_impact": "medium"},
                {"service": "storage", "type": "optional", "latency_impact": "low"}
            ],
            "storage": [
                {"service": "compute", "type": "required", "latency_impact": "medium"}
            ],
            "network": [
                {"service": "compute", "type": "required", "latency_impact": "low"}
            ],
            "compute": [],  # Base infrastructure (EC2, etc.)
            "load_balancer": [
                {"service": "api", "type": "required", "latency_impact": "high"},
                {"service": "network", "type": "required", "latency_impact": "high"}
            ],
            "worker": [
                {"service": "queue", "type": "required", "latency_impact": "high"},
                {"service": "database", "type": "optional", "latency_impact": "medium"}
            ],
            "lambda": [
                {"service": "api", "type": "optional", "latency_impact": "medium"},
                {"service": "database", "type": "optional", "latency_impact": "medium"}
            ]
        }
        
        # Reverse lookup cache (what depends on this service)
        self._reverse_deps: Optional[Dict[str, List[str]]] = None
        
        # Service health state
        self.health_state: Dict[str, Dict] = {}
        
        # Cascading failure tracking
        self.failure_history: List[Dict] = []
    
    def get_dependencies(self, service: str, 
                        dependency_type: Optional[str] = None) -> List[str]:
        """
        Get all dependencies for a service.
        
        Args:
            service: The service name
            dependency_type: Filter by type ('required', 'optional', or None for all)
        
        Returns:
            List of dependent service names
        """
        deps = self.dependencies.get(service, [])
        
        if dependency_type:
            deps = [d for d in deps if d.get("type") == dependency_type]
        
        return [d["service"] for d in deps]
    
    def get_dependents(self, service: str) -> List[str]:
        """
        Get all services that depend on this service (reverse lookup).
        
        Args:
            service: The service name
        
        Returns:
            List of services that depend on this service
        """
        if self._reverse_deps is None:
            self._build_reverse_deps()
        
        return self._reverse_deps.get(service, [])
    
    def _build_reverse_deps(self):
        """Build reverse dependency lookup table."""
        self._reverse_deps = defaultdict(list)
        
        for service, deps in self.dependencies.items():
            for dep in deps:
                dep_service = dep["service"]
                self._reverse_deps[dep_service].append(service)
    
    def get_all_dependencies_recursive(self, service: str, 
                                      visited: Optional[Set[str]] = None) -> List[str]:
        """
        Get all dependencies recursively (entire dependency tree).
        
        Args:
            service: The service name
            visited: Set of already visited services (for cycle detection)
        
        Returns:
            List of all services in dependency tree
        """
        if visited is None:
            visited = set()
        
        if service in visited:
            return []  # Cycle detected
        
        visited.add(service)
        all_deps = []
        
        direct_deps = self.get_dependencies(service)
        for dep in direct_deps:
            if dep not in all_deps:
                all_deps.append(dep)
                # Recursively get dependencies of dependencies
                sub_deps = self.get_all_dependencies_recursive(dep, visited.copy())
                for sub_dep in sub_deps:
                    if sub_dep not in all_deps:
                        all_deps.append(sub_dep)
        
        return all_deps
    
    def get_impact_radius(self, service: str) -> List[Tuple[str, int]]:
        """
        Calculate impact radius: all services affected if this service fails.
        
        Args:
            service: The failing service
        
        Returns:
            List of (service, distance) tuples sorted by distance
        """
        if self._reverse_deps is None:
            self._build_reverse_deps()
        
        impact = []
        visited = set()
        queue = deque([(service, 0)])
        
        while queue:
            current, distance = queue.popleft()
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if distance > 0:  # Don't include the failing service itself
                impact.append((current, distance))
            
            # Get services that depend on current service
            dependents = self.get_dependents(current)
            for dep in dependents:
                if dep not in visited:
                    queue.append((dep, distance + 1))
        
        return sorted(impact, key=lambda x: x[1])
    
    def find_root_cause_candidates(self, failing_service: str) -> List[Dict]:
        """
        Find potential root causes by analyzing the dependency chain.
        
        Args:
            failing_service: The service showing symptoms
        
        Returns:
            List of candidate root causes with reasoning
        """
        candidates = []
        
        # Get all dependencies
        all_deps = self.get_all_dependencies_recursive(failing_service)
        
        # Check required dependencies first (more likely to cause issues)
        required = self.get_dependencies(failing_service, "required")
        for dep in required:
            candidates.append({
                "service": dep,
                "likelihood": "high",
                "reason": f"{dep} is a required dependency of {failing_service}",
                "dependency_type": "required",
                "distance": 1
            })
        
        # Check optional dependencies (might cause degraded performance)
        optional = self.get_dependencies(failing_service, "optional")
        for dep in optional:
            candidates.append({
                "service": dep,
                "likelihood": "medium",
                "reason": f"{dep} is an optional dependency of {failing_service}",
                "dependency_type": "optional",
                "distance": 1
            })
        
        # Check deeper dependencies
        for dep in all_deps:
            if dep not in required and dep not in optional:
                # Calculate distance
                distance = self._calculate_distance(failing_service, dep)
                candidates.append({
                    "service": dep,
                    "likelihood": "low" if distance > 2 else "medium",
                    "reason": f"{dep} is an indirect dependency (distance: {distance})",
                    "dependency_type": "indirect",
                    "distance": distance
                })
        
        return sorted(candidates, key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}[x["likelihood"]],
            x["distance"]
        ))
    
    def _calculate_distance(self, from_service: str, to_service: str) -> int:
        """Calculate shortest path distance between two services."""
        if from_service == to_service:
            return 0
        
        visited = set()
        queue = deque([(from_service, 0)])
        
        while queue:
            current, distance = queue.popleft()
            
            if current in visited:
                continue
            visited.add(current)
            
            deps = self.get_dependencies(current)
            if to_service in deps:
                return distance + 1
            
            for dep in deps:
                if dep not in visited:
                    queue.append((dep, distance + 1))
        
        return float('inf')  # No path found
    
    def analyze_cascading_failure(self, root_service: str) -> Dict:
        """
        Predict cascading failure pattern if root_service fails.
        
        Args:
            root_service: The initial failing service
        
        Returns:
            Analysis of potential cascade
        """
        impact = self.get_impact_radius(root_service)
        
        # Categorize by severity
        critical_impact = []
        high_impact = []
        medium_impact = []
        
        for service, distance in impact:
            # Check if it's a required dependency
            dependents = self.get_dependents(root_service)
            
            if distance == 1:
                # Direct dependent
                deps_info = self.dependencies.get(service, [])
                is_required = any(
                    d["service"] == root_service and d["type"] == "required"
                    for d in deps_info
                )
                
                if is_required:
                    critical_impact.append(service)
                else:
                    high_impact.append(service)
            elif distance == 2:
                high_impact.append(service)
            else:
                medium_impact.append(service)
        
        return {
            "root_cause": root_service,
            "total_affected": len(impact),
            "critical_impact": critical_impact,
            "high_impact": high_impact,
            "medium_impact": medium_impact,
            "blast_radius": max([d for _, d in impact]) if impact else 0,
            "cascade_chain": self._build_cascade_chain(root_service)
        }
    
    def _build_cascade_chain(self, root_service: str) -> List[List[str]]:
        """Build the cascade chain showing failure propagation levels."""
        if self._reverse_deps is None:
            self._build_reverse_deps()
        
        levels = []
        current_level = [root_service]
        visited = set([root_service])
        
        while current_level:
            levels.append(current_level)
            next_level = []
            
            for service in current_level:
                dependents = self.get_dependents(service)
                for dep in dependents:
                    if dep not in visited:
                        next_level.append(dep)
                        visited.add(dep)
            
            current_level = next_level
        
        return levels
    
    def get_critical_path(self, from_service: str, to_service: str) -> List[str]:
        """
        Find the critical path between two services.
        Useful for understanding failure propagation.
        """
        visited = set()
        queue = deque([(from_service, [from_service])])
        
        while queue:
            current, path = queue.popleft()
            
            if current == to_service:
                return path
            
            if current in visited:
                continue
            visited.add(current)
            
            deps = self.get_dependencies(current)
            for dep in deps:
                if dep not in visited:
                    queue.append((dep, path + [dep]))
        
        return []  # No path found
    
    def add_service(self, service: str, dependencies: List[Dict]):
        """Dynamically add a new service to the graph."""
        self.dependencies[service] = dependencies
        self._reverse_deps = None  # Invalidate cache
    
    def remove_service(self, service: str):
        """Remove a service from the graph."""
        if service in self.dependencies:
            del self.dependencies[service]
        self._reverse_deps = None  # Invalidate cache
    
    def update_dependency(self, service: str, dependency: str, 
                         dep_type: str, latency_impact: str):
        """Update or add a specific dependency."""
        if service not in self.dependencies:
            self.dependencies[service] = []
        
        # Remove existing entry if present
        self.dependencies[service] = [
            d for d in self.dependencies[service] 
            if d["service"] != dependency
        ]
        
        # Add updated entry
        self.dependencies[service].append({
            "service": dependency,
            "type": dep_type,
            "latency_impact": latency_impact
        })
        
        self._reverse_deps = None  # Invalidate cache
    
    def visualize_graph(self) -> str:
        """
        Generate a text-based visualization of the dependency graph.
        Returns Mermaid diagram syntax.
        """
        lines = ["graph TD"]
        
        for service, deps in self.dependencies.items():
            for dep in deps:
                dep_service = dep["service"]
                dep_type = dep["type"]
                style = "-->>" if dep_type == "required" else "-->"
                lines.append(f"    {service}{style}{dep_service}")
        
        return "\n".join(lines)


# Global instance
dependency_graph = DependencyGraph()


# Convenience functions
def get_root_cause_candidates(service: str) -> List[Dict]:
    """Get potential root causes for a failing service."""
    return dependency_graph.find_root_cause_candidates(service)


def analyze_impact(service: str) -> Dict:
    """Analyze the impact if a service fails."""
    return dependency_graph.analyze_cascading_failure(service)


def get_dependencies(service: str) -> List[str]:
    """Get all dependencies of a service."""
    return dependency_graph.get_dependencies(service)


def get_dependents(service: str) -> List[str]:
    """Get all services that depend on this service."""
    return dependency_graph.get_dependents(service)