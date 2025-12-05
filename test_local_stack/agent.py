import boto3
import time

LOG_GROUP = "/my/app"
LOG_STREAM = "app-stream"

logs = boto3.client(
    "logs",
    region_name="us-east-1",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

def poll_logs():
    next_token = None
    print("Monitoring logs...")

    while True:
        params = {
            "logGroupName": LOG_GROUP,
            "logStreamName": LOG_STREAM,
            "startFromHead": True
        }

        # Only include this if you have a real token
        if next_token:
            params["nextToken"] = next_token

        response = logs.get_log_events(**params)

        for event in response["events"]:
            print("LOG:", event["message"])

        # Update next token for next request
        next_token = response.get("nextForwardToken")

        time.sleep(2)

if __name__ == "__main__":
    poll_logs()
