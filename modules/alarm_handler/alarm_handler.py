import os
import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table_name = os.environ.get('ALARM_TABLE_NAME')
    table = dynamodb.Table(table_name)

    # SNS can batch records; handle all
    for record in event.get('Records', []):
        try:
            sns = record.get('Sns', {})
            message = sns.get('Message')
            subject = sns.get('Subject')
            timestamp = sns.get('Timestamp')

            # Parse website name from alarm subject (format: "ALARM: LatencyAlarm-Google")
            website_name = "Unknown"
            if subject and "Alarm-" in subject:
                website_name = subject.split("Alarm-")[-1]

            item = {
                'timestamp': timestamp or datetime.utcnow().isoformat(),  # Partition key
                'website': website_name,  # Sort key
                'alarm_id': str(uuid.uuid4()),
                'subject': subject or 'CloudWatch Alarm',
                'message': message or json.dumps(sns)
            }

            table.put_item(Item=item)
        except Exception as e:
            print('Failed to write alarm to DynamoDB:', e)
    return {
        'statusCode': 200,
        'body': 'ok'
    }