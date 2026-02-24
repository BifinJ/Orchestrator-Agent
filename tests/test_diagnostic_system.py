# tests/test_diagnostic_system.py

"""
Comprehensive diagnostic system test suite with 200 test cases.
Generates detailed accuracy, latency, and performance reports.
"""

import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

from agents.diagnosis_agent.diagnostic_agent import DiagnosticAgent
from agents.diagnosis_agent.llm_fallback import LLMDiagnosticFallback
from agents.monitoring_agent.error_classifier import classify_error


class DiagnosticTestSuite:
    """
    Comprehensive test suite for the diagnostic system.
    Tests 20 different diagnosis scenarios with 200 total cases.
    """
    
    def __init__(self):
        self.test_cases = []
        self.results = []
        self.metrics = defaultdict(list)
        
        # Initialize diagnostic agent
        self.agent = DiagnosticAgent(metrics=[], logs=[])
        
        # Generate all test cases
        self._generate_test_cases()
    
    def _generate_test_cases(self):
        """Generate 200 test cases across 20 different categories."""
        
        # Category 1: Database Connection Issues (15 cases)
        self.test_cases.extend(self._generate_database_connection_tests())
        
        # Category 2: Cache Failures (15 cases)
        self.test_cases.extend(self._generate_cache_failure_tests())
        
        # Category 3: Network Timeouts (15 cases)
        self.test_cases.extend(self._generate_network_timeout_tests())
        
        # Category 4: Authentication Errors (10 cases)
        self.test_cases.extend(self._generate_auth_error_tests())
        
        # Category 5: Resource Exhaustion (10 cases)
        self.test_cases.extend(self._generate_resource_exhaustion_tests())
        
        # Category 6: API Rate Limiting (10 cases)
        self.test_cases.extend(self._generate_rate_limit_tests())
        
        # Category 7: Disk Space Issues (10 cases)
        self.test_cases.extend(self._generate_disk_space_tests())
        
        # Category 8: Memory Leaks (10 cases)
        self.test_cases.extend(self._generate_memory_leak_tests())
        
        # Category 9: Cascading Failures (10 cases)
        self.test_cases.extend(self._generate_cascading_failure_tests())
        
        # Category 10: Configuration Errors (10 cases)
        self.test_cases.extend(self._generate_config_error_tests())
        
        # Category 11: Load Balancer Issues (10 cases)
        self.test_cases.extend(self._generate_load_balancer_tests())
        
        # Category 12: DNS Resolution Failures (10 cases)
        self.test_cases.extend(self._generate_dns_failure_tests())
        
        # Category 13: SSL/TLS Certificate Issues (8 cases)
        self.test_cases.extend(self._generate_ssl_certificate_tests())
        
        # Category 14: Queue Backlog (8 cases)
        self.test_cases.extend(self._generate_queue_backlog_tests())
        
        # Category 15: Deadlock Detection (8 cases)
        self.test_cases.extend(self._generate_deadlock_tests())
        
        # Category 16: Third-Party API Failures (8 cases)
        self.test_cases.extend(self._generate_third_party_api_tests())
        
        # Category 17: Intermittent Errors (8 cases)
        self.test_cases.extend(self._generate_intermittent_error_tests())
        
        # Category 18: Correlated Service Failures (7 cases)
        self.test_cases.extend(self._generate_correlated_failure_tests())
        
        # Category 19: Performance Degradation (7 cases)
        self.test_cases.extend(self._generate_performance_degradation_tests())
        
        # Category 20: Unknown/Novel Issues (6 cases)
        self.test_cases.extend(self._generate_novel_issue_tests())
    
    # ========================================================================
    # TEST CASE GENERATORS
    # ========================================================================
    
    def _generate_database_connection_tests(self) -> List[Dict]:
        """Generate database connection test cases."""
        return [
            {
                "id": "DB_001",
                "category": "database_connection",
                "alert": {
                    "type": "error",
                    "service": "api",
                    "message": "Database connection timeout after 5000ms",
                    "timestamp": "2026-02-16T10:00:00Z"
                },
                "expected_root_cause": "database",
                "expected_category": "service_degradation",
                "min_confidence": 0.7
            },
            {
                "id": "DB_002",
                "category": "database_connection",
                "alert": {
                    "type": "error",
                    "service": "api",
                    "message": "MySQL connection pool exhausted (100/100)",
                    "timestamp": "2026-02-16T10:01:00Z"
                },
                "expected_root_cause": "database",
                "expected_category": "resource_exhaustion",
                "min_confidence": 0.8
            },
            {
                "id": "DB_003",
                "category": "database_connection",
                "alert": {
                    "type": "error",
                    "service": "worker",
                    "message": "psycopg2.OperationalError: could not connect to server",
                    "timestamp": "2026-02-16T10:02:00Z"
                },
                "expected_root_cause": "database",
                "expected_category": "service_degradation",
                "min_confidence": 0.7
            },
            {
                "id": "DB_004",
                "category": "database_connection",
                "alert": {
                    "type": "error",
                    "service": "api",
                    "message": "Lost connection to MySQL server during query",
                    "timestamp": "2026-02-16T10:03:00Z"
                },
                "expected_root_cause": "database",
                "expected_category": "service_degradation",
                "min_confidence": 0.75
            },
            {
                "id": "DB_005",
                "category": "database_connection",
                "alert": {
                    "type": "error",
                    "service": "api",
                    "message": "Database query timeout after 30 seconds",
                    "timestamp": "2026-02-16T10:04:00Z"
                },
                "expected_root_cause": "database",
                "expected_category": "service_degradation",
                "min_confidence": 0.7
            },
            # Add 10 more variations
            *[{
                "id": f"DB_{str(i).zfill(3)}",
                "category": "database_connection",
                "alert": {
                    "type": "error",
                    "service": ["api", "worker", "auth"][i % 3],
                    "message": [
                        "Database deadlock detected",
                        "Too many connections to database",
                        "Database connection refused",
                        "Connection reset by database peer",
                        "Database authentication failed",
                        "Lock wait timeout exceeded",
                        "Database replication lag detected",
                        "Slow query detected: 45 seconds",
                        "Database disk I/O error",
                        "Database connection pool timeout"
                    ][i % 10],
                    "timestamp": f"2026-02-16T10:{str(5+i).zfill(2)}:00Z"
                },
                "expected_root_cause": "database",
                "expected_category": ["service_degradation", "resource_exhaustion"][i % 2],
                "min_confidence": 0.65
            } for i in range(10)]
        ]
    
    def _generate_cache_failure_tests(self) -> List[Dict]:
        """Generate cache failure test cases."""
        messages = [
            "Redis connection timeout",
            "Cache connection refused",
            "Memcached error: Connection reset",
            "Redis master down",
            "Cache eviction rate critical",
            "Redis out of memory",
            "Cache cluster unavailable",
            "Redis replica lag detected",
            "Cache miss rate > 90%",
            "Redis connection pool exhausted",
            "Cache write failure",
            "Redis sentinel failure",
            "Cache corruption detected",
            "Redis AOF write error",
            "Cache replication failed"
        ]
        
        return [{
            "id": f"CACHE_{str(i+1).zfill(3)}",
            "category": "cache_failure",
            "alert": {
                "type": "error",
                "service": ["api", "worker"][i % 2],
                "message": messages[i],
                "timestamp": f"2026-02-16T11:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "cache",
            "expected_category": "service_degradation",
            "min_confidence": 0.7
        } for i in range(15)]
    
    def _generate_network_timeout_tests(self) -> List[Dict]:
        """Generate network timeout test cases."""
        messages = [
            "Connection timed out after 30s",
            "Network unreachable",
            "No route to host",
            "Connection refused by remote host",
            "Socket timeout exception",
            "DNS resolution failed",
            "Network packet loss detected",
            "TCP handshake timeout",
            "Connection reset by peer",
            "Network latency > 5000ms",
            "Port unreachable",
            "Network interface down",
            "Firewall blocking connection",
            "VPC peering connection failed",
            "Network congestion detected"
        ]
        
        return [{
            "id": f"NET_{str(i+1).zfill(3)}",
            "category": "network_timeout",
            "alert": {
                "type": "error",
                "service": ["api", "worker", "lambda"][i % 3],
                "message": messages[i],
                "timestamp": f"2026-02-16T12:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "network",
            "expected_category": "service_degradation",
            "min_confidence": 0.65
        } for i in range(15)]
    
    def _generate_auth_error_tests(self) -> List[Dict]:
        """Generate authentication error test cases."""
        messages = [
            "Authentication failed for user",
            "JWT token expired",
            "Invalid API credentials",
            "OAuth token validation failed",
            "Session expired",
            "Access token invalid",
            "Permission denied",
            "User account locked",
            "Two-factor authentication failed",
            "API key revoked"
        ]
        
        return [{
            "id": f"AUTH_{str(i+1).zfill(3)}",
            "category": "auth_error",
            "alert": {
                "type": "error",
                "service": ["api", "auth"][i % 2],
                "message": messages[i],
                "timestamp": f"2026-02-16T13:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "auth",
            "expected_category": "application_error",
            "min_confidence": 0.75
        } for i in range(10)]
    
    def _generate_resource_exhaustion_tests(self) -> List[Dict]:
        """Generate resource exhaustion test cases."""
        messages = [
            "Out of memory: heap space",
            "CPU usage at 100% for 5 minutes",
            "Thread pool exhausted",
            "File descriptor limit reached",
            "Swap space full",
            "Process count limit exceeded",
            "Memory allocation failed",
            "CPU throttling detected",
            "Semaphore limit reached",
            "Socket limit exceeded"
        ]
        
        return [{
            "id": f"RES_{str(i+1).zfill(3)}",
            "category": "resource_exhaustion",
            "alert": {
                "type": "critical",
                "service": ["compute", "api"][i % 2],
                "message": messages[i],
                "timestamp": f"2026-02-16T14:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "compute",
            "expected_category": "resource_exhaustion",
            "min_confidence": 0.7
        } for i in range(10)]
    
    def _generate_rate_limit_tests(self) -> List[Dict]:
        """Generate rate limiting test cases."""
        messages = [
            "Rate limit exceeded: 1000 req/min",
            "API quota exhausted",
            "Too many requests from IP",
            "Throttling active: 429 errors",
            "Request backoff required",
            "Burst limit exceeded",
            "Daily API limit reached",
            "Concurrent request limit hit",
            "Rate limiter circuit open",
            "Token bucket depleted"
        ]
        
        return [{
            "id": f"RATE_{str(i+1).zfill(3)}",
            "category": "rate_limiting",
            "alert": {
                "type": "warning",
                "service": "api",
                "message": messages[i],
                "timestamp": f"2026-02-16T15:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "api",
            "expected_category": "application_error",
            "min_confidence": 0.65
        } for i in range(10)]
    
    def _generate_disk_space_tests(self) -> List[Dict]:
        """Generate disk space issue test cases."""
        messages = [
            "Disk space critically low: 98% used",
            "No space left on device",
            "Disk I/O error",
            "Write failed: disk full",
            "Log partition at capacity",
            "Inode limit reached",
            "Disk quota exceeded",
            "Filesystem read-only",
            "Volume mount failed",
            "Disk health check failed"
        ]
        
        return [{
            "id": f"DISK_{str(i+1).zfill(3)}",
            "category": "disk_space",
            "alert": {
                "type": "critical",
                "service": "storage",
                "message": messages[i],
                "timestamp": f"2026-02-16T16:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "storage",
            "expected_category": "resource_exhaustion",
            "min_confidence": 0.8
        } for i in range(10)]
    
    def _generate_memory_leak_tests(self) -> List[Dict]:
        """Generate memory leak test cases."""
        messages = [
            "Memory usage increasing steadily",
            "Heap dump shows memory leak",
            "GC running continuously",
            "Memory not being released",
            "Process memory > 4GB",
            "Old generation heap full",
            "Native memory leak detected",
            "Memory fragmentation critical",
            "Retained heap growing",
            "Memory pressure warning"
        ]
        
        return [{
            "id": f"MEM_{str(i+1).zfill(3)}",
            "category": "memory_leak",
            "alert": {
                "type": "warning",
                "service": ["api", "worker"][i % 2],
                "message": messages[i],
                "timestamp": f"2026-02-16T17:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "application",
            "expected_category": "resource_exhaustion",
            "min_confidence": 0.6
        } for i in range(10)]
    
    def _generate_cascading_failure_tests(self) -> List[Dict]:
        """Generate cascading failure test cases."""
        return [{
            "id": f"CASCADE_{str(i+1).zfill(3)}",
            "category": "cascading_failure",
            "alert": {
                "type": "critical",
                "service": ["api", "database", "cache", "auth"][i % 4],
                "message": f"Multiple service failures detected in chain",
                "timestamp": f"2026-02-16T18:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": ["storage", "network", "database"][i % 3],
            "expected_category": "cascading_failure",
            "min_confidence": 0.7,
            "context": {
                "recent_alerts": [
                    {"service": "storage", "type": "error"},
                    {"service": "database", "type": "error"},
                    {"service": "api", "type": "error"}
                ]
            }
        } for i in range(10)]
    
    def _generate_config_error_tests(self) -> List[Dict]:
        """Generate configuration error test cases."""
        messages = [
            "Invalid configuration parameter",
            "Missing required environment variable",
            "Configuration file not found",
            "Port already in use",
            "Invalid database URL",
            "Misconfigured timeout value",
            "SSL certificate path invalid",
            "Invalid connection string",
            "Configuration schema validation failed",
            "Incompatible configuration version"
        ]
        
        return [{
            "id": f"CONFIG_{str(i+1).zfill(3)}",
            "category": "config_error",
            "alert": {
                "type": "error",
                "service": ["api", "worker", "database"][i % 3],
                "message": messages[i],
                "timestamp": f"2026-02-16T19:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "application",
            "expected_category": "configuration_error",
            "min_confidence": 0.65
        } for i in range(10)]
    
    def _generate_load_balancer_tests(self) -> List[Dict]:
        """Generate load balancer test cases."""
        messages = [
            "All backend targets unhealthy",
            "Load balancer connection timeout",
            "Target group empty",
            "Health check failing",
            "Load balancer 502 Bad Gateway",
            "Sticky session failure",
            "Backend connection refused",
            "Load balancer capacity exceeded",
            "Target deregistration failed",
            "Load balancer SSL negotiation failed"
        ]
        
        return [{
            "id": f"LB_{str(i+1).zfill(3)}",
            "category": "load_balancer",
            "alert": {
                "type": "critical",
                "service": "load_balancer",
                "message": messages[i],
                "timestamp": f"2026-02-16T20:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "load_balancer",
            "expected_category": "service_degradation",
            "min_confidence": 0.7
        } for i in range(10)]
    
    def _generate_dns_failure_tests(self) -> List[Dict]:
        """Generate DNS failure test cases."""
        messages = [
            "DNS resolution failed for domain",
            "Name or service not known",
            "DNS server not responding",
            "NXDOMAIN: domain does not exist",
            "DNS timeout after 5 seconds",
            "DNS cache expired",
            "Route53 health check failed",
            "DNS zone not found",
            "DNS query refused",
            "Reverse DNS lookup failed"
        ]
        
        return [{
            "id": f"DNS_{str(i+1).zfill(3)}",
            "category": "dns_failure",
            "alert": {
                "type": "error",
                "service": ["network", "api"][i % 2],
                "message": messages[i],
                "timestamp": f"2026-02-16T21:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "network",
            "expected_category": "service_degradation",
            "min_confidence": 0.7
        } for i in range(10)]
    
    def _generate_ssl_certificate_tests(self) -> List[Dict]:
        """Generate SSL certificate test cases."""
        messages = [
            "SSL certificate expired",
            "Certificate validation failed",
            "SSL handshake failed",
            "Certificate chain incomplete",
            "Certificate hostname mismatch",
            "Self-signed certificate rejected",
            "Certificate revoked",
            "SSL protocol version mismatch"
        ]
        
        return [{
            "id": f"SSL_{str(i+1).zfill(3)}",
            "category": "ssl_certificate",
            "alert": {
                "type": "error",
                "service": ["api", "load_balancer"][i % 2],
                "message": messages[i],
                "timestamp": f"2026-02-16T22:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "application",
            "expected_category": "configuration_error",
            "min_confidence": 0.75
        } for i in range(8)]
    
    def _generate_queue_backlog_tests(self) -> List[Dict]:
        """Generate queue backlog test cases."""
        messages = [
            "SQS queue depth exceeding threshold",
            "Message processing lag: 5 minutes",
            "Dead letter queue filling up",
            "Consumer lag increasing",
            "Queue messages timing out",
            "Processing rate < ingestion rate",
            "Queue at maximum capacity",
            "Message retention period expiring"
        ]
        
        return [{
            "id": f"QUEUE_{str(i+1).zfill(3)}",
            "category": "queue_backlog",
            "alert": {
                "type": "warning",
                "service": "queue",
                "message": messages[i],
                "timestamp": f"2026-02-16T23:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "queue",
            "expected_category": "resource_exhaustion",
            "min_confidence": 0.7
        } for i in range(8)]
    
    def _generate_deadlock_tests(self) -> List[Dict]:
        """Generate deadlock test cases."""
        messages = [
            "Database deadlock detected",
            "Lock acquisition timeout",
            "Distributed lock failure",
            "Resource deadlock avoided",
            "Transaction rollback: deadlock",
            "Mutex lock timeout",
            "Circular wait detected",
            "Thread deadlock: stack trace"
        ]
        
        return [{
            "id": f"DEADLOCK_{str(i+1).zfill(3)}",
            "category": "deadlock",
            "alert": {
                "type": "error",
                "service": ["database", "application"][i % 2],
                "message": messages[i],
                "timestamp": f"2026-02-17T00:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "database",
            "expected_category": "application_error",
            "min_confidence": 0.7
        } for i in range(8)]
    
    def _generate_third_party_api_tests(self) -> List[Dict]:
        """Generate third-party API failure test cases."""
        messages = [
            "Payment gateway timeout",
            "External API returned 503",
            "Third-party service unavailable",
            "Stripe API rate limit",
            "AWS API throttling",
            "Google Maps API error",
            "Twilio SMS delivery failed",
            "SendGrid API authentication failed"
        ]
        
        return [{
            "id": f"THIRD_{str(i+1).zfill(3)}",
            "category": "third_party_api",
            "alert": {
                "type": "error",
                "service": "external_api",
                "message": messages[i],
                "timestamp": f"2026-02-17T01:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "external_api",
            "expected_category": "dependency_failure",
            "min_confidence": 0.65
        } for i in range(8)]
    
    def _generate_intermittent_error_tests(self) -> List[Dict]:
        """Generate intermittent error test cases."""
        messages = [
            "Request failed intermittently",
            "Sporadic connection failures",
            "Random timeout errors",
            "Occasional 500 errors",
            "Intermittent authentication failures",
            "Flapping health checks",
            "Periodic request spikes",
            "Transient network blips"
        ]
        
        return [{
            "id": f"INTERMIT_{str(i+1).zfill(3)}",
            "category": "intermittent_error",
            "alert": {
                "type": "warning",
                "service": ["api", "network"][i % 2],
                "message": messages[i],
                "timestamp": f"2026-02-17T02:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": ["network", "application"][i % 2],
            "expected_category": "service_degradation",
            "min_confidence": 0.5  # Lower confidence expected
        } for i in range(8)]
    
    def _generate_correlated_failure_tests(self) -> List[Dict]:
        """Generate correlated service failure test cases."""
        return [{
            "id": f"CORR_{str(i+1).zfill(3)}",
            "category": "correlated_failure",
            "alert": {
                "type": "error",
                "service": ["api", "database", "cache"][i % 3],
                "message": f"Service degradation across multiple systems",
                "timestamp": f"2026-02-17T03:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "systemic_issue",
            "expected_category": "correlated_failure",
            "min_confidence": 0.6,
            "context": {
                "recent_alerts": [
                    {"service": "api", "type": "error"},
                    {"service": "database", "type": "warning"},
                    {"service": "cache", "type": "error"}
                ]
            }
        } for i in range(7)]
    
    def _generate_performance_degradation_tests(self) -> List[Dict]:
        """Generate performance degradation test cases."""
        messages = [
            "Response time increased 5x",
            "Throughput dropped by 50%",
            "Latency spiking intermittently",
            "Query performance degraded",
            "API slowdown detected",
            "Batch processing taking longer",
            "Background job backlog growing"
        ]
        
        return [{
            "id": f"PERF_{str(i+1).zfill(3)}",
            "category": "performance_degradation",
            "alert": {
                "type": "warning",
                "service": ["api", "database", "worker"][i % 3],
                "message": messages[i],
                "timestamp": f"2026-02-17T04:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": ["database", "application", "network"][i % 3],
            "expected_category": "service_degradation",
            "min_confidence": 0.55
        } for i in range(7)]
    
    def _generate_novel_issue_tests(self) -> List[Dict]:
        """Generate novel/unknown issue test cases."""
        messages = [
            "Unexpected system behavior observed",
            "Unknown error code: XYZ-999",
            "Anomalous pattern detected",
            "New failure mode discovered",
            "Unhandled exception type",
            "Novel attack pattern suspected"
        ]
        
        return [{
            "id": f"NOVEL_{str(i+1).zfill(3)}",
            "category": "novel_issue",
            "alert": {
                "type": "unknown",
                "service": "application",
                "message": messages[i],
                "timestamp": f"2026-02-17T05:{str(i).zfill(2)}:00Z"
            },
            "expected_root_cause": "unknown",
            "expected_category": "unknown",
            "min_confidence": 0.4,  # Very low confidence expected
            "requires_llm": True  # These should trigger LLM
        } for i in range(6)]
    
    # ========================================================================
    # TEST EXECUTION
    # ========================================================================
    
    def run_all_tests(self) -> Dict:
        """
        Run all test cases and collect results.
        """
        print("=" * 80)
        print(f"RUNNING DIAGNOSTIC SYSTEM TEST SUITE")
        print(f"Total Test Cases: {len(self.test_cases)}")
        print("=" * 80)
        
        start_time = time.time()
        
        for i, test_case in enumerate(self.test_cases, 1):
            if i % 20 == 0:
                print(f"\nProgress: {i}/{len(self.test_cases)} tests completed...")
            
            result = self._run_single_test(test_case)
            self.results.append(result)
            
            # Collect metrics
            self.metrics['latency'].append(result['latency_ms'])
            self.metrics['accuracy'].append(1 if result['correct'] else 0)
            self.metrics['confidence'].append(result['actual_confidence'])
            self.metrics[test_case['category']].append(result)
        
        total_time = time.time() - start_time
        
        print(f"\n✓ All tests completed in {total_time:.2f}s")
        
        return self._generate_report()
    
    def _run_single_test(self, test_case: Dict) -> Dict:
        """Run a single test case and return result."""
        
        test_id = test_case['id']
        alert = test_case['alert']
        expected_root_cause = test_case['expected_root_cause']
        expected_category = test_case.get('expected_category')
        min_confidence = test_case.get('min_confidence', 0.5)
        
        # Time the diagnosis
        start_time = time.time()
        
        try:
            # Run diagnosis
            diagnoses = self.agent.handle_anomaly(alert)
            
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            if not diagnoses:
                return {
                    'test_id': test_id,
                    'category': test_case['category'],
                    'correct': False,
                    'actual_root_cause': None,
                    'expected_root_cause': expected_root_cause,
                    'actual_confidence': 0.0,
                    'latency_ms': latency,
                    'error': 'No diagnosis returned',
                    'llm_used': False
                }
            
            # Get top diagnosis
            top_diagnosis = diagnoses[0]
            actual_root_cause = top_diagnosis.get('root_cause')
            actual_category = top_diagnosis.get('category')
            actual_confidence = top_diagnosis.get('confidence', 0.0)
            llm_used = top_diagnosis.get('source') == 'llm_fallback'
            
            # Check correctness
            root_cause_correct = actual_root_cause == expected_root_cause
            category_correct = (expected_category is None or 
                              actual_category == expected_category)
            confidence_ok = actual_confidence >= min_confidence
            
            correct = root_cause_correct and confidence_ok
            
            return {
                'test_id': test_id,
                'category': test_case['category'],
                'correct': correct,
                'root_cause_correct': root_cause_correct,
                'category_correct': category_correct,
                'confidence_ok': confidence_ok,
                'actual_root_cause': actual_root_cause,
                'expected_root_cause': expected_root_cause,
                'actual_category': actual_category,
                'expected_category': expected_category,
                'actual_confidence': actual_confidence,
                'min_confidence': min_confidence,
                'latency_ms': latency,
                'llm_used': llm_used,
                'evidence_count': len(top_diagnosis.get('evidence', [])),
                'actions_count': len(top_diagnosis.get('recommended_actions', []))
            }
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return {
                'test_id': test_id,
                'category': test_case['category'],
                'correct': False,
                'actual_root_cause': None,
                'expected_root_cause': expected_root_cause,
                'actual_confidence': 0.0,
                'latency_ms': latency,
                'error': str(e),
                'llm_used': False
            }
    
    # ========================================================================
    # REPORT GENERATION
    # ========================================================================
    
    def _generate_report(self) -> Dict:
        """Generate comprehensive test report."""
        
        total_tests = len(self.results)
        correct_tests = sum(1 for r in self.results if r['correct'])
        
        # Overall metrics
        overall_accuracy = (correct_tests / total_tests) * 100
        avg_latency = statistics.mean(self.metrics['latency'])
        median_latency = statistics.median(self.metrics['latency'])
        p95_latency = self._percentile(self.metrics['latency'], 95)
        p99_latency = self._percentile(self.metrics['latency'], 99)
        
        avg_confidence = statistics.mean(self.metrics['confidence'])
        
        # LLM usage stats
        llm_used_count = sum(1 for r in self.results if r.get('llm_used', False))
        llm_usage_rate = (llm_used_count / total_tests) * 100
        
        # Per-category accuracy
        category_stats = self._calculate_category_stats()
        
        # Failure analysis
        failures = [r for r in self.results if not r['correct']]
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': correct_tests,
                'failed': total_tests - correct_tests,
                'accuracy_percent': round(overall_accuracy, 2),
                'avg_latency_ms': round(avg_latency, 2),
                'median_latency_ms': round(median_latency, 2),
                'p95_latency_ms': round(p95_latency, 2),
                'p99_latency_ms': round(p99_latency, 2),
                'avg_confidence': round(avg_confidence, 3),
                'llm_usage_rate_percent': round(llm_usage_rate, 2),
                'llm_used_count': llm_used_count
            },
            'category_performance': category_stats,
            'failure_analysis': {
                'total_failures': len(failures),
                'failure_by_category': self._group_failures_by_category(failures),
                'failure_reasons': self._analyze_failure_reasons(failures)
            },
            'latency_distribution': {
                'min_ms': round(min(self.metrics['latency']), 2),
                'max_ms': round(max(self.metrics['latency']), 2),
                'std_dev_ms': round(statistics.stdev(self.metrics['latency']), 2)
            },
            'confidence_distribution': {
                'min': round(min(self.metrics['confidence']), 3),
                'max': round(max(self.metrics['confidence']), 3),
                'std_dev': round(statistics.stdev(self.metrics['confidence']), 3)
            }
        }
        
        return report
    
    def _calculate_category_stats(self) -> Dict:
        """Calculate per-category statistics."""
        stats = {}
        
        # Get unique categories
        categories = set(r['category'] for r in self.results)
        
        for category in categories:
            category_results = [r for r in self.results if r['category'] == category]
            
            total = len(category_results)
            correct = sum(1 for r in category_results if r['correct'])
            accuracy = (correct / total) * 100 if total > 0 else 0
            
            latencies = [r['latency_ms'] for r in category_results]
            confidences = [r['actual_confidence'] for r in category_results]
            
            llm_used = sum(1 for r in category_results if r.get('llm_used', False))
            
            stats[category] = {
                'total_tests': total,
                'passed': correct,
                'failed': total - correct,
                'accuracy_percent': round(accuracy, 2),
                'avg_latency_ms': round(statistics.mean(latencies), 2),
                'avg_confidence': round(statistics.mean(confidences), 3),
                'llm_usage_count': llm_used
            }
        
        return stats
    
    def _group_failures_by_category(self, failures: List[Dict]) -> Dict:
        """Group failures by category."""
        grouped = defaultdict(list)
        
        for failure in failures:
            grouped[failure['category']].append({
                'test_id': failure['test_id'],
                'expected': failure['expected_root_cause'],
                'actual': failure['actual_root_cause'],
                'confidence': failure['actual_confidence']
            })
        
        return dict(grouped)
    
    def _analyze_failure_reasons(self, failures: List[Dict]) -> Dict:
        """Analyze reasons for failures."""
        reasons = {
            'wrong_root_cause': 0,
            'low_confidence': 0,
            'no_diagnosis': 0,
            'exception_error': 0
        }
        
        for failure in failures:
            if failure.get('error'):
                if 'No diagnosis' in failure['error']:
                    reasons['no_diagnosis'] += 1
                else:
                    reasons['exception_error'] += 1
            elif not failure.get('root_cause_correct', False):
                reasons['wrong_root_cause'] += 1
            elif not failure.get('confidence_ok', False):
                reasons['low_confidence'] += 1
        
        return reasons
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def print_report(self, report: Dict):
        """Print formatted test report."""
        
        print("\n" + "=" * 80)
        print("DIAGNOSTIC SYSTEM TEST REPORT")
        print("=" * 80)
        
        # Summary
        summary = report['summary']
        print(f"\n{'OVERALL PERFORMANCE':^80}")
        print("-" * 80)
        print(f"Total Tests:           {summary['total_tests']}")
        print(f"Passed:                {summary['passed']} ({summary['accuracy_percent']}%)")
        print(f"Failed:                {summary['failed']}")
        print(f"\nAverage Latency:       {summary['avg_latency_ms']} ms")
        print(f"Median Latency:        {summary['median_latency_ms']} ms")
        print(f"P95 Latency:           {summary['p95_latency_ms']} ms")
        print(f"P99 Latency:           {summary['p99_latency_ms']} ms")
        print(f"\nAverage Confidence:    {summary['avg_confidence']}")
        print(f"LLM Usage:             {summary['llm_used_count']} ({summary['llm_usage_rate_percent']}%)")
        
        # Category Performance
        print(f"\n{'CATEGORY PERFORMANCE':^80}")
        print("-" * 80)
        print(f"{'Category':<25} {'Tests':<8} {'Pass':<8} {'Fail':<8} {'Accuracy':<10} {'Latency':<10}")
        print("-" * 80)
        
        for category, stats in sorted(report['category_performance'].items()):
            print(f"{category:<25} {stats['total_tests']:<8} {stats['passed']:<8} "
                  f"{stats['failed']:<8} {stats['accuracy_percent']:<9.1f}% "
                  f"{stats['avg_latency_ms']:<9.1f}ms")
        
        # Failure Analysis
        print(f"\n{'FAILURE ANALYSIS':^80}")
        print("-" * 80)
        failure_analysis = report['failure_analysis']
        print(f"Total Failures:        {failure_analysis['total_failures']}")
        print(f"\nFailure Reasons:")
        for reason, count in failure_analysis['failure_reasons'].items():
            print(f"  {reason.replace('_', ' ').title():<30} {count}")
        
        # Latency Distribution
        print(f"\n{'LATENCY DISTRIBUTION':^80}")
        print("-" * 80)
        latency = report['latency_distribution']
        print(f"Min:                   {latency['min_ms']} ms")
        print(f"Max:                   {latency['max_ms']} ms")
        print(f"Std Deviation:         {latency['std_dev_ms']} ms")
        
        # Performance Grade
        print(f"\n{'PERFORMANCE GRADE':^80}")
        print("-" * 80)
        grade = self._calculate_grade(summary['accuracy_percent'], summary['avg_latency_ms'])
        print(f"Overall Grade:         {grade}")
        
        print("\n" + "=" * 80)
    
    def _calculate_grade(self, accuracy: float, latency: float) -> str:
        """Calculate performance grade."""
        if accuracy >= 95 and latency < 100:
            return "A+ (Excellent)"
        elif accuracy >= 90 and latency < 150:
            return "A (Very Good)"
        elif accuracy >= 85 and latency < 200:
            return "B+ (Good)"
        elif accuracy >= 80 and latency < 250:
            return "B (Satisfactory)"
        elif accuracy >= 75 and latency < 300:
            return "C+ (Acceptable)"
        elif accuracy >= 70:
            return "C (Needs Improvement)"
        else:
            return "D (Poor - Needs Major Improvement)"
    
    def save_report(self, report: Dict, filename: str = "test_report.json"):
        """Save report to JSON file."""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Report saved to {filename}")
    
    def save_detailed_results(self, filename: str = "test_results_detailed.json"):
        """Save detailed results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Detailed results saved to {filename}")


# ========================================================================
# MAIN EXECUTION
# ========================================================================

def run_test_suite():
    """Run the complete test suite."""
    
    print("\n" + "🧪" * 40)
    print("INITIALIZING DIAGNOSTIC SYSTEM TEST SUITE")
    print("🧪" * 40)
    
    # Initialize test suite
    suite = DiagnosticTestSuite()
    
    print(f"\n✓ Generated {len(suite.test_cases)} test cases")
    print(f"✓ Covering 20 different diagnostic categories")
    
    input("\nPress Enter to start testing...")
    
    # Run tests
    report = suite.run_all_tests()
    
    # Print report
    suite.print_report(report)
    
    # Save reports
    suite.save_report(report, "reports/diagnostic_test_report.json")
    suite.save_detailed_results("reports/diagnostic_test_results_detailed.json")
    
    print("\n✓ Testing complete!")
    print("📊 Reports generated in 'reports/' directory")
    
    return suite, report


if __name__ == "__main__":
    suite, report = run_test_suite()