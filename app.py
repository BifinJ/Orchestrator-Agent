from flask import Flask, request
import boto3
import logging
import time
import random
import os
from datetime import datetime, timezone

app = Flask(__name__)

LOG_GROUP = "flask-log-group"
LOG_STREAM = "flask-stream"

client = boto3.client(
    "logs",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
    endpoint_url="http://localstack:4566"
)

os.makedirs("logs", exist_ok=True)

# ----------- Setup CloudWatch log group/stream -----------
def setup_cloudwatch():
    try:
        client.create_log_group(logGroupName=LOG_GROUP)
    except:
        pass
    try:
        client.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
    except:
        pass

setup_cloudwatch()

sequence_token = None

def push_to_cloudwatch(message):
    global sequence_token
    timestamp = int(time.time() * 1000)

    args = {
        "logGroupName": LOG_GROUP,
        "logStreamName": LOG_STREAM,
        "logEvents": [
            {"timestamp": timestamp, "message": message}
        ]
    }

    if sequence_token:
        args["sequenceToken"] = sequence_token

    response = client.put_log_events(**args)
    sequence_token = response.get("nextSequenceToken")

# ----------- LOGGING HOOK -----------
def log_message(level, msg):
    timestamp = datetime.now(timezone.utc).isoformat()

    formatted = f"{timestamp} [{level}] {msg}"

    with open("logs/app.log", "a") as f:
        f.write(formatted + "\n")

    push_to_cloudwatch(formatted)

# ----------- API ROUTES -----------
@app.route("/")
def home():
    log_message("INFO", "Home endpoint hit")
    return {"msg": "Flask running"}

@app.route("/random-fail")
def random_fail():
    if random.random() < 0.5:
        log_message("ERROR", "Random failure occurred")
        return {"error": "Random failure"}, 500
    log_message("INFO", "Random endpoint success")
    return {"msg": "Success"}

@app.route("/db-error")
def db_error():
    log_message("ERROR", "Database timeout")
    return {"error": "DB connection timeout"}, 500

@app.route("/slow")
def slow():
    log_message("WARNING", "Slow endpoint triggered")
    time.sleep(6)
    return {"msg": "Slow response returned"}

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if data.get("username") != "admin" or data.get("password") != "1234":
        log_message("ERROR", f"Invalid login attempt: {data.get('username')}")
        return {"msg": "Invalid"}, 401
    log_message("INFO", "Login successful")
    return {"msg": "Success"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
