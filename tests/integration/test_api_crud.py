import pytest
import json
from modules.api.api_handler import validate_website


def test_create_website_validation():
    """Test website creation validation"""
    # Test valid website
    website = {"name": "Test Site", "url": "https://example.com"}
    error = validate_website(website)
    assert error is None

    # Test invalid website
    invalid_website = {"name": "Test Site", "url": "invalid-url"}
    error = validate_website(invalid_website)
    assert error == "URL must start with http:// or https://"