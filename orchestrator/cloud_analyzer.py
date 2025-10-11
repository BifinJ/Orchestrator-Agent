import boto3
import json

ENDPOINT = "http://localhost:4566"
BUCKET_NAME = "cloud-logs"

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

def _get_all_logs():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="logs/")
    logs = []
    for obj in response.get("Contents", []):
        log_obj = s3.get_object(Bucket=BUCKET_NAME, Key=obj["Key"])
        log_data = json.loads(log_obj["Body"].read().decode("utf-8"))
        logs.append(log_data)
    return logs


def get_average_cpu_usage():
    """Return average CPU usage."""
    logs = _get_all_logs()
    if not logs:
        return "No logs found."
    avg_cpu = sum(l["cpu_usage"] for l in logs) / len(logs)
    return f"Average CPU usage: {avg_cpu:.2f}%"


def get_latest_error():
    """Return the latest error/critical log."""
    logs = _get_all_logs()
    errors = [l for l in logs if l["log_level"] in ["ERROR", "CRITICAL"]]
    if not errors:
        return "No recent errors."
    latest = max(errors, key=lambda x: x["timestamp"])
    return f"Latest error ({latest['log_level']}): {latest['message']} in {latest['service']}"


def get_high_usage_services(threshold=80):
    """Return services exceeding CPU threshold."""
    logs = _get_all_logs()
    high_usage = [l for l in logs if l["cpu_usage"] > threshold]
    if not high_usage:
        return f"No services above {threshold}% CPU usage."
    services = set(l["service"] for l in high_usage)
    return f"High CPU usage detected in: {', '.join(services)}"
