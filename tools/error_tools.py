def get_current_errors():
    return [
        {"service": "EC2", "error": "InstanceNotReachable"},
        {"service": "S3", "error": "AccessDenied"},
    ]

def analyze_error_trend():
    return "Errors increased by 15% in the last 24 hours."
