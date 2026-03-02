# agents/monitoring_agent/error_classifier.py (IMPROVED VERSION)

import re
from typing import Optional, Dict


class ErrorClassifier:
    """
    Enhanced error classifier with better pattern matching.
    """
    
    # CRITICAL: More comprehensive and specific patterns
    ERROR_PATTERNS = {
        'database': [
            # Connection issues
            r'database.*connection.*timeout',
            r'database.*connection.*failed',
            r'database.*connection.*refused',
            r'db.*connection.*pool.*exhausted',
            r'connection.*pool.*exhausted',
            r'mysql.*connection',
            r'postgres.*connection',
            r'postgresql.*connection',
            
            # Specific errors
            r'mysql.*error',
            r'postgres.*error',
            r'postgresql.*error',
            r'psycopg2',
            r'sqlalchemy',
            
            # Database operations
            r'connection.*to.*database.*failed',
            r'query.*timeout',
            r'deadlock.*detected',
            r'too many connections',
            r'lock wait timeout',
            r'lost connection.*mysql',
            r'lost connection.*postgres',
            r'could not connect.*database',
            r'could not connect.*server',
            
            # Replication/Lag
            r'database.*replication',
            r'database.*lag',
            r'slow.*query',
            
            # Authentication
            r'database.*authentication.*failed',
            r'database.*denied',
        ],
        
        'cache': [
            # Redis
            r'redis.*connection',
            r'redis.*timeout',
            r'redis.*refused',
            r'redis.*error',
            r'redis.*down',
            r'redis.*out of memory',
            r'redis.*cluster',
            r'redis.*replica',
            r'redis.*sentinel',
            r'redis.*aof',
            
            # Memcached
            r'memcached.*error',
            r'memcached.*connection',
            
            # Generic cache
            r'cache.*connection.*failed',
            r'cache.*connection.*refused',
            r'cache.*timeout',
            r'cache.*miss.*rate',
            r'cache.*eviction',
            r'cache.*write.*failure',
            r'cache.*corruption',
            r'cache.*unavailable',
        ],
        
        'queue': [
            # SQS
            r'sqs.*error',
            r'sqs.*queue',
            r'queue.*depth',
            r'message.*queue',
            
            # RabbitMQ
            r'rabbitmq.*connection',
            r'rabbitmq.*error',
            
            # Kafka
            r'kafka.*error',
            r'kafka.*lag',
            
            # Generic queue
            r'message.*processing.*lag',
            r'dead letter queue',
            r'consumer.*lag',
            r'producer.*error',
            r'message.*timeout',
            r'queue.*at.*capacity',
            r'queue.*messages.*timing out',
            r'processing.*rate.*<.*ingestion',
        ],
        
        'auth': [
            r'authentication.*failed',
            r'unauthorized',
            r'token.*expired',
            r'token.*invalid',
            r'jwt.*error',
            r'oauth.*error',
            r'permission.*denied',
            r'access.*denied',
            r'session.*expired',
            r'api.*key.*revoked',
            r'two.*factor.*authentication',
            r'account.*locked',
        ],
        
        'network': [
            r'connection.*timed out',
            r'network.*unreachable',
            r'connection.*refused',
            r'dns.*resolution.*failed',
            r'socket.*timeout',
            r'no route to host',
            r'connection.*reset',
            r'broken pipe',
            r'packet.*loss',
            r'tcp.*handshake',
            r'port.*unreachable',
            r'network.*interface.*down',
            r'firewall.*blocking',
            r'vpc.*peering',
            r'network.*congestion',
            r'name or service not known',
            r'nxdomain',
            r'dns.*server.*not responding',
            r'dns.*timeout',
            r'dns.*query.*refused',
            r'reverse.*dns.*lookup.*failed',
        ],
        
        'storage': [
            r'disk.*full',
            r'no space left',
            r'io.*error',
            r'disk.*i/o.*error',
            r'file.*not.*found',
            r'permission.*denied.*file',
            r's3.*error',
            r'ebs.*error',
            r'inode.*limit',
            r'disk.*quota',
            r'filesystem.*read.*only',
            r'volume.*mount.*failed',
            r'disk.*health.*check.*failed',
        ],
        
        'compute': [
            r'out of memory',
            r'memory.*error',
            r'cpu.*throttl',
            r'resource.*limit.*exceeded',
            r'oom.*killer',
            r'cpu.*usage.*100',
            r'thread.*pool.*exhausted',
            r'file.*descriptor.*limit',
            r'process.*count.*limit',
        ],
        
        'load_balancer': [
            r'load.*balancer',
            r'backend.*targets.*unhealthy',
            r'target.*group.*empty',
            r'health.*check.*failing',
            r'502.*bad.*gateway',
            r'sticky.*session.*failure',
            r'backend.*connection.*refused',
            r'target.*deregistration',
        ],
        
        'external_api': [
            r'payment.*gateway',
            r'stripe.*api',
            r'third.*party.*service',
            r'external.*api',
            r'external.*service.*unavailable',
            r'google.*maps.*api',
            r'twilio.*sms',
            r'sendgrid.*api',
        ],
        
        'application': [
            # Configuration
            r'invalid.*configuration',
            r'missing.*environment.*variable',
            r'configuration.*file.*not.*found',
            r'port.*already.*in.*use',
            r'invalid.*connection.*string',
            r'configuration.*validation.*failed',
            
            # SSL/TLS
            r'ssl.*certificate.*expired',
            r'certificate.*validation.*failed',
            r'ssl.*handshake.*failed',
            r'certificate.*chain',
            r'certificate.*hostname.*mismatch',
            r'self.*signed.*certificate',
            r'certificate.*revoked',
            
            # Memory leaks
            r'memory.*usage.*increasing',
            r'heap.*dump.*shows.*memory.*leak',
            r'gc.*running.*continuously',
            r'memory.*not.*being.*released',
            r'heap.*full',
            r'memory.*fragmentation',
            
            # Generic application
            r'unexpected.*system.*behavior',
            r'unknown.*error.*code',
            r'unhandled.*exception',
            r'novel.*attack.*pattern',
        ]
    }
    
    @classmethod
    def classify_error_source(cls, message: str, 
                             logged_from_service: str = None) -> Dict:
        """
        Classify where the error actually originated from based on content.
        
        IMPROVED: Better pattern matching and prioritization.
        """
        if not isinstance(message, str):
            return {
                'actual_service': logged_from_service or 'unknown',
                'confidence': 0.5,
                'reason': 'Invalid message type',
                'severity': 'unknown'
            }
        
        message_lower = message.lower()
        
        # STEP 1: Check for specific error patterns (HIGH PRIORITY)
        matches = []
        for service, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    matches.append({
                        'service': service,
                        'pattern': pattern,
                        'priority': cls._get_pattern_priority(pattern, message_lower)
                    })
        
        # STEP 2: Sort by priority (most specific matches first)
        if matches:
            matches.sort(key=lambda x: x['priority'], reverse=True)
            best_match = matches[0]
            
            return {
                'actual_service': best_match['service'],
                'confidence': 0.9,
                'reason': f"Matched pattern: {best_match['pattern']}",
                'severity': cls._classify_severity(message),
                'logged_from': logged_from_service
            }
        
        # STEP 3: No specific pattern - use logged source with lower confidence
        return {
            'actual_service': logged_from_service or 'application',
            'confidence': 0.6,
            'reason': 'No specific error pattern detected, using log source',
            'severity': cls._classify_severity(message),
            'logged_from': logged_from_service
        }
    
    @classmethod
    def _get_pattern_priority(cls, pattern: str, message: str) -> int:
        """
        Calculate pattern priority based on specificity.
        More specific patterns get higher priority.
        """
        priority = 0
        
        # Longer patterns are usually more specific
        priority += len(pattern)
        
        # Patterns with multiple words are more specific
        priority += pattern.count(r'\.')  * 10
        
        # Exact service name matches get bonus
        if any(name in pattern for name in ['redis', 'mysql', 'postgres', 'kafka', 'sqs']):
            priority += 50
        
        # Connection/timeout patterns are less specific
        if 'timeout' in pattern and pattern.count(r'\.') < 3:
            priority -= 20
        
        return priority
    
    @classmethod
    def _classify_severity(cls, message: str) -> str:
        """Determine error severity from message."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['critical', 'fatal', 'disk full', 'out of memory']):
            return 'critical'
        elif any(word in message_lower for word in ['error', 'exception', 'failed', 'timeout', 'refused']):
            return 'error'
        elif any(word in message_lower for word in ['warn', 'warning', 'deprecated', 'slow']):
            return 'warning'
        else:
            return 'info'


# Convenience function
def classify_error(message: str, logged_from: str = None) -> Dict:
    """
    Quick error classification.
    
    Usage:
        result = classify_error(
            "Database connection timeout", 
            logged_from="api"
        )
    """
    return ErrorClassifier.classify_error_source(message, logged_from)