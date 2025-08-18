import boto3
def publish(NS, metric_name, dimension, value):

    client = boto3.client('cloudwatch')


    client.put_metric_data(
        Namespace=NS,
        MetricData=[ # data about availability metric data
            {
                'MetricName': metric_name,
                'Dimensions': dimension,
                'Value': value
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