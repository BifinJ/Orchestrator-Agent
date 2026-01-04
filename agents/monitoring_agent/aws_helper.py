import boto3
import os

from dotenv import load_dotenv
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")

logs_client = boto3.client("logs", region_name=AWS_REGION)
cw_client = boto3.client("cloudwatch", region_name=AWS_REGION)
