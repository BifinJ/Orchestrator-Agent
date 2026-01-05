from data_loader import load_metrics, load_logs
from diagnostic_agent import DiagnosticAgent

from learning.action_store import record_action
from learning.incident_store import record_incident



metrics = load_metrics("metric_history.log")
logs = load_logs("monitor_logs.log")


# anomaly_event = {
#     "service": "api",
#     "timestamp": "2025-12-07T17:21:33.204907Z",
#     "type": "HIGH_CPU"
# }

# anomaly_event = {
#     "service": "api",
#     "timestamp": "2025-12-07T17:22:33.226975Z",
#     "type": "HIGH_LATENCY"
# }

anomaly_event = {
    "service": "db",
    "timestamp": "2025-12-07T17:23:33.269629Z",
    "type": "DB_CONNECTION_EXHAUSTION"
}

agent = DiagnosticAgent(metrics, logs)
diagnosis_results = agent.handle_anomaly(anomaly_event)

print("\n=== DIAGNOSTIC REPORT ===\n")

for idx, result in enumerate(diagnosis_results, 1):
    print(f"{idx}. Root Cause: {result['root_cause']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Evidence: {result['evidence']}")

    print("   Recommended Actions:")
    for action in result.get("recommended_actions", []):
        print(
            f"     - {action['action']} | "
            f"Risk: {action['risk']} | "
            f"Success Rate: {action['success_rate']} | "
            f"Avg Recovery: {action['avg_recovery_time']}"
        )
    print()



print("\n=== REMEDIATION EXECUTION (SIMULATED) ===")

executed_action = {
    "action": "restart_db",
    "success": True,
    "recovery_time_sec": 42
}

print(f"Executed Action: {executed_action['action']}")
print(f"Success: {executed_action['success']}")
print(f"Recovery Time: {executed_action['recovery_time_sec']} seconds")

record_action(
    action=executed_action["action"],
    success=executed_action["success"],
    recovery_time=executed_action["recovery_time_sec"]
)


record_incident(
    anomaly=anomaly_event,
    diagnosis=diagnosis_results,
    resolved_root_cause="DB",
    remediation=executed_action
)

print("\nIncident recorded for learning.")


