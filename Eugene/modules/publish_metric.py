import boto3
def publish(NS, metric_name, dimension, value):

    client = boto3.client('cloudwatch')
    unit = 'Count'
    if metric_name == "Latency":
        unit = 'Milliseconds'
    elif metric_name == "ResponseSize":
        unit = 'Bytes'


    # Put metric data function: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch/client/put_metric_data.html
    client.put_metric_data(
        Namespace=NS,
        MetricData=[ # data about availability metric data
            {
                'MetricName': metric_name,
                'Dimensions': dimension,
                'Value': value,
                'Unit': unit 
            }
        ]
    )

'''
    client.put_metric_data(
        Namespace=URL_NAMESPACE,
        MetricData=[ # data about latency
            {
                'MetricName': URL_MONITOR_LATENCY,
                'Dimensions': [
                    {
                        'Name': 'URL',
                        'Value': 'https://www.youtube.com'
                    }
                ],
                'Unit': 'Seconds',
                'Value': latency
            }
        ]
    )
    '''