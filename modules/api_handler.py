import json
import os
import boto3
import uuid
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
table = dynamodb.Table(os.environ['CONFIG_TABLE'])
crawl_results_table = dynamodb.Table(os.environ['CRAWL_RESULTS_TABLE'])

def create_response(status_code: int, body: Any) -> Dict:
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def validate_website(website: Dict) -> Optional[str]:
    """Validate website data"""
    required_fields = ['name', 'url']
    for field in required_fields:
        if field not in website:
            return f"Missing required field: {field}"

    if not website['url'].startswith(('http://', 'https://')):
        return "URL must start with http:// or https://"

    return None

def create_website(event):
    """Create new website entry"""
    try:
        website = json.loads(event['body'])

        # Validate input
        error = validate_website(website)
        if error:
            return create_response(400, {'error': error})

        # Add metadata
        website['id'] = str(uuid.uuid4())
        website['createdAt'] = datetime.utcnow().isoformat()
        website['updatedAt'] = website['createdAt']

        # Save to DynamoDB
        table.put_item(Item=website)

        return create_response(201, website)

    except Exception as e:
        logger.error(f"Error creating website: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def get_website(event):
    """Get website by ID"""
    try:
        website_id = event['pathParameters']['websiteId']

        response = table.get_item(Key={'id': website_id})

        if 'Item' not in response:
            return create_response(404, {'error': 'Website not found'})

        return create_response(200, response['Item'])

    except Exception as e:
        logger.error(f"Error getting website: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def list_websites(event):
    """List all websites"""
    try:
        response = table.scan()
        return create_response(200, response.get('Items', []))

    except Exception as e:
        logger.error(f"Error listing websites: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def update_website(event):
    """Update website by ID"""
    try:
        website_id = event['pathParameters']['websiteId']
        updates = json.loads(event['body'])

        # Validate input
        error = validate_website(updates)
        if error:
            return create_response(400, {'error': error})

        # Check if website exists
        response = table.get_item(Key={'id': website_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Website not found'})

        # Update metadata
        updates['id'] = website_id
        updates['updatedAt'] = datetime.utcnow().isoformat()
        updates['createdAt'] = response['Item']['createdAt']

        # Save to DynamoDB
        table.put_item(Item=updates)

        return create_response(200, updates)

    except Exception as e:
        logger.error(f"Error updating website: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def delete_website(event):
    """Delete website by ID"""
    try:
        website_id = event['pathParameters']['websiteId']

        # Check if website exists
        response = table.get_item(Key={'id': website_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Website not found'})

        # Delete from DynamoDB
        table.delete_item(Key={'id': website_id})

        return create_response(204, {})

    except Exception as e:
        logger.error(f"Error deleting website: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

# Crawl Results Handlers
def list_crawl_results(event):
    """List all crawl results"""
    try:
        # Optional query parameters for filtering
        target_id = event.get('queryStringParameters', {}).get('target_id')
        limit = int(event.get('queryStringParameters', {}).get('limit', '100'))

        if target_id:
            # Query by target_id
            response = crawl_results_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('target_id').eq(target_id),
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
        else:
            # Scan all results (less efficient, but for demo)
            response = crawl_results_table.scan(Limit=limit)

        return create_response(200, response.get('Items', []))

    except Exception as e:
        logger.error(f"Error listing crawl results: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def create_crawl_result(event):
    """Create a new crawl result (used by crawler Lambda)"""
    try:
        result = json.loads(event['body'])

        # Validate required fields
        required_fields = ['target_id', 'crawl_timestamp', 'url']
        for field in required_fields:
            if field not in result:
                return create_response(400, {'error': f'Missing required field: {field}'})

        # Add timestamp if not provided
        if 'ttl' not in result:
            result['ttl'] = int(time.time()) + (30 * 24 * 60 * 60)  # 30 days

        # Save to DynamoDB
        crawl_results_table.put_item(Item=result)

        return create_response(201, result)

    except Exception as e:
        logger.error(f"Error creating crawl result: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def get_crawl_result(event):
    """Get a specific crawl result"""
    try:
        result_id = event['pathParameters']['resultId']

        # Parse result_id as target_id:crawl_timestamp
        if ':' not in result_id:
            return create_response(400, {'error': 'Invalid result ID format. Use target_id:crawl_timestamp'})

        target_id, crawl_timestamp = result_id.split(':', 1)

        response = crawl_results_table.get_item(
            Key={'target_id': target_id, 'crawl_timestamp': crawl_timestamp}
        )

        if 'Item' not in response:
            return create_response(404, {'error': 'Crawl result not found'})

        return create_response(200, response['Item'])

    except Exception as e:
        logger.error(f"Error getting crawl result: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def delete_crawl_result(event):
    """Delete a crawl result"""
    try:
        result_id = event['pathParameters']['resultId']

        # Parse result_id as target_id:crawl_timestamp
        if ':' not in result_id:
            return create_response(400, {'error': 'Invalid result ID format. Use target_id:crawl_timestamp'})

        target_id, crawl_timestamp = result_id.split(':', 1)

        # Check if exists
        response = crawl_results_table.get_item(
            Key={'target_id': target_id, 'crawl_timestamp': crawl_timestamp}
        )
        if 'Item' not in response:
            return create_response(404, {'error': 'Crawl result not found'})

        # Delete
        crawl_results_table.delete_item(
            Key={'target_id': target_id, 'crawl_timestamp': crawl_timestamp}
        )

        return create_response(204, {})

    except Exception as e:
        logger.error(f"Error deleting crawl result: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

# Crawler Management Handlers
def get_crawler_status(event):
    """Get crawler status and statistics"""
    try:
        # Get target count
        targets_response = table.scan(Select='COUNT')
        target_count = targets_response['Count']

        # Get recent crawl results count
        recent_time = str(int(time.time()) - (24 * 60 * 60))  # Last 24 hours
        results_response = crawl_results_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('crawl_timestamp').gt(recent_time)
        )
        recent_results_count = len(results_response.get('Items', []))

        status = {
            'total_targets': target_count,
            'recent_crawls': recent_results_count,
            'last_updated': datetime.utcnow().isoformat(),
            'status': 'active' if target_count > 0 else 'idle'
        }

        return create_response(200, status)

    except Exception as e:
        logger.error(f"Error getting crawler status: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def start_crawler(event):
    """Manually trigger the crawler Lambda"""
    try:
        # Invoke the crawler Lambda function
        lambda_client.invoke(
            FunctionName=os.environ.get('CRAWLER_FUNCTION_NAME', 'WebCrawlerFunction'),
            InvocationType='Event',  # Asynchronous
            Payload=json.dumps({})
        )

        return create_response(202, {
            'message': 'Crawler started successfully',
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Error starting crawler: {str(e)}")
        return create_response(500, {'error': 'Failed to start crawler'})

def handler(event, context):
    """Main Lambda handler"""
    logger.info(f"Processing event: {json.dumps(event)}")

    method = event['httpMethod']
    path = event.get('resource', event.get('path', ''))
    has_id = event.get('pathParameters', {}) and ('websiteId' in event['pathParameters'] or 'resultId' in event['pathParameters'])

    # Route request to appropriate handler
    if path.startswith('/websites'):
        if method == 'POST' and not has_id:
            return create_website(event)
        elif method == 'GET' and has_id:
            return get_website(event)
        elif method == 'GET' and not has_id:
            return list_websites(event)
        elif method == 'PUT' and has_id:
            return update_website(event)
        elif method == 'DELETE' and has_id:
            return delete_website(event)

    elif path.startswith('/crawl-results'):
        if method == 'POST' and not has_id:
            return create_crawl_result(event)
        elif method == 'GET' and has_id:
            return get_crawl_result(event)
        elif method == 'GET' and not has_id:
            return list_crawl_results(event)
        elif method == 'DELETE' and has_id:
            return delete_crawl_result(event)

    elif path.startswith('/crawler'):
        if path.endswith('/status') and method == 'GET':
            return get_crawler_status(event)
        elif path.endswith('/start') and method == 'POST':
            return start_crawler(event)

    # Default fallback
    return create_response(400, {'error': 'Invalid request'})