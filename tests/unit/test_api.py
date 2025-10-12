import pytest
import json
import boto3
from moto import mock_dynamodb
import os
from unittest.mock import patch
from modules.api_handler import handler

TEST_WEBSITE = {
    'name': 'Test Site',
    'url': 'https://facebook.com',
    'crawlEnabled': True,
    'crawlInterval': 300,
    'selectors': {
        'title': 'title',
        'content': '.content'
    }
}

TEST_CRAWL_RESULT = {
    'target_id': 'test-id',
    'crawl_timestamp': '2024-01-15T10:30:00Z',
    'statusCode': 200,
    'responseTime': 150,
    'contentLength': 1024,
    'title': 'Test Page Title',
    'content': 'Test page content...',
    'error': None
}

@pytest.fixture
def api_event():
    """Base API Gateway event"""
    return {
        'httpMethod': 'GET',
        'headers': {},
        'pathParameters': None,
        'queryStringParameters': None,
        'body': None,
        'resource': '/websites'
    }

@pytest.fixture
def dynamodb_tables():
    """Set up mock DynamoDB tables"""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb')

        # Create websites table
        websites_table = dynamodb.create_table(
            TableName='WebsiteConfigTable',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create crawl results table
        crawl_results_table = dynamodb.create_table(
            TableName='CrawlResultsTable',
            KeySchema=[
                {'AttributeName': 'target_id', 'KeyType': 'HASH'},
                {'AttributeName': 'crawl_timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'target_id', 'AttributeType': 'S'},
                {'AttributeName': 'crawl_timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        os.environ['CONFIG_TABLE'] = 'WebsiteConfigTable'
        os.environ['CRAWL_RESULTS_TABLE'] = 'CrawlResultsTable'

        yield {'websites': websites_table, 'crawl_results': crawl_results_table}

class TestApiHandler:
    def test_create_website(self, api_event, dynamodb_tables):
        """Test POST /websites"""
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/websites'
        api_event['body'] = json.dumps(TEST_WEBSITE)

        response = handler(api_event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['name'] == TEST_WEBSITE['name']
        assert body['url'] == TEST_WEBSITE['url']
        assert body['crawlEnabled'] == TEST_WEBSITE['crawlEnabled']
        assert 'id' in body

    def test_get_website(self, api_event, dynamodb_tables):
        """Test GET /websites/{id}"""
        # First create a website
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/websites'
        api_event['body'] = json.dumps(TEST_WEBSITE)
        create_response = handler(api_event, None)
        website_id = json.loads(create_response['body'])['id']

        # Then get it
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/websites/{websiteId}'
        api_event['pathParameters'] = {'websiteId': website_id}
        api_event['body'] = None

        response = handler(api_event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['name'] == TEST_WEBSITE['name']
        assert body['url'] == TEST_WEBSITE['url']

    def test_list_websites(self, api_event, dynamodb_tables):
        """Test GET /websites"""
        # Create multiple websites
        websites = [
            {'name': f'Site {i}', 'url': f'https://example{i}.com', 'crawlEnabled': True}
            for i in range(3)
        ]

        for website in websites:
            api_event['httpMethod'] = 'POST'
            api_event['resource'] = '/websites'
            api_event['body'] = json.dumps(website)
            handler(api_event, None)

        # List all websites
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/websites'
        api_event['pathParameters'] = None
        api_event['body'] = None

        response = handler(api_event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body) == 3

    def test_update_website(self, api_event, dynamodb_tables):
        """Test PUT /websites/{id}"""
        # First create a website
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/websites'
        api_event['body'] = json.dumps(TEST_WEBSITE)
        create_response = handler(api_event, None)
        website_id = json.loads(create_response['body'])['id']

        # Then update it
        updated_data = {
            'name': 'Updated Site',
            'url': 'https://updated-example.com',
            'crawlEnabled': False
        }

        api_event['httpMethod'] = 'PUT'
        api_event['resource'] = '/websites/{websiteId}'
        api_event['pathParameters'] = {'websiteId': website_id}
        api_event['body'] = json.dumps(updated_data)

        response = handler(api_event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['name'] == updated_data['name']
        assert body['url'] == updated_data['url']
        assert body['crawlEnabled'] == updated_data['crawlEnabled']

    def test_delete_website(self, api_event, dynamodb_tables):
        """Test DELETE /websites/{id}"""
        # First create a website
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/websites'
        api_event['body'] = json.dumps(TEST_WEBSITE)
        create_response = handler(api_event, None)
        website_id = json.loads(create_response['body'])['id']

        # Then delete it
        api_event['httpMethod'] = 'DELETE'
        api_event['resource'] = '/websites/{websiteId}'
        api_event['pathParameters'] = {'websiteId': website_id}
        api_event['body'] = None

        response = handler(api_event, None)

        assert response['statusCode'] == 204

        # Verify it's gone
        api_event['httpMethod'] = 'GET'
        response = handler(api_event, None)
        assert response['statusCode'] == 404

    def test_create_crawl_result(self, api_event, dynamodb_tables):
        """Test POST /crawl-results"""
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/crawl-results'
        api_event['body'] = json.dumps(TEST_CRAWL_RESULT)

        response = handler(api_event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['target_id'] == TEST_CRAWL_RESULT['target_id']
        assert body['statusCode'] == TEST_CRAWL_RESULT['statusCode']

    def test_get_crawl_result(self, api_event, dynamodb_tables):
        """Test GET /crawl-results/{resultId}"""
        # First create a crawl result
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/crawl-results'
        api_event['body'] = json.dumps(TEST_CRAWL_RESULT)
        handler(api_event, None)

        # Then get it
        result_id = f"{TEST_CRAWL_RESULT['target_id']}:{TEST_CRAWL_RESULT['crawl_timestamp']}"
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/crawl-results/{resultId}'
        api_event['pathParameters'] = {'resultId': result_id}
        api_event['body'] = None

        response = handler(api_event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['target_id'] == TEST_CRAWL_RESULT['target_id']

    def test_list_crawl_results(self, api_event, dynamodb_tables):
        """Test GET /crawl-results"""
        # Create multiple crawl results
        results = []
        for i in range(3):
            result = TEST_CRAWL_RESULT.copy()
            result['target_id'] = f'test-{i}'
            result['crawl_timestamp'] = f'2024-01-15T10:{30+i}:00Z'
            results.append(result)

        for result in results:
            api_event['httpMethod'] = 'POST'
            api_event['resource'] = '/crawl-results'
            api_event['body'] = json.dumps(result)
            handler(api_event, None)

        # List all results
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/crawl-results'
        api_event['pathParameters'] = None
        api_event['body'] = None

        response = handler(api_event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body) == 3

    @patch('modules.api_handler.lambda_client')
    def test_get_crawler_status(self, mock_lambda_client, api_event, dynamodb_tables):
        """Test GET /crawler/status"""
        # Mock Lambda client
        mock_lambda_client.invoke = patch('boto3.client').return_value

        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/crawler/status'

        response = handler(api_event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'total_targets' in body
        assert 'recent_crawls' in body

    @patch('modules.api_handler.lambda_client')
    def test_start_crawler(self, mock_lambda_client, api_event, dynamodb_tables):
        """Test POST /crawler/start"""
        # Mock Lambda invoke
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}

        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/crawler/start'

        response = handler(api_event, None)

        assert response['statusCode'] == 202
        body = json.loads(response['body'])
        assert 'message' in body

    def test_website_validation(self, api_event, dynamodb_tables):
        """Test website validation"""
        # Test missing name
        invalid_website = {'url': 'https://example.com'}
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/websites'
        api_event['body'] = json.dumps(invalid_website)

        response = handler(api_event, None)
        assert response['statusCode'] == 400

        # Test invalid URL
        invalid_website = {'name': 'Test', 'url': 'invalid-url'}
        api_event['body'] = json.dumps(invalid_website)

        response = handler(api_event, None)
        assert response['statusCode'] == 400

    def test_invalid_endpoint(self, api_event, dynamodb_tables):
        """Test invalid endpoint"""
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/invalid'

        response = handler(api_event, None)
        assert response['statusCode'] == 400

@pytest.mark.integration
class TestApiIntegration:
    def test_complete_website_crud_cycle(self, api_event, dynamodb_tables):
        """Test complete CRUD cycle for websites"""
        # Create
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/websites'
        api_event['body'] = json.dumps(TEST_WEBSITE)
        create_response = handler(api_event, None)
        assert create_response['statusCode'] == 201
        website_id = json.loads(create_response['body'])['id']

        # Read
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/websites/{websiteId}'
        api_event['pathParameters'] = {'websiteId': website_id}
        read_response = handler(api_event, None)
        assert read_response['statusCode'] == 200

        # Update
        updated_data = {
            'name': 'Updated Site',
            'url': 'https://updated-example.com',
            'crawlEnabled': False
        }
        api_event['httpMethod'] = 'PUT'
        api_event['body'] = json.dumps(updated_data)
        update_response = handler(api_event, None)
        assert update_response['statusCode'] == 200

        # Delete
        api_event['httpMethod'] = 'DELETE'
        api_event['body'] = None
        delete_response = handler(api_event, None)
        assert delete_response['statusCode'] == 204

    def test_crawl_results_workflow(self, api_event, dynamodb_tables):
        """Test crawl results CRUD operations"""
        # Create crawl result
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/crawl-results'
        api_event['body'] = json.dumps(TEST_CRAWL_RESULT)
        create_response = handler(api_event, None)
        assert create_response['statusCode'] == 201

        # List results
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/crawl-results'
        api_event['pathParameters'] = None
        list_response = handler(api_event, None)
        assert list_response['statusCode'] == 200
        assert len(json.loads(list_response['body'])) == 1

        # Get specific result
        result_id = f"{TEST_CRAWL_RESULT['target_id']}:{TEST_CRAWL_RESULT['crawl_timestamp']}"
        api_event['resource'] = '/crawl-results/{resultId}'
        api_event['pathParameters'] = {'resultId': result_id}
        get_response = handler(api_event, None)
        assert get_response['statusCode'] == 200

        # Delete result
        api_event['httpMethod'] = 'DELETE'
        delete_response = handler(api_event, None)
        assert delete_response['statusCode'] == 204

    @patch('modules.api_handler.lambda_client')
    def test_crawler_management_integration(self, mock_lambda_client, api_event, dynamodb_tables):
        """Test crawler status and control integration"""
        # Mock Lambda client
        mock_lambda_client.invoke.return_value = {'StatusCode': 202}

        # Test status endpoint
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/crawler/status'
        api_event['pathParameters'] = None
        status_response = handler(api_event, None)
        assert status_response['statusCode'] == 200

        # Test start endpoint
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/crawler/start'
        start_response = handler(api_event, None)
        assert start_response['statusCode'] == 202

    def test_bulk_operations_performance(self, api_event, dynamodb_tables):
        """Test performance with bulk operations"""
        import time

        # Create multiple websites
        start_time = time.time()
        websites = []
        for i in range(10):
            api_event['httpMethod'] = 'POST'
            api_event['resource'] = '/websites'
            api_event['body'] = json.dumps({
                'name': f'Bulk Site {i}',
                'url': f'https://bulk-example{i}.com',
                'crawlEnabled': True
            })
            response = handler(api_event, None)
            websites.append(json.loads(response['body']))
        create_time = time.time() - start_time

        # Bulk read
        start_time = time.time()
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/websites'
        api_event['pathParameters'] = None
        handler(api_event, None)
        read_time = time.time() - start_time

        # Assess performance
        assert create_time < 5  # Should create 10 items in under 5 seconds
        assert read_time < 1    # Should read all items in under 1 second

    def test_error_handling_and_edge_cases(self, api_event, dynamodb_tables):
        """Test error handling and edge cases"""
        # Test non-existent website
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/websites/{websiteId}'
        api_event['pathParameters'] = {'websiteId': 'non-existent'}
        response = handler(api_event, None)
        assert response['statusCode'] == 404

        # Test non-existent crawl result
        api_event['resource'] = '/crawl-results/{resultId}'
        api_event['pathParameters'] = {'resultId': 'non-existent:timestamp'}
        response = handler(api_event, None)
        assert response['statusCode'] == 404

        # Test invalid HTTP method
        api_event['httpMethod'] = 'PATCH'
        api_event['resource'] = '/websites'
        response = handler(api_event, None)
        assert response['statusCode'] == 400

        # Test malformed JSON
        api_event['httpMethod'] = 'POST'
        api_event['body'] = 'invalid json'
        response = handler(api_event, None)
        assert response['statusCode'] == 500