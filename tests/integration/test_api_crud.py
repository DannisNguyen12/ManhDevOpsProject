import pytest
import json
from unittest.mock import patch, MagicMock


class TestAPICrudOperations:
    """Integration tests for API CRUD operations"""

    @patch('modules.api.api_handler.dynamodb')
    def test_create_website_success(self, mock_dynamodb):
        """Test successful website creation"""
        from modules.api.api_handler import handler

        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Test data
        website_data = {
            'name': 'Test Website',
            'url': 'https://example.com'
        }

        event = {
            'httpMethod': 'POST',
            'resource': '/websites',
            'body': json.dumps(website_data)
        }

        # Call the handler
        result = handler(event, None)

        # Verify response
        assert result['statusCode'] == 201
        response_body = json.loads(result['body'])

        assert response_body['name'] == 'Test Website'
        assert response_body['url'] == 'https://example.com'
        assert 'id' in response_body
        assert response_body['enabled'] == True
        assert 'createdAt' in response_body

        # Verify DynamoDB put_item was called
        mock_table.put_item.assert_called_once()

    @patch('modules.api.api_handler.dynamodb')
    def test_get_website_success(self, mock_dynamodb):
        """Test successful website retrieval"""
        from modules.api.api_handler import handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Mock the get_item response
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'test-id',
                'name': 'Test Website',
                'url': 'https://example.com',
                'enabled': True
            }
        }

        event = {
            'httpMethod': 'GET',
            'resource': '/websites/{websiteId}',
            'pathParameters': {'websiteId': 'test-id'}
        }

        result = handler(event, None)

        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['name'] == 'Test Website'
        assert response_body['id'] == 'test-id'

    @patch('modules.api.api_handler.dynamodb')
    def test_get_website_not_found(self, mock_dynamodb):
        """Test website retrieval when not found"""
        from modules.api.api_handler import handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Mock empty response (no Item)
        mock_table.get_item.return_value = {}

        event = {
            'httpMethod': 'GET',
            'resource': '/websites/{websiteId}',
            'pathParameters': {'websiteId': 'nonexistent-id'}
        }

        result = handler(event, None)

        assert result['statusCode'] == 404
        response_body = json.loads(result['body'])
        assert 'Website not found' in response_body['error']

    @patch('modules.api.api_handler.dynamodb')
    def test_list_websites_success(self, mock_dynamodb):
        """Test successful website listing"""
        from modules.api.api_handler import handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Mock scan response
        mock_table.scan.return_value = {
            'Items': [
                {'id': '1', 'name': 'Site 1', 'url': 'https://site1.com'},
                {'id': '2', 'name': 'Site 2', 'url': 'https://site2.com'}
            ]
        }

        event = {
            'httpMethod': 'GET',
            'resource': '/websites'
        }

        result = handler(event, None)

        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert len(response_body) == 2
        assert response_body[0]['name'] == 'Site 1'
        assert response_body[1]['name'] == 'Site 2'

    @patch('modules.api.api_handler.dynamodb')
    def test_update_website_success(self, mock_dynamodb):
        """Test successful website update"""
        from modules.api.api_handler import handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Mock existing item
        mock_table.get_item.return_value = {
            'Item': {
                'id': 'test-id',
                'name': 'Old Name',
                'url': 'https://old.com',
                'enabled': True
            }
        }

        update_data = {
            'name': 'Updated Name',
            'url': 'https://updated.com'
        }

        event = {
            'httpMethod': 'PUT',
            'resource': '/websites/{websiteId}',
            'pathParameters': {'websiteId': 'test-id'},
            'body': json.dumps(update_data)
        }

        result = handler(event, None)

        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['name'] == 'Updated Name'
        assert response_body['url'] == 'https://updated.com'
        assert 'updatedAt' in response_body

    @patch('modules.api.api_handler.dynamodb')
    def test_delete_website_success(self, mock_dynamodb):
        """Test successful website deletion"""
        from modules.api.api_handler import handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Mock existing item
        mock_table.get_item.return_value = {
            'Item': {'id': 'test-id', 'name': 'Test Site'}
        }

        event = {
            'httpMethod': 'DELETE',
            'resource': '/websites/{websiteId}',
            'pathParameters': {'websiteId': 'test-id'}
        }

        result = handler(event, None)

        assert result['statusCode'] == 204
        # Verify delete_item was called
        mock_table.delete_item.assert_called_once_with(Key={'id': 'test-id'})

    @patch('modules.api.api_handler.dynamodb')
    def test_invalid_request_method(self, mock_dynamodb):
        """Test handling of invalid request methods"""
        from modules.api.api_handler import handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        event = {
            'httpMethod': 'PATCH',
            'resource': '/websites'
        }

        result = handler(event, None)

        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'Invalid request' in response_body['error']