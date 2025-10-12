import pytest
import json
import boto3
from moto import mock_dynamodb, mock_lambda
import os
from unittest.mock import patch, MagicMock
import requests_mock
from modules.api_handler import handler
from modules.lambda_webcrawler import WebCrawler

TEST_WEBSITE = {
    'id': 'test-website-1',
    'name': 'Test Site',
    'url': 'https://httpbin.org/html',
    'crawlEnabled': True,
    'crawlInterval': 300,
    'selectors': {
        'title': 'h1',
        'content': 'p'
    }
}

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture
def dynamodb_setup(aws_credentials):
    """Set up mock DynamoDB tables for integration tests"""
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

        # Create events table
        events_table = dynamodb.create_table(
            TableName='EventsTable',
            KeySchema=[
                {'AttributeName': 'timestamp', 'KeyType': 'HASH'},
                {'AttributeName': 'website', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'website', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        os.environ['CONFIG_TABLE'] = 'WebsiteConfigTable'
        os.environ['CRAWL_RESULTS_TABLE'] = 'CrawlResultsTable'
        os.environ['EVENTS_TABLE'] = 'EventsTable'
        os.environ['TARGETS_TABLE'] = 'WebsiteConfigTable'

        yield {
            'websites': websites_table,
            'crawl_results': crawl_results_table,
            'events': events_table
        }

@pytest.fixture
def api_event():
    """Base API Gateway event for integration tests"""
    return {
        'httpMethod': 'GET',
        'headers': {},
        'pathParameters': None,
        'queryStringParameters': None,
        'body': None,
        'resource': '/websites'
    }

@pytest.mark.integration
class TestWebCrawlerIntegration:
    def test_full_crawling_workflow(self, dynamodb_setup):
        """Test complete web crawling workflow from target to results"""
        # Setup test website
        websites_table = dynamodb_setup['websites']
        websites_table.put_item(Item=TEST_WEBSITE)

        # Mock HTTP response
        with requests_mock.Mocker() as m:
            m.get('https://httpbin.org/html', text='''
            <html>
                <head><title>Test Page</title></head>
                <body>
                    <h1>Test Page Title</h1>
                    <p>This is test content for crawling.</p>
                </body>
            </html>
            ''')

            # Initialize crawler and run
            crawler = WebCrawler()
            targets = crawler.get_crawl_targets()
            assert len(targets) == 1

            # Crawl the website
            result = crawler.crawl_website(targets[0])
            assert result is not None
            assert result['statusCode'] == 200
            assert 'Test Page Title' in result['title']
            assert 'test content' in result['content']

    def test_crawler_with_multiple_targets(self, dynamodb_setup):
        """Test crawler handling multiple website targets"""
        websites_table = dynamodb_setup['websites']

        # Add multiple websites
        websites = []
        for i in range(3):
            website = TEST_WEBSITE.copy()
            website['id'] = f'test-website-{i}'
            website['url'] = f'https://httpbin.org/html{i}'
            websites.append(website)
            websites_table.put_item(Item=website)

        # Mock HTTP responses
        with requests_mock.Mocker() as m:
            for i, website in enumerate(websites):
                m.get(website['url'], text=f'''
                <html>
                    <head><title>Page {i}</title></head>
                    <body><h1>Title {i}</h1><p>Content {i}</p></body>
                </html>
                ''')

            # Run crawler
            crawler = WebCrawler()
            targets = crawler.get_crawl_targets()
            assert len(targets) == 3

            # Crawl all targets
            results = []
            for target in targets:
                result = crawler.crawl_website(target)
                assert result is not None
                results.append(result)

            assert len(results) == 3
            for i, result in enumerate(results):
                assert result['statusCode'] == 200
                assert f'Title {i}' in result['title']

    def test_crawler_error_handling(self, dynamodb_setup):
        """Test crawler error handling for failed requests"""
        websites_table = dynamodb_setup['websites']

        # Add website that will fail
        failing_website = TEST_WEBSITE.copy()
        failing_website['url'] = 'https://nonexistent.example.com'
        websites_table.put_item(Item=failing_website)

        # Mock network failure
        with requests_mock.Mocker() as m:
            m.get('https://nonexistent.example.com', exc=Exception('Connection failed'))

            crawler = WebCrawler()
            targets = crawler.get_crawl_targets()
            assert len(targets) == 1

            result = crawler.crawl_website(targets[0])
            assert result is not None
            assert result['statusCode'] == 0  # Error status
            assert result['error'] is not None

    def test_crawler_selectors_customization(self, dynamodb_setup):
        """Test crawler with custom CSS selectors"""
        websites_table = dynamodb_setup['websites']

        # Website with custom selectors
        custom_website = TEST_WEBSITE.copy()
        custom_website['selectors'] = {
            'title': 'h2.custom-title',
            'content': '.custom-content'
        }
        websites_table.put_item(Item=custom_website)

        # Mock response with custom elements
        with requests_mock.Mocker() as m:
            m.get('https://httpbin.org/html', text='''
            <html>
                <body>
                    <h2 class="custom-title">Custom Title</h2>
                    <div class="custom-content">Custom content here</div>
                    <h1>Wrong title</h1>
                    <p>Wrong content</p>
                </body>
            </html>
            ''')

            crawler = WebCrawler()
            targets = crawler.get_crawl_targets()
            result = crawler.crawl_website(targets[0])

            assert result is not None
            assert 'Custom Title' in result['title']
            assert 'Custom content here' in result['content']
            assert 'Wrong title' not in result['title']

    @mock_lambda
    def test_crawler_lambda_integration(self, dynamodb_setup):
        """Test crawler Lambda function end-to-end"""
        websites_table = dynamodb_setup['websites']
        websites_table.put_item(Item=TEST_WEBSITE)

        # Mock HTTP response
        with requests_mock.Mocker() as m:
            m.get('https://httpbin.org/html', text='''
            <html>
                <head><title>Lambda Test</title></head>
                <body><h1>Lambda Test Title</h1><p>Lambda test content</p></body>
            </html>
            ''')

            # Import and run the Lambda handler
            from modules.lambda_webcrawler import lambda_handler

            # Run the Lambda
            result = lambda_handler({}, None)

            # Verify results were stored
            crawl_results_table = dynamodb_setup['crawl_results']
            response = crawl_results_table.scan()
            items = response['Items']

            assert len(items) == 1
            item = items[0]
            assert item['statusCode'] == 200
            assert 'Lambda Test Title' in item['title']

@pytest.mark.integration
class TestApiCrawlerIntegration:
    def test_website_to_crawl_results_workflow(self, api_event, dynamodb_setup):
        """Test complete workflow from website creation to crawl results"""
        # Create website via API
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/websites'
        api_event['body'] = json.dumps({
            'name': 'Integration Test Site',
            'url': 'https://httpbin.org/html',
            'crawlEnabled': True,
            'selectors': {'title': 'h1', 'content': 'p'}
        })

        create_response = handler(api_event, None)
        assert create_response['statusCode'] == 201
        website_data = json.loads(create_response['body'])
        website_id = website_data['id']

        # Verify website was created
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/websites/{websiteId}'
        api_event['pathParameters'] = {'websiteId': website_id}
        get_response = handler(api_event, None)
        assert get_response['statusCode'] == 200

        # Simulate crawl result creation (normally done by crawler Lambda)
        crawl_result = {
            'target_id': website_id,
            'crawl_timestamp': '2024-01-15T10:30:00Z',
            'statusCode': 200,
            'responseTime': 150,
            'contentLength': 1024,
            'title': 'Integration Test Title',
            'content': 'Integration test content',
            'error': None
        }

        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/crawl-results'
        api_event['pathParameters'] = None
        api_event['body'] = json.dumps(crawl_result)

        crawl_create_response = handler(api_event, None)
        assert crawl_create_response['statusCode'] == 201

        # List crawl results
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/crawl-results'
        list_response = handler(api_event, None)
        assert list_response['statusCode'] == 200

        results = json.loads(list_response['body'])
        assert len(results) == 1
        assert results[0]['title'] == 'Integration Test Title'

    @patch('modules.api_handler.lambda_client')
    def test_crawler_control_integration(self, mock_lambda_client, api_event, dynamodb_setup):
        """Test crawler control via API"""
        # Mock Lambda invoke
        mock_lambda_client.invoke.return_value = {
            'StatusCode': 202,
            'Payload': json.dumps({'message': 'Success'})
        }

        # Test crawler status
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/crawler/status'
        status_response = handler(api_event, None)
        assert status_response['statusCode'] == 200

        # Test crawler start
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/crawler/start'
        start_response = handler(api_event, None)
        assert start_response['statusCode'] == 202

        # Verify Lambda was called
        mock_lambda_client.invoke.assert_called_once()

    def test_crawl_results_filtering(self, api_event, dynamodb_setup):
        """Test crawl results filtering by website ID"""
        crawl_results_table = dynamodb_setup['crawl_results']

        # Create multiple crawl results for different websites
        results = []
        for i in range(3):
            result = {
                'target_id': f'website-{i}',
                'crawl_timestamp': f'2024-01-15T10:{30+i}:00Z',
                'statusCode': 200,
                'responseTime': 100 + i * 10,
                'contentLength': 1000 + i * 100,
                'title': f'Title {i}',
                'content': f'Content {i}',
                'error': None
            }
            results.append(result)

            # Add via API
            api_event['httpMethod'] = 'POST'
            api_event['resource'] = '/crawl-results'
            api_event['body'] = json.dumps(result)
            handler(api_event, None)

        # Test filtering by website ID
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/crawl-results'
        api_event['queryStringParameters'] = {'target_id': 'website-1'}
        api_event['pathParameters'] = None

        filtered_response = handler(api_event, None)
        assert filtered_response['statusCode'] == 200

        filtered_results = json.loads(filtered_response['body'])
        assert len(filtered_results) == 1
        assert filtered_results[0]['target_id'] == 'website-1'

    def test_bulk_website_operations(self, api_event, dynamodb_setup):
        """Test bulk website creation and management"""
        # Create multiple websites
        websites = []
        for i in range(5):
            website = {
                'name': f'Bulk Test Site {i}',
                'url': f'https://bulk-test{i}.com',
                'crawlEnabled': True,
                'crawlInterval': 300,
                'selectors': {'title': 'h1', 'content': '.content'}
            }

            api_event['httpMethod'] = 'POST'
            api_event['resource'] = '/websites'
            api_event['body'] = json.dumps(website)
            response = handler(api_event, None)
            assert response['statusCode'] == 201

            website_data = json.loads(response['body'])
            websites.append(website_data)

        # List all websites
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/websites'
        api_event['pathParameters'] = None
        api_event['queryStringParameters'] = None

        list_response = handler(api_event, None)
        assert list_response['statusCode'] == 200

        all_websites = json.loads(list_response['body'])
        assert len(all_websites) == 5

        # Test individual updates
        for website in websites[:2]:  # Update first 2
            updated_data = website.copy()
            updated_data['crawlEnabled'] = False

            api_event['httpMethod'] = 'PUT'
            api_event['resource'] = '/websites/{websiteId}'
            api_event['pathParameters'] = {'websiteId': website['id']}
            api_event['body'] = json.dumps(updated_data)

            update_response = handler(api_event, None)
            assert update_response['statusCode'] == 200

    def test_error_scenarios_integration(self, api_event, dynamodb_setup):
        """Test error scenarios in integrated workflow"""
        # Test invalid website creation
        api_event['httpMethod'] = 'POST'
        api_event['resource'] = '/websites'
        api_event['body'] = json.dumps({
            'name': '',  # Invalid: empty name
            'url': 'not-a-url'  # Invalid: not a proper URL
        })

        response = handler(api_event, None)
        assert response['statusCode'] == 400

        # Test accessing non-existent resources
        api_event['httpMethod'] = 'GET'
        api_event['resource'] = '/websites/{websiteId}'
        api_event['pathParameters'] = {'websiteId': 'non-existent-id'}

        response = handler(api_event, None)
        assert response['statusCode'] == 404

        # Test invalid crawl result ID format
        api_event['resource'] = '/crawl-results/{resultId}'
        api_event['pathParameters'] = {'resultId': 'invalid-format'}

        response = handler(api_event, None)
        assert response['statusCode'] == 400