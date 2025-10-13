import pytest
from unittest.mock import patch, MagicMock


class TestURLValidation:
    """Unit tests for monitor URL validation functions"""

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_is_same_domain_same_domain(self, mock_cloudwatch, mock_dynamodb):
        """Test _is_same_domain with same domain URLs"""
        from modules.monitor.monitor import WebsiteMonitor

        monitor = WebsiteMonitor()
        assert monitor._is_same_domain('https://example.com', 'https://example.com/page') == True
        assert monitor._is_same_domain('https://example.com', 'https://example.com/subdomain/page') == True

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_is_same_domain_different_domain(self, mock_cloudwatch, mock_dynamodb):
        """Test _is_same_domain with different domain URLs"""
        from modules.monitor.monitor import WebsiteMonitor

        monitor = WebsiteMonitor()
        assert monitor._is_same_domain('https://example.com', 'https://other.com/page') == False
        assert monitor._is_same_domain('https://example.com', 'https://sub.example.org/page') == False

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_is_same_domain_invalid_urls(self, mock_cloudwatch, mock_dynamodb):
        """Test _is_same_domain with invalid URLs"""
        from modules.monitor.monitor import WebsiteMonitor

        monitor = WebsiteMonitor()
        assert monitor._is_same_domain('invalid-url', 'https://example.com') == False
        assert monitor._is_same_domain('https://example.com', 'invalid-url') == False

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_is_valid_url_valid_urls(self, mock_cloudwatch, mock_dynamodb):
        """Test _is_valid_url with valid URLs"""
        from modules.monitor.monitor import WebsiteMonitor

        monitor = WebsiteMonitor()
        assert monitor._is_valid_url('https://example.com') == True
        assert monitor._is_valid_url('http://example.com/page') == True
        assert monitor._is_valid_url('https://sub.example.com/path?query=value') == True

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_is_valid_url_invalid_urls(self, mock_cloudwatch, mock_dynamodb):
        """Test _is_valid_url with invalid URLs"""
        from modules.monitor.monitor import WebsiteMonitor

        monitor = WebsiteMonitor()
        assert monitor._is_valid_url('') == False
        assert monitor._is_valid_url('not-a-url') == False
        assert monitor._is_valid_url('#anchor') == False
        assert monitor._is_valid_url('ftp://example.com') == True  # This should be valid

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_is_valid_url_edge_cases(self, mock_cloudwatch, mock_dynamodb):
        """Test _is_valid_url with edge cases"""
        from modules.monitor.monitor import WebsiteMonitor

        monitor = WebsiteMonitor()
        assert monitor._is_valid_url('https://example.com#anchor') == True  # Should be valid, just anchor
        assert monitor._is_valid_url('https://') == True  # Minimal valid URL