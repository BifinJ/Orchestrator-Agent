import re
from typing import Optional, Dict


class ServiceDetector:
    """
    Dynamically identifies which service an alert belongs to
    based on context clues from logs, metrics, and AWS metadata.
    """
    
    # Service patterns for log message detection
    LOG_PATTERNS = {
        'api': [
            r'GET\s+/',
            r'POST\s+/',
            r'PUT\s+/',
            r'DELETE\s+/',
            r'HTTP/\d\.\d',
            r'\d{3}\s+\d+\.\d+ms', 
            r'application/json',
            r'User-Agent:',
        ],
        'database': [
            r'mysql',
            r'postgres',
            r'connection pool',
            r'query timeout',
            r'deadlock',
            r'transaction',
            r'SELECT\s+\*',
            r'INSERT INTO',
            r'UPDATE\s+\w+\s+SET',
        ],
        'cache': [
            r'redis',
            r'memcached',
            r'cache miss',
            r'cache hit',
            r'eviction',
        ],
        'queue': [
            r'sqs',
            r'rabbitmq',
            r'kafka',
            r'message queue',
            r'consumer',
            r'producer',
        ],
        'worker': [
            r'celery',
            r'background job',
            r'task\s+\w+\s+(started|completed|failed)',
            r'worker\s+\d+',
        ]
    }
    
    # AWS namespace to service mapping
    NAMESPACE_TO_SERVICE = {
        'AWS/EC2': 'ec2',
        'AWS/RDS': 'database',
        'AWS/ELB': 'load_balancer',
        'AWS/ApplicationELB': 'load_balancer',
        'AWS/Lambda': 'lambda',
        'AWS/DynamoDB': 'database',
        'AWS/ElastiCache': 'cache',
        'AWS/SQS': 'queue',
        'AWS/ECS': 'container',
        'AWS/EKS': 'container',
    }
    
    # Metric name patterns
    METRIC_PATTERNS = {
        'api': ['RequestCount', 'TargetResponseTime', 'HTTPCode'],
        'database': ['DatabaseConnections', 'ReadLatency', 'WriteLatency'],
        'cache': ['CacheHits', 'CacheMisses', 'Evictions'],
        'network': ['NetworkIn', 'NetworkOut', 'NetworkPackets'],
        'compute': ['CPUUtilization', 'CPUCreditBalance', 'StatusCheck'],
        'storage': ['DiskReadBytes', 'DiskWriteBytes', 'VolumeReadOps'],
    }
    
    @classmethod
    def detect_from_log(cls, message: str) -> str:
        """
        Detect service type from log message content.
        
        Args:
            message: The log message string
            
        Returns:
            Service name (e.g., 'api', 'database', 'cache')
        """
        if not isinstance(message, str):
            return 'unknown'
        
        message_lower = message.lower()
        
        # Check each service pattern
        for service, patterns in cls.LOG_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return service
        
        # Default to 'application' if no specific service detected
        return 'application'
    
    @classmethod
    def detect_from_metric(cls, metric_name: str, namespace: str) -> str:
        """
        Detect service type from CloudWatch metric.
        
        Args:
            metric_name: The metric name (e.g., 'CPUUtilization')
            namespace: AWS namespace (e.g., 'AWS/EC2')
            
        Returns:
            Service name
        """
        # First try namespace mapping
        if namespace in cls.NAMESPACE_TO_SERVICE:
            base_service = cls.NAMESPACE_TO_SERVICE[namespace]
            
            # Refine based on metric name if possible
            for service, metric_keywords in cls.METRIC_PATTERNS.items():
                for keyword in metric_keywords:
                    if keyword in metric_name:
                        return service
            
            return base_service
        
        # Fall back to metric pattern matching
        for service, metric_keywords in cls.METRIC_PATTERNS.items():
            for keyword in metric_keywords:
                if keyword in metric_name:
                    return service
        
        return 'ec2'  # Default for unknown EC2 metrics
    
    @classmethod
    def detect_from_dimensions(cls, dimensions: list) -> Optional[str]:
        """
        Detect service from CloudWatch dimensions.
        
        Args:
            dimensions: List of dimension dicts with 'Name' and 'Value'
            
        Returns:
            Service name if detectable, None otherwise
        """
        for dim in dimensions:
            name = dim.get('Name', '')
            
            if name == 'LoadBalancer':
                return 'load_balancer'
            elif name == 'TargetGroup':
                return 'api'
            elif name == 'DBInstanceIdentifier':
                return 'database'
            elif name == 'CacheClusterId':
                return 'cache'
            elif name == 'QueueName':
                return 'queue'
            elif name == 'FunctionName':
                return 'lambda'
        
        return None
    
    @classmethod
    def detect_service(cls, 
                      message: str = None, 
                      metric_name: str = None,
                      namespace: str = None,
                      dimensions: list = None) -> str:
        """
        Comprehensive service detection using all available context.
        
        Args:
            message: Log message (optional)
            metric_name: Metric name (optional)
            namespace: AWS namespace (optional)
            dimensions: Metric dimensions (optional)
            
        Returns:
            Detected service name
        """
        # Priority 1: Check dimensions (most specific)
        if dimensions:
            service = cls.detect_from_dimensions(dimensions)
            if service:
                return service
        
        # Priority 2: Check metric + namespace
        if metric_name and namespace:
            return cls.detect_from_metric(metric_name, namespace)
        
        # Priority 3: Check log message
        if message:
            return cls.detect_from_log(message)
        
        # Default fallback
        return 'unknown'


# Convenience function for quick detection
def detect_service(**kwargs) -> str:
    """
    Quick service detection function.
    
    Usage:
        detect_service(message="GET /api/users 200 45.2ms")
        detect_service(metric_name="CPUUtilization", namespace="AWS/EC2")
        detect_service(dimensions=[{"Name": "LoadBalancer", "Value": "..."}])
    """
    return ServiceDetector.detect_service(**kwargs)