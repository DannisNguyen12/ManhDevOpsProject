import requests
import time



def lambda_handler(event, context):

    url = "https://westernsydney.edu.au"  
    start = time.time()
    
    try:
        response = requests.get(url, timeout=5)
        latency = time.time() - start
        status_code = response.status_code
        response_size = len(response.content) 
        
        return {
            "statusCode": status_code,
            "latency": latency,
            "responseSizeBytes": response_size
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "latency": None,
            "responseSizeBytes": 0,
            "error": str(e)
        }
