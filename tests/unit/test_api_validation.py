import pytest
import json
from unittest.mock import patch, MagicMock


class TestAPIValidation:
    """Unit tests for API handler validation functions"""

    @patch('modules.api.api_handler.dynamodb')
    def test_validate_website_valid_input(self, mock_dynamodb):
        """Test validation with valid website data"""
        # Import after patching
        from modules.api.api_handler import validate_website

        website = {
            'name': 'Test Website',
            'url': 'https://example.com'
        }
        result = validate_website(website)
        assert result is None

    @patch('modules.api.api_handler.dynamodb')
    def test_validate_website_missing_name(self, mock_dynamodb):
        """Test validation with missing name field"""
        from modules.api.api_handler import validate_website

        website = {
            'url': 'https://example.com'
        }
        result = validate_website(website)
        assert result == "Missing required field: name"

    @patch('modules.api.api_handler.dynamodb')
    def test_validate_website_missing_url(self, mock_dynamodb):
        """Test validation with missing URL field"""
        from modules.api.api_handler import validate_website

        website = {
            'name': 'Test Website'
        }
        result = validate_website(website)
        assert result == "Missing required field: url"

    @patch('modules.api.api_handler.dynamodb')
    def test_validate_website_invalid_url(self, mock_dynamodb):
        """Test validation with invalid URL format"""
        from modules.api.api_handler import validate_website

        website = {
            'name': 'Test Website',
            'url': 'invalid-url'
        }
        result = validate_website(website)
        assert result == "URL must start with http:// or https://"

    @patch('modules.api.api_handler.dynamodb')
    def test_validate_website_http_url(self, mock_dynamodb):
        """Test validation with HTTP URL"""
        from modules.api.api_handler import validate_website

        website = {
            'name': 'Test Website',
            'url': 'http://example.com'
        }
        result = validate_website(website)
        assert result is None

    @patch('modules.api.api_handler.dynamodb')
    def test_create_response_structure(self, mock_dynamodb):
        """Test create_response returns correct structure"""
        from modules.api.api_handler import create_response

        response = create_response(200, {'message': 'success'})

        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert json.loads(response['body']) == {'message': 'success'}