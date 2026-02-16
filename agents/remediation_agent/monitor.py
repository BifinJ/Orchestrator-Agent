# agents/remediation_agent/monitor.py
# Post-remediation health check.
# Reads from the same storage files the monitoring agent writes to
# (storage/log_alerts.json, storage/metric_alerts.json) and checks
# whether new alerts appeared for this service after remediation ran.

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

LOG_ALERTS_PATH    = "storage/log_alerts.json"
METRIC_ALERTS_PATH = "storage/metric_alerts.json"
APPROVAL_FILE      = "storage/approval.json"
MONITOR_LOG        = Path("storage/monitor.log")

# How long to wait for new alerts before declaring recovery
CHECK_WINDOW_SECONDS = 30


def monitor_post_remediation(service: str):
    """
    Checks log_alerts.json and metric_alerts.json for new alerts
    that appeared after remediation ran for this service.
    Escalates to human via approval file if the service still looks bad.
    """
    remediated_at = datetime.now(timezone.utc)

    # Give the monitoring agent a moment to write any immediate new alerts
    import time
    time.sleep(CHECK_WINDOW_SECONDS)

    new_log_alerts    = _get_new_alerts(LOG_ALERTS_PATH,    service, remediated_at)
    new_metric_alerts = _get_new_alerts(METRIC_ALERTS_PATH, service, remediated_at)

    recovered = len(new_log_alerts) == 0 and len(new_metric_alerts) == 0

    _write_monitor_log(service, remediated_at, new_log_alerts, new_metric_alerts, recovered)

    if recovered:
        print(f"[MONITOR] Service '{service}' recovered — no new alerts after remediation.")
    else:
        print(f"[MONITOR] Service '{service}' still alerting — escalating to human.")
        _escalate(service, new_log_alerts, new_metric_alerts)


def _get_new_alerts(path: str, service: str, since: datetime) -> list:
    """
    Read an alert file and return alerts for this service
    that appeared after the given timestamp.
    """
    if not Path(path).exists():
        return []

    try:
        with open(path) as f:
            alerts = json.load(f)
    except Exception:
        return []

    new = []
    for alert in alerts:
        alert_ts = _parse_ts(alert.get("timestamp"))
        alert_service = alert.get("service", "")

        if alert_ts and alert_ts > since:
            # Match if service name is contained in either direction
            if service in alert_service or alert_service in service:
                new.append(alert)

    return new


def _parse_ts(ts_str) -> datetime | None:
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _write_monitor_log(service: str, remediated_at: datetime,
                       new_log_alerts: list, new_metric_alerts: list,
                       recovered: bool):
    os.makedirs(MONITOR_LOG.parent, exist_ok=True)
    entry = {
        "timestamp":        datetime.utcnow().isoformat() + "Z",
        "service":          service,
        "remediated_at":    remediated_at.isoformat(),
        "new_log_alerts":   len(new_log_alerts),
        "new_metric_alerts": len(new_metric_alerts),
        "recovered":        recovered,
    }
    with open(MONITOR_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _escalate(service: str, new_log_alerts: list, new_metric_alerts: list):
    os.makedirs("storage", exist_ok=True)

    sample_alerts = (new_log_alerts + new_metric_alerts)[:3]  # show up to 3 examples

    with open(APPROVAL_FILE, "w") as f:
        json.dump({
            "incident_id":   None,
            "service":       service,
            "action":        "manual_investigation_required",
            "risk":          "high",
            "confidence":    None,
            "score":         None,
            "justification": (
                f"Post-remediation check failed for '{service}'. "
                f"New log alerts: {len(new_log_alerts)}, "
                f"new metric alerts: {len(new_metric_alerts)}. "
                f"Sample: {json.dumps(sample_alerts)}"
            ),
            "approved": None,
        }, f, indent=2)