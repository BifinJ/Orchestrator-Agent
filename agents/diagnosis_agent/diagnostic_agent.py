# agents/diagnosis_agent/diagnostic_agent.py

from typing import Dict, List, Optional
from datetime import datetime
from agents.diagnosis_agent.dependency_graph import (
    dependency_graph,
    get_root_cause_candidates,
    analyze_impact
)
from agents.diagnosis_agent.llm_fallback import LLMDiagnosticFallback


class DiagnosticAgent:
    """
    Enhanced diagnostic agent with sophisticated dependency analysis.
    """
    
    def __init__(self, metrics: List[Dict], logs: List[Dict]):
        self.metrics = metrics
        self.logs = logs
        self.recent_alerts = []  # Track recent alerts for correlation
        self.llm_fallback = LLMDiagnosticFallback()  # Initialize LLM fallback
        
    def handle_anomaly(self, alert: Dict) -> List[Dict]:
        """
        Main entry point for anomaly diagnosis.
        
        Args:
            alert: The anomaly alert with service, type, timestamp, etc.
            
        Returns:
            List of diagnosis results with root causes and recommended actions
        """
        service = alert.get("service", "unknown")
        alert_type = alert.get("type")
        timestamp = alert.get("timestamp")
        
        print(f"[DIAG] Analyzing anomaly for service '{service}' at {timestamp}")
        
        # Store alert for correlation analysis
        self.recent_alerts.append(alert)
        self._cleanup_old_alerts()
        
        # Multi-phase diagnosis
        diagnoses = []
        
        # Phase 1: Direct service analysis
        direct_diagnosis = self._analyze_direct_service(alert)
        if direct_diagnosis:
            diagnoses.append(direct_diagnosis)
        
        # Phase 2: Dependency-based root cause analysis
        dependency_diagnoses = self._analyze_dependencies(alert)
        diagnoses.extend(dependency_diagnoses)
        
        # Phase 3: Cascading failure detection
        cascade_diagnosis = self._detect_cascading_failures(alert)
        if cascade_diagnosis:
            diagnoses.append(cascade_diagnosis)
        
        # Phase 4: Correlation analysis with recent alerts
        correlated_diagnosis = self._correlate_with_recent_alerts(alert)
        if correlated_diagnosis:
            diagnoses.append(correlated_diagnosis)
        
        # Sort by confidence
        diagnoses = sorted(diagnoses, key=lambda d: d.get("confidence", 0), reverse=True)
        
        # LLM FALLBACK: Use LLM if diagnoses are insufficient
        if self.llm_fallback.should_use_llm(diagnoses, alert):
            print("[DIAG] Rule-based diagnosis insufficient, consulting LLM...")
            
            llm_diagnosis = self.llm_fallback.diagnose_with_llm(
                alert=alert,
                existing_diagnoses=diagnoses,
                recent_alerts=self.recent_alerts[-10:],
                metrics=self._get_recent_metrics(alert.get("service")),
                logs=self._get_recent_logs(alert.get("service"))
            )
            
            if llm_diagnosis:
                # Add LLM diagnosis to the list
                diagnoses.insert(0, llm_diagnosis)  # Add at the top
                print(f"[DIAG] LLM diagnosis: {llm_diagnosis['root_cause']} "
                      f"(confidence: {llm_diagnosis['confidence']:.2f})")
        
        return diagnoses
    
    def _analyze_direct_service(self, alert: Dict) -> Optional[Dict]:
        """
        Analyze the service itself for issues.
        """
        service = alert.get("service")
        alert_type = alert.get("type")
        
        # Check metrics for this service
        service_metrics = self._get_recent_metrics(service)
        
        # Build diagnosis based on alert type
        if alert_type == "metric_anomaly":
            metric_name = alert.get("metric")
            zscore = alert.get("zscore", 0)
            
            return {
                "root_cause": service,
                "category": "service_degradation",
                "confidence": 0.7,
                "evidence": [
                    f"{metric_name} anomaly detected (z-score: {zscore:.2f})",
                    f"Direct issue with {service} service"
                ],
                "recommended_actions": self._get_actions_for_service(service, alert_type),
                "impact_analysis": analyze_impact(service)
            }
        
        elif alert_type in ["error", "critical"]:
            return {
                "root_cause": service,
                "category": "application_error",
                "confidence": 0.8,
                "evidence": [
                    f"{alert_type.upper()} detected in {service}",
                    f"Message: {alert.get('message', 'N/A')}"
                ],
                "recommended_actions": self._get_actions_for_service(service, alert_type),
                "impact_analysis": analyze_impact(service)
            }
        
        return None
    
    def _analyze_dependencies(self, alert: Dict) -> List[Dict]:
        """
        Analyze dependency chain to find potential root causes.
        """
        service = alert.get("service")
        diagnoses = []
        
        # Get all potential root cause candidates
        candidates = get_root_cause_candidates(service)
        
        for candidate in candidates[:5]:  # Top 5 candidates
            dep_service = candidate["service"]
            likelihood = candidate["likelihood"]
            reason = candidate["reason"]
            distance = candidate["distance"]
            
            # Check if this dependency has recent issues
            dep_issues = self._check_service_health(dep_service)
            
            if dep_issues:
                confidence = {
                    "high": 0.85,
                    "medium": 0.65,
                    "low": 0.45
                }.get(likelihood, 0.5)
                
                # Boost confidence if we have evidence
                confidence += len(dep_issues) * 0.05
                confidence = min(confidence, 0.95)
                
                diagnoses.append({
                    "root_cause": dep_service,
                    "category": "dependency_failure",
                    "confidence": confidence,
                    "evidence": [
                        reason,
                        f"Distance in dependency chain: {distance}",
                        *[f"Issue detected: {issue}" for issue in dep_issues]
                    ],
                    "recommended_actions": self._get_actions_for_dependency(
                        service, dep_service, candidate["dependency_type"]
                    ),
                    "impact_analysis": analyze_impact(dep_service)
                })
        
        return diagnoses
    
    def _detect_cascading_failures(self, alert: Dict) -> Optional[Dict]:
        """
        Detect if this is part of a cascading failure pattern.
        """
        service = alert.get("service")
        
        # Check if multiple services in the dependency chain are failing
        all_deps = dependency_graph.get_all_dependencies_recursive(service)
        
        failing_deps = []
        for dep in all_deps:
            if self._has_recent_alert(dep):
                failing_deps.append(dep)
        
        if len(failing_deps) >= 2:
            # Multiple dependencies failing = likely cascade
            
            # Find the deepest failing service (likely root cause)
            deepest = self._find_deepest_service(failing_deps)
            
            cascade_analysis = analyze_impact(deepest)
            
            return {
                "root_cause": deepest,
                "category": "cascading_failure",
                "confidence": 0.9,
                "evidence": [
                    f"Multiple services failing: {', '.join(failing_deps)}",
                    f"Cascade originated from {deepest}",
                    f"Blast radius: {cascade_analysis['blast_radius']} levels",
                    f"Total affected services: {cascade_analysis['total_affected']}"
                ],
                "recommended_actions": [
                    {
                        "action": f"isolate_{deepest}",
                        "risk": "medium",
                        "description": f"Isolate {deepest} to prevent further cascade"
                    },
                    {
                        "action": f"restart_{deepest}",
                        "risk": "low",
                        "description": f"Restart {deepest} service"
                    }
                ],
                "cascade_chain": cascade_analysis["cascade_chain"],
                "impact_analysis": cascade_analysis
            }
        
        return None
    
    def _correlate_with_recent_alerts(self, alert: Dict) -> Optional[Dict]:
        """
        Check if this alert correlates with other recent alerts.
        """
        service = alert.get("service")
        timestamp = alert.get("timestamp")
        
        # Find alerts from related services within last 5 minutes
        related_alerts = []
        
        # Get all services related to this one
        dependencies = dependency_graph.get_all_dependencies_recursive(service)
        dependents = dependency_graph.get_dependents(service)
        related_services = set(dependencies + dependents)
        
        for recent_alert in self.recent_alerts[-20:]:  # Last 20 alerts
            if recent_alert == alert:
                continue
            
            recent_service = recent_alert.get("service")
            if recent_service in related_services:
                related_alerts.append(recent_alert)
        
        if len(related_alerts) >= 2:
            # Pattern detected
            affected_services = [a.get("service") for a in related_alerts]
            
            return {
                "root_cause": "systemic_issue",
                "category": "correlated_failure",
                "confidence": 0.75,
                "evidence": [
                    f"Correlated alerts detected across: {', '.join(set(affected_services))}",
                    f"Total correlated alerts: {len(related_alerts)}",
                    "Pattern suggests systemic issue"
                ],
                "recommended_actions": [
                    {
                        "action": "investigate_infrastructure",
                        "risk": "low",
                        "description": "Check underlying infrastructure (network, compute)"
                    },
                    {
                        "action": "check_resource_limits",
                        "risk": "low",
                        "description": "Verify resource limits and quotas"
                    }
                ],
                "correlated_alerts": related_alerts
            }
        
        return None
    
    def _get_recent_metrics(self, service: str, minutes: int = 10) -> List[Dict]:
        """Get recent metrics for a service."""
        # Filter metrics by service (you'd implement actual filtering logic)
        return [m for m in self.metrics[-100:] if m.get("service") == service]
    
    def _check_service_health(self, service: str) -> List[str]:
        """
        Check if a service has any recent health issues.
        Returns list of issue descriptions.
        """
        issues = []
        
        # Check for recent alerts
        for alert in self.recent_alerts[-10:]:
            if alert.get("service") == service:
                issues.append(f"{alert.get('type')} at {alert.get('timestamp')}")
        
        # Check metrics for anomalies
        recent_metrics = self._get_recent_metrics(service, minutes=5)
        for metric in recent_metrics:
            if metric.get("zscore") and abs(metric.get("zscore", 0)) > 2:
                issues.append(f"Metric anomaly: {metric.get('metric')}")
        
        return issues
    
    def _has_recent_alert(self, service: str, minutes: int = 5) -> bool:
        """Check if service has recent alerts."""
        return any(
            alert.get("service") == service 
            for alert in self.recent_alerts[-10:]
        )
    
    def _find_deepest_service(self, services: List[str]) -> str:
        """
        Find the service deepest in dependency tree (most fundamental).
        This is likely the root cause in a cascade.
        """
        max_dependents = 0
        deepest = services[0] if services else "unknown"
        
        for service in services:
            # Count how many services depend on this one
            dependents = dependency_graph.get_dependents(service)
            if len(dependents) > max_dependents:
                max_dependents = len(dependents)
                deepest = service
        
        return deepest
    
    def _get_actions_for_service(self, service: str, alert_type: str) -> List[Dict]:
        """Generate remediation actions based on service and alert type."""
        actions = []
        
        # Service-specific actions
        if service in ["api", "application"]:
            actions.extend([
                {
                    "action": f"restart_{service}",
                    "risk": "low",
                    "description": f"Restart {service} service"
                },
                {
                    "action": f"scale_{service}",
                    "risk": "low",
                    "description": f"Scale up {service} instances"
                }
            ])
        
        elif service == "database":
            actions.extend([
                {
                    "action": "restart_db",
                    "risk": "medium",
                    "description": "Restart database connection pool"
                },
                {
                    "action": "optimize_db_queries",
                    "risk": "low",
                    "description": "Analyze and optimize slow queries"
                }
            ])
        
        elif service == "cache":
            actions.extend([
                {
                    "action": "clear_cache",
                    "risk": "low",
                    "description": "Clear cache and rebuild"
                },
                {
                    "action": "restart_cache",
                    "risk": "low",
                    "description": "Restart cache service"
                }
            ])
        
        # Alert-type specific actions
        if alert_type == "metric_anomaly":
            actions.append({
                "action": "check_resource_usage",
                "risk": "low",
                "description": "Check CPU, memory, and disk usage"
            })
        
        return actions if actions else [{
            "action": f"investigate_{service}",
            "risk": "low",
            "description": f"Manual investigation of {service} required"
        }]
    
    def _get_actions_for_dependency(self, service: str, 
                                   dependency: str, 
                                   dep_type: str) -> List[Dict]:
        """Generate actions when issue is with a dependency."""
        actions = [
            {
                "action": f"check_{dependency}",
                "risk": "low",
                "description": f"Investigate {dependency} service health"
            }
        ]
        
        if dep_type == "required":
            actions.append({
                "action": f"restart_{dependency}",
                "risk": "medium",
                "description": f"Restart {dependency} (required by {service})"
            })
        else:
            actions.append({
                "action": f"disable_{dependency}_temporarily",
                "risk": "low",
                "description": f"Temporarily disable optional {dependency} dependency"
            })
        
        return actions
    
    def _get_recent_logs(self, service: str, minutes: int = 10) -> List[Dict]:
        """Get recent logs for a service."""
        # Filter logs by service
        return [log for log in self.logs[-50:] if log.get("service") == service]
    
    def _cleanup_old_alerts(self, max_age_minutes: int = 30):
        """Remove alerts older than max_age_minutes."""
        if len(self.recent_alerts) > 100:
            self.recent_alerts = self.recent_alerts[-50:]  # Keep last 50