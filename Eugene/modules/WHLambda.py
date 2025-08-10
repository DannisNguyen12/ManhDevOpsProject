## Web Health Lambda Function
# This Lambda function is designed to monitor the health of a web resource.

import json
import time
import urllib.request

URL = "https://www.youtube.com"

import json

# def lambda_handler(event, context):
    # obtain 3 metrixs for a web resource
    # select a web resource


def lambda_handler(event, context):
    print("Hello from Lambda!")

    # This function checks the availability and latency of a web resource
    try:
        start_time = time.time()
        response = urllib.request.urlopen(URL, timeout=5)
        latency_ms = (time.time() - start_time) * 1000
        availability = 1 if response.status == 200 else 0
        message = {
            "availability": availability,
            "latency_ms": latency_ms,
            "status_code": response.status
        }
    except Exception as e:
        message = {
            "availability": 0,
            "latency_ms": 0,
            "status_code": None,
            "error": str(e)
        }
    print(message) # prints the message when on lambda server
    return {
        'statusCode': 200, # HTTP status code 200 means server runs with no errors
        'body': json.dumps(message)
    }
