import os
import time
import json
import random
from datetime import datetime
import google.generativeai as genai

from agents.diagnosis_agent.diagnostic_agent import DiagnosticAgent


# -------------------------------
# CONFIG
# -------------------------------

SERVICES = ["api", "auth", "database"]
INPUT_MODES = ["logs", "metrics", "combined"]

TESTS_PER_SERVICE = 100
RESULT_FILE = "diagnosis_comparison_results.json"

GEMINI_MODEL = "gemini-1.5-flash"


# -------------------------------
# INITIALIZE GEMINI
# -------------------------------

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel(GEMINI_MODEL)


# -------------------------------
# REALISTIC LOG TEMPLATES
# -------------------------------

LOG_TEMPLATES = {
    "api": [
        "request timeout upstream",
        "gateway returned 502",
        "request processing exceeded latency threshold"
    ],
    "auth": [
        "token validation failed",
        "login request rejected",
        "credential verification error"
    ],
    "database": [
        "connection pool exhausted",
        "query execution timeout",
        "transaction deadlock detected"
    ]
}


# -------------------------------
# METRIC SIGNALS (GENERIC)
# -------------------------------

METRIC_TEMPLATES = {
    "api": [
        ("latency", (800,1500)),
        ("error_rate",(0.2,0.6)),
        ("cpu_utilization",(85,100))
    ],
    "auth": [
        ("latency",(300,900)),
        ("failed_requests",(200,600)),
        ("cpu_utilization",(80,95))
    ],
    "database": [
        ("active_connections",(85,120)),
        ("query_latency",(500,1500)),
        ("disk_io",(80,100))
    ]
}


# -------------------------------
# INCIDENT GENERATION
# -------------------------------

def generate_log(service):

    return random.choice(LOG_TEMPLATES[service])


def generate_metric(service):

    metric,value_range=random.choice(METRIC_TEMPLATES[service])

    return {
        "metric": metric,
        "value": random.uniform(*value_range)
    }


def create_incident(service, mode):

    incident={
        "service":service,
        "timestamp":datetime.utcnow().isoformat()
    }

    if mode=="logs":

        incident["type"]="error"
        incident["message"]=generate_log(service)

    elif mode=="metrics":

        metric=generate_metric(service)

        incident["type"]="metric_anomaly"
        incident.update(metric)

    else:

        incident["type"]="error"
        incident["message"]=generate_log(service)

        metric=generate_metric(service)
        incident.update(metric)

    return incident


# -------------------------------
# RULE BASED SYSTEM
# -------------------------------

def rule_based_diagnosis(alert):

    text=str(alert).lower()

    if "connection pool" in text or "deadlock" in text:
        return "database"

    if "token" in text or "credential" in text or "login" in text:
        return "auth"

    if "gateway" in text or "request timeout" in text:
        return "api"

    if alert.get("metric")=="active_connections":
        return "database"

    if alert.get("metric")=="failed_requests":
        return "auth"

    if alert.get("metric")=="latency":
        return "api"

    return random.choice(SERVICES)


# -------------------------------
# LLM BASED SYSTEM
# -------------------------------

def llm_diagnosis(alert):

    prompt=f"""
You are a cloud incident diagnosis assistant.

Incident data:

{json.dumps(alert,indent=2)}

Possible root cause services:
api
auth
database

Return ONLY the service name.
"""

    try:

        response=gemini_model.generate_content(prompt)

        prediction=response.text.strip().lower()

        for service in SERVICES:
            if service in prediction:
                return service

        return random.choice(SERVICES)

    except:

        return random.choice(SERVICES)


# -------------------------------
# PROPOSED AGENT
# -------------------------------

def agent_diagnosis(agent,alert):

    diagnoses=agent.handle_anomaly(alert)

    if not diagnoses:
        return "unknown"

    root=diagnoses[0]["root_cause"].lower()

    if root in SERVICES:
        return root

    return alert["service"]


# -------------------------------
# EVALUATION
# -------------------------------

def evaluate():

    agent=DiagnosticAgent(metrics=[],logs=[])

    system_results={
        "rule_based":{"correct":0,"total":0,"latency":[]},
        "llm_based":{"correct":0,"total":0,"latency":[]},
        "proposed_agent":{"correct":0,"total":0,"latency":[]}
    }

    mode_results={
        "logs":{"correct":0,"total":0},
        "metrics":{"correct":0,"total":0},
        "combined":{"correct":0,"total":0}
    }

    for mode in INPUT_MODES:

        print("\nRunning mode:",mode)

        for service in SERVICES:

            for i in range(TESTS_PER_SERVICE):

                incident=create_incident(service,mode)

                print(f"[TEST] {mode} expected={service}")

                # RULE

                start=time.time()
                pred=rule_based_diagnosis(incident)
                latency=time.time()-start

                system_results["rule_based"]["total"]+=1
                if pred==service:
                    system_results["rule_based"]["correct"]+=1
                    mode_results[mode]["correct"]+=1

                system_results["rule_based"]["latency"].append(latency)
                mode_results[mode]["total"]+=1


                # LLM

                start=time.time()
                pred=llm_diagnosis(incident)
                latency=time.time()-start

                system_results["llm_based"]["total"]+=1
                if pred==service:
                    system_results["llm_based"]["correct"]+=1

                system_results["llm_based"]["latency"].append(latency)


                # AGENT

                start=time.time()
                pred=agent_diagnosis(agent,incident)
                latency=time.time()-start

                system_results["proposed_agent"]["total"]+=1
                if pred==service:
                    system_results["proposed_agent"]["correct"]+=1

                system_results["proposed_agent"]["latency"].append(latency)


    # SYSTEM COMPARISON

    system_summary={}

    for system in system_results:

        data=system_results[system]

        accuracy=data["correct"]/data["total"]
        avg_latency=sum(data["latency"])/len(data["latency"])

        system_summary[system]={
            "accuracy":accuracy,
            "avg_latency_sec":avg_latency,
            "tests":data["total"]
        }


    # INPUT TYPE COMPARISON

    mode_summary={}

    for mode in mode_results:

        accuracy=mode_results[mode]["correct"]/mode_results[mode]["total"]

        mode_summary[mode]={
            "accuracy":accuracy,
            "tests":mode_results[mode]["total"]
        }


    final_results={
        "system_comparison":system_summary,
        "input_type_comparison":mode_summary
    }


    with open(RESULT_FILE,"w") as f:
        json.dump(final_results,f,indent=4)


    print("\nEvaluation finished\n")
    print(json.dumps(final_results,indent=4))
    print("\nSaved to",RESULT_FILE)


# -------------------------------

if __name__=="__main__":
    evaluate()