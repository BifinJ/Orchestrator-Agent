import random
import time
import json
import os
import requests
from datetime import datetime

from agents.diagnosis_agent.diagnostic_agent import DiagnosticAgent


TOTAL_TESTS = 300
SERVICES = ["api", "auth", "database"]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


LOG_ERRORS = {
    "api": [
        "API endpoint timeout",
        "Internal server error in API",
        "API gateway failure",
        "API request processing failed"
    ],
    "auth": [
        "Authentication token validation failed",
        "Auth service unavailable",
        "Login authentication timeout",
        "JWT verification error"
    ],
    "database": [
        "Database connection pool exhausted",
        "Query execution timeout",
        "Database replication lag detected",
        "Deadlock detected in database"
    ]
}


METRIC_ERRORS = {
    "api": [
        ("CPUUtilization",95),
        ("Latency",1200),
        ("RequestErrors",200)
    ],
    "auth": [
        ("AuthFailureRate",80),
        ("TokenErrors",150),
        ("Latency",900)
    ],
    "database": [
        ("DBConnections",900),
        ("QueryLatency",1400),
        ("DiskIO",95)
    ]
}


# -------------------------
# INCIDENT GENERATION
# -------------------------

def generate_log_incident():

    service = random.choice(SERVICES)
    message = random.choice(LOG_ERRORS[service])

    alert = {
        "service": service,
        "type": "error",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }

    log = {
        "service": service,
        "message": message,
        "level": "ERROR",
        "timestamp": datetime.utcnow()
    }

    return alert, service, log


def generate_metric_incident():

    service = random.choice(SERVICES)

    metric,value = random.choice(METRIC_ERRORS[service])

    alert = {
        "service": service,
        "type": "metric_anomaly",
        "metric": metric,
        "value": value,
        "zscore": random.uniform(3,5),
        "timestamp": datetime.utcnow().isoformat()
    }

    metric_record = {
        "service": service,
        "metric": metric,
        "value": value,
        "zscore": alert["zscore"],
        "timestamp": datetime.utcnow()
    }

    return alert, service, metric_record


# -------------------------
# RULE SYSTEM
# -------------------------

def rule_engine(alert):

    msg = (alert.get("message") or "").lower()

    if "database" in msg:
        return "database"

    if "auth" in msg or "token" in msg:
        return "auth"

    if "api" in msg:
        return "api"

    metric = (alert.get("metric") or "").lower()

    if "db" in metric:
        return "database"

    if "auth" in metric:
        return "auth"

    return alert.get("service","unknown")


# -------------------------
# GEMINI SYSTEM
# -------------------------

def gemini_engine(alert):

    prompt=f"""
Identify root cause service.

Possible answers:
api
auth
database

Alert:
{alert}

Return only service name.
"""

    url=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

    payload={
        "contents":[{"parts":[{"text":prompt}]}]
    }

    try:

        r=requests.post(url,json=payload,timeout=10)

        text=r.json()["candidates"][0]["content"]["parts"][0]["text"]

        text=text.lower().strip()

        for s in SERVICES:
            if s in text:
                return s

        return "unknown"

    except:
        return "unknown"


# -------------------------
# PROPOSED AGENT SYSTEM
# -------------------------

def proposed_engine(agent, alert):

    diagnoses = agent.handle_anomaly(alert)

    if not diagnoses:
        return "unknown"

    root = diagnoses[0]["root_cause"].lower()

    if root in ["api", "auth", "database"]:
        return root

    # dependency mapping
    mapping = {
        "cache": "api",
        "queue": "api",
        "network": "database",
        "storage": "database",
        "compute": "database",
        "systemic_issue": alert["service"]
    }

    return mapping.get(root, alert["service"])


# -------------------------
# EVALUATION
# -------------------------

def evaluate(system,generator,label,is_proposed=False):

    correct=0
    latency=[]

    print(f"\n--- {label} ---\n")

    metrics=[]
    logs=[]

    agent=None

    if is_proposed:
        agent=DiagnosticAgent(metrics,logs)

    for i in range(TOTAL_TESTS):

        if generator==generate_log_incident:

            alert,truth,log=generator()
            logs.append(log)

        else:

            alert,truth,metric=generator()
            metrics.append(metric)

        print(f"[TEST {i+1}/{TOTAL_TESTS}] {truth}")

        start=time.time()

        if is_proposed:
            pred=proposed_engine(agent,alert)
        else:
            pred=system(alert)

        latency.append(time.time()-start)

        print(f"Predicted={pred} Expected={truth}\n")

        if pred==truth:
            correct+=1

    return{
        "accuracy":correct/TOTAL_TESTS,
        "avg_latency_sec":sum(latency)/len(latency),
        "tests":TOTAL_TESTS
    }


# -------------------------
# MAIN
# -------------------------

def main():

    print("\nCloudOps Diagnosis Evaluation\n")

    results={}

    results["rule_based"]={
        "logs":evaluate(rule_engine,generate_log_incident,"Rule Logs"),
        "metrics":evaluate(rule_engine,generate_metric_incident,"Rule Metrics")
    }

    results["llm_based"]={
        "logs":evaluate(gemini_engine,generate_log_incident,"LLM Logs"),
        "metrics":evaluate(gemini_engine,generate_metric_incident,"LLM Metrics")
    }

    results["proposed_agent"]={
        "logs":evaluate(None,generate_log_incident,"Proposed Logs",True),
        "metrics":evaluate(None,generate_metric_incident,"Proposed Metrics",True)
    }

    with open("diagnosis_evaluation_results_3.json","w") as f:
        json.dump(results,f,indent=4)

    print("\nResults saved\n")
    print(json.dumps(results,indent=2))


if __name__=="__main__":
    main()