def reduce_cost_recommendations():
    return [
        "Stop unused EC2 instances",
        "Switch to spot instances",
        "Use S3 lifecycle policies",
    ]

def get_cost_summary():
    return {"estimated_monthly_cost": "$120.45", "services": ["EC2", "S3", "Lambda"]}
