import boto3

def get_cpu_usage(instance_id="i-1234567890"):
    client = boto3.client("cloudwatch", endpoint_url="http://localhost:4566")
    # Simulated response (since LocalStack won't have real data)
    return {"instance_id": instance_id, "cpu_usage": "23.5%"}

def get_instance_status(instance_id="i-1234567890"):
    ec2 = boto3.client("ec2", endpoint_url="http://localhost:4566")
    return {"instance_id": instance_id, "status": "running"}
