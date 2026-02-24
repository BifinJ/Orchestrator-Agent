import re
from collections import defaultdict
from typing import Dict, Optional, List


class ServiceDetector:

    LOG_PATTERNS = {
        "api": [
            r"\bGET\b", r"\bPOST\b", r"\bPUT\b", r"\bDELETE\b",
            r"HTTP/\d\.\d",
            r"\b\d{3}\b\s+\d+ms",
            r"User-Agent",
            r"Random", r"System", r"failure", r"Simulated"
        ],
        "database": [
            r"\bmysql\b", r"\bpostgres\b", r"\bconnection\b",
            r"\bquery\b", r"\btransaction\b",
            r"\bdeadlock\b", r"\btimeout\b",
            r"\bSELECT\b", r"\bINSERT\b", r"\bUPDATE\b",
        ],
        "cache": [
            r"\bredis\b", r"\bmemcached\b",
            r"\bcache hit\b", r"\bcache miss\b",
        ],
        "queue": [
            r"\bsqs\b", r"\bkafka\b",
            r"\brabbitmq\b", r"\bconsumer\b", r"\bproducer\b",
        ],
        "worker": [
            r"\bcelery\b", r"\bbackground job\b",
            r"\btask\b.*\b(started|failed|completed)\b",
        ]
    }

    NAMESPACE_TO_SERVICE = {
        "AWS/EC2": "compute",
        "AWS/RDS": "database",
        "AWS/ElastiCache": "cache",
        "AWS/SQS": "queue",
        "AWS/Lambda": "lambda",
        "AWS/ApplicationELB": "load_balancer",
        "AWS/ELB": "load_balancer",
    }

    METRIC_PATTERNS = {
        "compute": ["CPUUtilization", "StatusCheck", "NetworkIn", "NetworkOut"],
        "database": ["DatabaseConnections", "ReadLatency", "WriteLatency"],
        "cache": ["CacheHits", "CacheMisses", "Evictions"],
        "queue": ["NumberOfMessages", "ApproximateAgeOfOldestMessage"],
        "load_balancer": ["RequestCount", "TargetResponseTime", "HTTPCode"],
    }

    @classmethod
    def detect_from_log(cls, message: str) -> Dict:
        scores = defaultdict(int)

        if not message:
            return {"service": "unknown", "confidence": 0.0}

        for service, patterns in cls.LOG_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    scores[service] += 1

        if not scores:
            return {"service": "unknown", "confidence": 0.0}

        best = max(scores, key=scores.get)
        confidence = scores[best] / sum(scores.values())

        return {"service": best, "confidence": round(confidence, 2)}

    @classmethod
    def detect_from_metric(cls, metric_name: str, namespace: str) -> Dict:
        scores = defaultdict(int)

        # namespace priority weight
        if namespace in cls.NAMESPACE_TO_SERVICE:
            base = cls.NAMESPACE_TO_SERVICE[namespace]
            scores[base] += 2

        for service, metrics in cls.METRIC_PATTERNS.items():
            for keyword in metrics:
                if keyword in metric_name:
                    scores[service] += 1

        if not scores:
            return {"service": "unknown", "confidence": 0.0}

        best = max(scores, key=scores.get)
        confidence = scores[best] / sum(scores.values())

        return {"service": best, "confidence": round(confidence, 2)}

    @classmethod
    def detect_from_dimensions(cls, dimensions: List[Dict]) -> Optional[str]:
        for dim in dimensions:
            name = dim.get("Name", "")
            if name == "DBInstanceIdentifier":
                return "database"
            if name == "LoadBalancer":
                return "load_balancer"
            if name == "TargetGroup":
                return "api"
            if name == "FunctionName":
                return "lambda"
        return None

    @classmethod
    def detect_service(
        cls,
        message: str = None,
        metric_name: str = None,
        namespace: str = None,
        dimensions: list = None
    ) -> str:

        # 1️⃣ Dimensions highest priority
        if dimensions:
            svc = cls.detect_from_dimensions(dimensions)
            if svc:
                return svc

        # 2️⃣ Metric-based detection
        if metric_name and namespace:
            result = cls.detect_from_metric(metric_name, namespace)
            return result["service"]

        # 3️⃣ Log-based detection
        if message:
            result = cls.detect_from_log(message)
            return result["service"]

        return "unknown"
