import boto3
import argparse

# Create a parser
parser = argparse.ArgumentParser(description='Find target group of an instance')

# Add the arguments
parser.add_argument('-i', '--instance_id', type=str, required=True, help='The instance ID')
parser.add_argument('-r', '--region', type=str, required=True, help='The AWS region')

# Parse the arguments
args = parser.parse_args()

# Create a low-level service client
client = boto3.client('elbv2', region_name=args.region)

# Get the list of all target groups
target_groups = client.describe_target_groups()

# Check each target group
for target_group in target_groups['TargetGroups']:
    target_group_arn = target_group['TargetGroupArn']
    print(f"Checking target group {target_group_arn}")
    
    # Describe the target health for the current target group
    target_health_descriptions = client.describe_target_health(TargetGroupArn=target_group_arn)
    
    # Initialize a variable to check if the instance is found in the current target group
    found = False
    
    # Check each target health description
    for target_health_description in target_health_descriptions['TargetHealthDescriptions']:
        if target_health_description['Target']['Id'] == args.instance_id:
            print(f"Instance '{args.instance_id}' is in target group {target_group_arn}")
            print(f"**************************************************************************************************************************")
            found = True

    # If the instance is not found in the current target group
    if not found:
        print(f"Instance '{args.instance_id}' is not found in target group {target_group_arn}")
