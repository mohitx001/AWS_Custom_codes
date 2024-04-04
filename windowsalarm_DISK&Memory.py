import argparse
import boto3
#test
def create_disk_alarm(region, instance_id):
    # Create session
    session = boto3.Session(region_name=region)

    # Get account ID
    account_id = session.client('sts').get_caller_identity()['Account']

    # Create SNS topic ARNs
    sns_urgent = f'arn:aws:sns:{region}:{account_id}:rackspace-support-urgent'
    sns_emergency = f'arn:aws:sns:{region}:{account_id}:rackspace-support-emergency'
    sns_customer = 'arn:aws:sns:ap-southeast-2:119489832836:119489832836-ap-southeast-2-modops-alerts'

    # Create CloudWatch client
    cw = session.client('cloudwatch')

    # Get instance name from instance ID
    ec2 = session.resource('ec2')
    instance = ec2.Instance(instance_id)
    instance_name = ''
    for tag in instance.tags:
        if tag['Key'] == 'Name':
            instance_name = tag['Value']
            break

    # Create disk space alarm
    disk_alarm_name = f"rackspace-modops-low-disk-alert-{instance_name}-{instance_id}-drive"
    disk_alarm_description = f"Notify when Disk space of instance {instance_id} for drive is breaching threshold for 10 mins"
    cw.put_metric_alarm(
        AlarmName=disk_alarm_name,
        ComparisonOperator='LessThanOrEqualToThreshold',
        EvaluationPeriods=2,
        MetricName='LogicalDisk % Free Space',
        Namespace='CWAgent',
        Period=300,
        Statistic='Average',
        Threshold=10.0,
        ActionsEnabled=True,
        AlarmActions=[sns_urgent,sns_customer],
        OKActions=[sns_urgent],
        AlarmDescription=disk_alarm_description,
        Unit='Percent',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': instance_id
            },
        ],
    )

    print(f"Successfully created disk space alarm with name {disk_alarm_name}")

def create_memory_alarm(region, instance_id):
    # Create session
    session = boto3.Session(region_name=region)

    # Get account ID
    account_id = session.client('sts').get_caller_identity()['Account']

    # Create SNS topic ARNs
    sns_urgent = f'arn:aws:sns:{region}:{account_id}:rackspace-support-urgent'
    sns_customer = 'arn:aws:sns:ap-southeast-2:119489832836:119489832836-ap-southeast-2-modops-alerts'

    # Create CloudWatch client
    cw = session.client('cloudwatch')

    # Get instance name from instance ID
    ec2 = session.resource('ec2')
    instance = ec2.Instance(instance_id)
    instance_name = ''
    for tag in instance.tags:
        if tag['Key'] == 'Name':
            instance_name = tag['Value']
            break

    # Create memory usage alarm
    memory_alarm_name = f"rackspace-modops-low-memory-alert-{instance_name}-{instance_id}"
    memory_alarm_description = f"Notify when used memory percent of instance {instance_id} is more than 90%"
    cw.put_metric_alarm(
        AlarmName=memory_alarm_name,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        EvaluationPeriods=6,
        MetricName='Memory % Committed Bytes In Use',
        Namespace='CWAgent',
        Period=300,
        Statistic='Average',
        Threshold=90.0,
        ActionsEnabled=True,
        AlarmActions=[sns_urgent,sns_customer],
        OKActions=[sns_urgent],
        AlarmDescription=memory_alarm_description,
        Unit='Percent',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': instance_id
            },
        ],
    )

    print(f"Successfully created memory usage alarm with name {memory_alarm_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create CloudWatch alarms.')
    parser.add_argument('--region', required=True, help='The region where the instance is located.')
    parser.add_argument('--instance-id', required=True, help='The ID of the instance.')
    args = parser.parse_args()

    print("Select the type of alarm to create:")
    print("1. Disk Alarm")
    print("2. Memory Alarm")
    print("3. Both")

    choice = input("Enter your choice (1/2/3): ")

    if choice == "1":
        create_disk_alarm(args.region, args.instance_id)
    elif choice == "2":
        create_memory_alarm(args.region, args.instance_id)
    elif choice == "3":
        create_disk_alarm(args.region, args.instance_id)
        create_memory_alarm(args.region, args.instance_id)
    else:
        print("Invalid choice. Please select 1, 2, or 3.")
