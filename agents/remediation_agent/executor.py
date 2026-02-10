

from dotenv import load_dotenv
load_dotenv()
import os
AWS_REGION = os.getenv("AWS_REGION")

"""
Clean Action Executor - Function Only
Just the execute_action function, nothing else
"""

import boto3
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def execute_action(action: str, service: str) -> dict:
    """
    Execute a remediation action on AWS
    
    Args:
        action: Action name ('restart_api', 'scale_api', etc.)
        service: Service name (e.g., 'api')
        region: AWS region (default: 'us-east-1')
        
    Returns:
        dict: {
            'status': 'success' or 'error',
            'action': action name,
            'service': service name,
            'message': description,
            'timestamp': ISO timestamp,
            ... additional fields depending on action
        }
    """
    logger.info(f"[EXECUTOR] Executing: {action} on service '{service}'")
    
    ec2 = boto3.client('ec2', region_name=AWS_REGION)
    
    try:
        # ============================================
        # RESTART ACTION
        # ============================================
        if action in ['restart_api', 'restart_service']:
            # Find EC2 instances with Name tag = 'mainproject'
            response = ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': ['mainproject']},
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            instance_ids = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
            
            if not instance_ids:
                logger.error(f"[EXECUTOR] No instances found with tag Name=mainproject")
                return {
                    'status': 'error',
                    'action': action,
                    'service': service,
                    'error': f'No running EC2 instances found with tag Name=mainproject',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Reboot instances
            ec2.reboot_instances(InstanceIds=instance_ids)
            
            logger.info(f"[EXECUTOR] ✓ SUCCESS: Rebooted {len(instance_ids)} instance(s)")
            return {
                'status': 'success',
                'action': action,
                'service': service,
                'instances_rebooted': instance_ids,
                'instance_count': len(instance_ids),
                'message': f'Rebooted {len(instance_ids)} instance(s)',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # ============================================
        # SCALE ACTION
        # ============================================
        elif action in ['scale_api', 'scale_service']:
            asg = boto3.client('autoscaling', region_name=AWS_REGION)
            asgs = asg.describe_auto_scaling_groups()
            
            for asg_info in asgs['AutoScalingGroups']:
                tags = {t['Key']: t['Value'] for t in asg_info['Tags']}
                
                if tags.get('Name') == 'mainproject':
                    asg_name = asg_info['AutoScalingGroupName']
                    current = asg_info['DesiredCapacity']
                    max_size = asg_info['MaxSize']
                    new_capacity = min(current + 1, max_size)
                    
                    if new_capacity == current:
                        logger.error(f"[EXECUTOR] Already at max capacity: {max_size}")
                        return {
                            'status': 'error',
                            'action': action,
                            'service': service,
                            'error': f'Already at max capacity: {max_size}',
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    
                    asg.set_desired_capacity(
                        AutoScalingGroupName=asg_name,
                        DesiredCapacity=new_capacity
                    )
                    
                    logger.info(f"[EXECUTOR] ✓ SUCCESS: Scaled from {current} to {new_capacity}")
                    return {
                        'status': 'success',
                        'action': action,
                        'service': service,
                        'asg_name': asg_name,
                        'previous_capacity': current,
                        'new_capacity': new_capacity,
                        'message': f'Scaled from {current} to {new_capacity}',
                        'timestamp': datetime.utcnow().isoformat()
                    }
            
            logger.error(f"[EXECUTOR] No Auto Scaling Group found")
            return {
                'status': 'error',
                'action': action,
                'service': service,
                'error': 'No Auto Scaling Group found',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # ============================================
        # UNKNOWN ACTION
        # ============================================
        else:
            logger.error(f"[EXECUTOR] Unknown action: {action}")
            return {
                'status': 'error',
                'action': action,
                'service': service,
                'error': f'Unknown action: {action}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        logger.error(f"[EXECUTOR] Exception: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'action': action,
            'service': service,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }