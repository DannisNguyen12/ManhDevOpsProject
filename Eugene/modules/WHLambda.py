## Web Health Lambda Function
# This Lambda function is designed to monitor the health of a web resource.

import json
import time
import urllib.request
from publish_metric import publish

URLS = [
    "https://www.youtube.com",
    "https://www.google.com",
    "https://www.facebook.com",
]
URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
URL_MONITOR_MEMORY = "Memory" # user package, pre defined names spaces include lambda, it calculculates how much power it consumes
URL_NAMESPACE = "EUGENEPROJECT_WSU2025"


# def lambda_handler(event, context):
    # obtain 3 metrixs for a web resource
    # select a web resource


def lambda_handler(event, context):
    print("Hello from Lambda!")
    results = []
    
    for URL in URLS:
        try:
            start_time = time.time() # records request duration
            response = urllib.request.urlopen(URL, timeout = 5) # request fails if no response in 5 sec
            latency_ms = (time.time() - start_time) * 1000 # calculate latency in ms
        
            if response.status == 200: # check if website is available, 200 means success
                avail = 1 
            else:
                avail = 0

            latency = latency_ms
            message = {
                "url": URL,
                "availability": avail,
                "latency_ms": latency,
                "status_code": response.status
            }
        except Exception as e:
            availability = 0
            latency = 0
            message = {
                "availability": 0, # prints that website is not available
                "latency_ms": 0, # prints latency is 0, as no user input
                "status_code": None,
                "error": str(e)
            }
        print(f"Health check for {URL}: {message}")
        results.append(message)
        # defines dimension for cloud watch
        dimension = [{"Name": "URL", "Value": URL}]

        # Send metric
        response1 = publish(URL_NAMESPACE, URL_MONITOR_AVAILABILITY,dimension, avail)
        response2 = publish(URL_NAMESPACE, URL_MONITOR_LATENCY,dimension, latency)


    return {
        "statusCode": 200,
        "body": results
    }

