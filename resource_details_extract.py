#testing
import boto3
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
import argparse
from colorama import Fore, Style
# Initialize the argument parser
parser = argparse.ArgumentParser(description='Extract instance details and save to Excel')
parser.add_argument('-r', '--region', help='AWS Region', required=True)
args = parser.parse_args()

# Initialize the Boto3 client with the specified region
ec2 = boto3.client('ec2', region_name=args.region)
autoscaling = boto3.client('autoscaling', region_name=args.region)  # New line to initialize Auto Scaling client
# Get all instances
#ssm = boto3.client('ssm' ,  region_name=args.region)
instances = ec2.describe_instances()

# Create a new Excel workbook
workbook = openpyxl.Workbook()
sheet = workbook.active
sheet.title = 'Instance Details'

# Write account ID
print(f'{Fore.GREEN} [\u2713] Creating workbook {Style.RESET_ALL} \n')
account_id = boto3.client('sts').get_caller_identity().get('Account')
account_cell = sheet['A1']
account_cell.value = f'Account ID: {account_id} ({args.region})'
account_cell.font = Font(bold=True)
account_cell.alignment = Alignment(horizontal='center')
account_cell.fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
sheet.merge_cells('A1:K1')

# Write headers
print(f'{Fore.GREEN} [\u2713] Adding header {Style.RESET_ALL}\n')
headers = ['Service', 'Instance_Name', 'Instance_ID', 'Instance Class', 'State', 'Platform', 'Detailed Monitoring', 'SSM_Agent', 'CW_Agent', 'AutoScalingGroup', 'Remarks']  # Updated headers
for col, header in enumerate(headers, start=1):
    cell = sheet.cell(row=2, column=col, value=header)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
    cell.alignment = Alignment(horizontal='center', vertical='center')

# Write EC2 details to Excel
print(f'{Fore.GREEN} [\u2713] Finding Instance Details {Style.RESET_ALL} \n')
row = 3
instance_count= sum(1 for _ in instances['Reservations'] for _ in _['Instances'])
print(f' {Fore.YELLOW} [\u2B50] Total instances present are : {instance_count} {Style.RESET_ALL}\n ' )
for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
      
        # Check if SSM agent is installed
        ssm_client = boto3.client('ssm', region_name=args.region)
        ssm_status = ''
        try:
            ssm_response = ssm_client.describe_instance_information(InstanceInformationFilterList=[{'key': 'InstanceIds', 'valueSet': [instance_id]}])
            if ssm_response['InstanceInformationList']:
                ssm_status = 'Installed'
            else:
                ssm_status = 'Not Installed'
        except ssm_client.exceptions.InvalidInstanceId:
            ssm_status = 'Invalid Instance ID or Not Installed'
        
        # Check if CloudWatch agent is installed
        cw_client = boto3.client('cloudwatch', region_name=args.region)
        memory_metric_name = ""
        disk_metric_name = ""
        
        cw_metrics = cw_client.list_metrics(
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
            ]
        ).get('Metrics')
        
        metric_list = []
        cw_agent_list = []
        custom_namespace_list = []
        
        for data in cw_metrics:
            for x in list(data['Namespace'].split(" ")):
                if x not in metric_list:
                    metric_list.append(x)
            if "Memory Available MBytes" not in data['MetricName'] and "Memory" in data['MetricName'] or "mem" in data[
                'MetricName']:
                memory_metric_name = data['MetricName']
        
            elif "LogicalDisk % Free Space" in data['MetricName'] or "disk_used_percent" in data['MetricName']:
                disk_metric_name = data['MetricName']

        # preparing for workbook creation    
        instance_name = ''
        if 'Tags' in instance:
            for tag in instance['Tags']:
                if tag["Key"] == "Name":
                    instance_name = tag["Value"]
                    break
        instance_class = instance['InstanceType']
        state = instance['State']['Name']
        platform = instance.get('Platform', 'Linux/Unix')  # Default to Linux/Unix if platform is not specified
        region = args.region
        monitoring_state = instance['Monitoring']['State'] if 'Monitoring' in instance and 'State' in instance['Monitoring'] else 'Disabled'
        
        print(f'  \t {Fore.MAGENTA} [\u269B ] Working on instance name : {instance_name} {Style.RESET_ALL} \n ' )
        # print(custom_metric_list)
        print(f' \t \t [\u26A1] memory metric name is: {Fore.GREEN}{memory_metric_name}{Style.RESET_ALL} \n ' )
        print(f' \t \t [\u26A1] disk metric name is: {Fore.GREEN}{disk_metric_name}{Style.RESET_ALL} \n ' )

        
        cw_status = ''
        try:
            if memory_metric_name in ["mem_used_percent", "Memory % Committed Bytes In Use", "Memory Available MBytes"] or disk_metric_name in ["LogicalDisk % Free Space", "disk_used_percent"]:
                cw_status = "installed"
            else:
                cw_status = "not installed"

        except cw_client.exceptions.ResourceNotFoundException:
            cw_status = 'Not Installed or No Alarms Configured'



        # Check if the instance is part of an Auto Scaling group
        response = autoscaling.describe_auto_scaling_instances(InstanceIds=[instance_id])
        auto_scaling_group = response['AutoScalingInstances'][0]['AutoScalingGroupName'] if response['AutoScalingInstances'] else 'Not in Auto Scaling Group'
        data = ['EC2', instance_name, instance_id, instance_class, state, platform, monitoring_state, ssm_status, cw_status, auto_scaling_group, '']  # Updated data
        for col, value in enumerate(data, start=1):
            cell = sheet.cell(row=row, column=col, value=value)
            if row > 2 or col > 1:  # Align everything to the left except for row 1, row 2, and column 1
                cell.alignment = Alignment(horizontal='left', vertical='center')
            else:  # Keep row 1, row 2, and column 1 centered
                cell.alignment = Alignment(horizontal='center', vertical='center')
        row += 1

# Merge the cells in the first column for the "EC2" service
service_cell = sheet.cell(row=3, column=1)
last_row = row - 1
sheet.merge_cells(start_row=3, start_column=1, end_row=last_row, end_column=1)
service_cell.value = 'EC2'
service_cell.font = Font(bold=True)
service_cell.alignment = Alignment(horizontal='center', vertical='center')
service_cell.fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")

# Get all RDS instances
rds = boto3.client('rds', region_name=args.region)
rds_instances = rds.describe_db_instances()
# Write RDS headers
rds_headers = ['RDSname', 'RDS Endpoint', 'Class', 'State', 'Engine', 'Version', 'Remarks']
for col, header in enumerate(rds_headers, start=2):
    cell = sheet.cell(row=row, column=col, value=header)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
    cell.alignment = Alignment(horizontal='center', vertical='center')

# Write RDS details to Excel
print(f' {Fore.GREEN} [\u2713] Adding RDS detals {Style.RESET_ALL} \n')
row += 1
#row is 9 here
for rds_instance in rds_instances['DBInstances']:
    rds_name = rds_instance['DBInstanceIdentifier']
    rds_endpoint = rds_instance['Endpoint']['Address']
    rds_class = rds_instance['DBInstanceClass']
    rds_state = rds_instance['DBInstanceStatus']
    rds_engine = rds_instance['Engine']
    rds_version = rds_instance['EngineVersion']
    rds_remarks = ''  # You can add remarks here if needed

    rds_data = [rds_name, rds_endpoint, rds_class, rds_state, rds_engine, rds_version, rds_remarks]
    for col, value in enumerate(rds_data, start=2):
        cell = sheet.cell(row=row, column=col, value=value)
        if row > 2 or col > 1:  # Align everything to the left except for row 1, row 2, and column 1
            cell.alignment = Alignment(horizontal='left', vertical='center')
        else:  # Keep row 1, row 2, and column 1 centered
            cell.alignment = Alignment(horizontal='center', vertical='center')
    row += 1
# Merge the cells in the first column for the "RDS" service
# row is 11 here
rds_service_cell = sheet.cell(row=last_row+1, column=1)
rds_last_row = row - 1 # 10
sheet.merge_cells(start_row=last_row+1, start_column=1, end_row=rds_last_row, end_column=1)
sheet.merge_cells(start_row=last_row+1, start_column=8, end_row=last_row+1, end_column=11)
rds_service_cell.value = 'RDS'
rds_service_cell.font = Font(bold=True)
rds_service_cell.alignment = Alignment(horizontal='center', vertical='center')
rds_service_cell.fill = PatternFill(start_color="FFFAF0", end_color="FFFAF0", fill_type="solid")

# Get all Auto Scaling groups
print(f' {Fore.GREEN} [\u2713] Adding Autoscalling details {Style.RESET_ALL} \n')
autoscaling_groups = autoscaling.describe_auto_scaling_groups()

# Write Auto Scaling Group headers
asg_headers = ['ASG Name', 'Launch Configuration', 'Launch Template' , 'Min Size', 'Max Size', 'Desired Capacity' ,'Remarks' ]
for col, header in enumerate(asg_headers, start=2):
    cell = sheet.cell(row=row, column=col, value=header)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
    cell.alignment = Alignment(horizontal='center', vertical='center')

# Write Auto Scaling Group details to Excel
row += 1
for group in autoscaling_groups['AutoScalingGroups']:
    asg_name = group['AutoScalingGroupName']
    launch_config = group.get('LaunchConfigurationName', 'N/A')  # Check if key is present
    #Launch_template =  group['LaunchTemplate'].get('LaunchTemplateName', 'N/A')
    Launch_template = group.get('LaunchTemplate', {}).get('LaunchTemplateName', 'N/A')
    min_size = group['MinSize']
    max_size = group['MaxSize']
    desired_capacity = group['DesiredCapacity']

    asg_data = [asg_name, launch_config,Launch_template, min_size, max_size, desired_capacity,'']
    for col, value in enumerate(asg_data, start=2):
        cell = sheet.cell(row=row, column=col, value=value)
        if row > 2 or col > 1:  # Align everything to the left except for row 1, row 2, and column 1
            cell.alignment = Alignment(horizontal='left', vertical='center')
        else:  # Keep row 1, row 2, and column 1 centered
            cell.alignment = Alignment(horizontal='center', vertical='center')
    row += 1

# Merge the cells in the first column for the "ASG" service
asg_service_cell = sheet.cell(row=rds_last_row+1, column=1)
asg_last_row = row - 1
sheet.merge_cells(start_row=rds_last_row+1, start_column=1, end_row=asg_last_row, end_column=1)
sheet.merge_cells(start_row=rds_last_row+1, start_column=8, end_row=rds_last_row+1, end_column=11)
asg_service_cell.value = 'ASG'
asg_service_cell.font = Font(bold=True)
asg_service_cell.alignment = Alignment(horizontal='center', vertical='center')
asg_service_cell.fill = PatternFill(start_color="F08080", end_color="F08080", fill_type="solid")



#################################

# Get all RDS cluster groups

print(f' {Fore.GREEN} [\u2713] Adding RDS cluster details {Style.RESET_ALL} \n')
RDS_cluster = rds.describe_db_clusters()

# Write RDS cluster headers
RDS_C_headers = ['RDS Cluster Name', 'Endpoints', 'class' , 'state', 'engine', 'version' ,'Remarks']
for col, header in enumerate(RDS_C_headers, start=2):
    cell = sheet.cell(row=row, column=col, value=header)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
    cell.alignment = Alignment(horizontal='center', vertical='center')

# Write RDS cluster details to Excel
row += 1
for cluster in RDS_cluster['DBClusters']:
    cluster_name = cluster['DatabaseName']
    cluster_endpoint = cluster['Endpoint']
    cluster_class = cluster['EngineMode']
    cluster_state = cluster['Status']
    cluster_engine = cluster['Engine']
    cluster_version = cluster['EngineVersion']
    cluster_remarks = ''  # You can add remarks here if needed

    cluster_data = [cluster_name, cluster_endpoint,cluster_class,cluster_state,cluster_engine,cluster_version,'']
    for col, value in enumerate(cluster_data, start=2):
        cell = sheet.cell(row=row, column=col, value=value)
        if row > 2 or col > 1:  # Align everything to the left except for row 1, row 2, and column 1
            cell.alignment = Alignment(horizontal='left', vertical='center')
        else:  # Keep row 1, row 2, and column 1 centered
            cell.alignment = Alignment(horizontal='center', vertical='center')
    row += 1

# Merge the cells in the first column for the "ASG" service
cluster_service_cell = sheet.cell(row=asg_last_row+1, column=1)
#row is 9,so cluster last row is 8 and asg last row is 6
cluster_last_row = row - 1
sheet.merge_cells(start_row=asg_last_row+1, start_column=1, end_row=cluster_last_row, end_column=1) # for service cell
sheet.merge_cells(start_row=asg_last_row+1, start_column=8, end_row=asg_last_row+1, end_column=11) # for header cell
sheet.merge_cells(start_row=cluster_last_row, start_column=8, end_row=cluster_last_row, end_column=11) # for header cell
cluster_service_cell.value = 'RDS Cluster'
cluster_service_cell.font = Font(bold=True)
cluster_service_cell.alignment = Alignment(horizontal='center', vertical='center')
cluster_service_cell.fill = PatternFill(start_color="FF00FF", end_color="FF00FF", fill_type="solid")
################################

print(f' {Fore.GREEN} [\u2713] Task completed successfully {Style.RESET_ALL} \n')



# Save the Excel workbook

workbook.save(f'Resource_{account_id}_{args.region}.xlsx')
