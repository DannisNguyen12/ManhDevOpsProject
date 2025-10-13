import pytest
import json
from unittest.mock import patch, MagicMock


class TestMonitorIntegration:
    """Integration tests for monitor Lambda functionality"""

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_monitor_lambda_with_websites(self, mock_cloudwatch, mock_dynamodb):
        """Test monitor Lambda with available websites"""
        from modules.monitor.monitor import lambda_handler

        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Mock CloudWatch client
        mock_cloudwatch_client = MagicMock()
        mock_cloudwatch.return_value = mock_cloudwatch_client

        # Mock website data
        mock_table.scan.return_value = {
            'Items': [
                {
                    'id': 'site1',
                    'name': 'Test Site 1',
                    'url': 'https://httpbin.org/status/200',
                    'enabled': True
                }
            ]
        }

        # Mock requests for website checking
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.5
            mock_get.return_value = mock_response

            # Mock BeautifulSoup for crawling
            with patch('modules.monitor.monitor.BeautifulSoup') as mock_bs:
                mock_soup = MagicMock()
                mock_soup.title.string = 'Test Page'
                mock_soup.get_text.return_value = 'Test content with words'
                mock_soup.find_all.return_value = []
                mock_bs.return_value = mock_soup

                # Call the lambda handler
                result = lambda_handler({}, None)

                # Verify response
                assert result['statusCode'] == 200
                response_body = json.loads(result['body'])
                assert 'Successfully processed' in response_body['message']
                assert response_body['crawl_results_count'] >= 0
                assert response_body['monitor_results_count'] >= 0

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_monitor_lambda_no_websites(self, mock_cloudwatch, mock_dynamodb):
        """Test monitor Lambda when no websites are available"""
        from modules.monitor.monitor import lambda_handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        mock_cloudwatch_client = MagicMock()
        mock_cloudwatch.return_value = mock_cloudwatch_client

        # Mock empty scan result
        mock_table.scan.return_value = {'Items': []}

        result = lambda_handler({}, None)

        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'No websites to monitor' in response_body['message']

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_monitor_lambda_alarm_creation(self, mock_cloudwatch, mock_dynamodb):
        """Test that alarms are created for websites"""
        from modules.monitor.monitor import lambda_handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        mock_cloudwatch_client = MagicMock()
        mock_cloudwatch.return_value = mock_cloudwatch_client

        # Mock website data
        mock_table.scan.return_value = {
            'Items': [
                {
                    'id': 'test-site',
                    'name': 'TestSite',
                    'url': 'https://example.com',
                    'enabled': True
                }
            ]
        }

        # Mock describe_alarms to return no existing alarms
        mock_cloudwatch_client.describe_alarms.return_value = {'MetricAlarms': []}

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_get.return_value = mock_response

            with patch('modules.monitor.monitor.BeautifulSoup') as mock_bs:
                mock_soup = MagicMock()
                mock_soup.title.string = 'Test'
                mock_soup.get_text.return_value = 'content'
                mock_soup.find_all.return_value = []
                mock_bs.return_value = mock_soup

                lambda_handler({}, None)

                # Verify that put_metric_alarm was called for both availability and latency
                assert mock_cloudwatch_client.put_metric_alarm.call_count == 2

                # Check the alarm names
                calls = mock_cloudwatch_client.put_metric_alarm.call_args_list
                alarm_names = [call[1]['AlarmName'] for call in calls]
                assert 'TestSite-Availability' in alarm_names
                assert 'TestSite-Latency' in alarm_names

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_monitor_lambda_disabled_websites_filtered(self, mock_cloudwatch, mock_dynamodb):
        """Test that disabled websites are filtered out"""
        from modules.monitor.monitor import lambda_handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        mock_cloudwatch_client = MagicMock()
        mock_cloudwatch.return_value = mock_cloudwatch_client

        # Mock websites with mixed enabled status
        mock_table.scan.return_value = {
            'Items': [
                {'id': 'enabled-site', 'name': 'Enabled', 'url': 'https://enabled.com', 'enabled': True},
                {'id': 'disabled-site', 'name': 'Disabled', 'url': 'https://disabled.com', 'enabled': False},
                {'id': 'default-site', 'name': 'Default', 'url': 'https://default.com'}  # No enabled field
            ]
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_get.return_value = mock_response

            with patch('modules.monitor.monitor.BeautifulSoup') as mock_bs:
                mock_soup = MagicMock()
                mock_soup.title.string = 'Test'
                mock_soup.get_text.return_value = 'content'
                mock_soup.find_all.return_value = []
                mock_bs.return_value = mock_soup

                result = lambda_handler({}, None)

                # Should only process 2 websites (enabled and default)
                response_body = json.loads(result['body'])
                assert response_body['crawl_results_count'] == 2
                assert response_body['monitor_results_count'] == 2

    @patch('modules.monitor.monitor.dynamodb')
    @patch('modules.monitor.monitor.cloudwatch')
    def test_monitor_lambda_metrics_sent(self, mock_cloudwatch, mock_dynamodb):
        """Test that CloudWatch metrics are sent correctly"""
        from modules.monitor.monitor import lambda_handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        mock_cloudwatch_client = MagicMock()
        mock_cloudwatch.return_value = mock_cloudwatch_client

        mock_table.scan.return_value = {
            'Items': [{'id': 'test', 'name': 'Test', 'url': 'https://example.com', 'enabled': True}]
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.elapsed.total_seconds.return_value = 1.5  # 1.5 seconds = 1500ms
            mock_get.return_value = mock_response

            with patch('modules.monitor.monitor.BeautifulSoup') as mock_bs:
                mock_soup = MagicMock()
                mock_soup.title.string = 'Test'
                mock_soup.get_text.return_value = 'content'
                mock_soup.find_all.return_value = []
                mock_bs.return_value = mock_soup

                lambda_handler({}, None)

                # Verify put_metric_data was called
                mock_cloudwatch_client.put_metric_data.assert_called()

                # Check the metrics data
                call_args = mock_cloudwatch_client.put_metric_data.call_args
                metrics_data = call_args[1]['MetricData']

                # Should have Availability, Latency, and StatusCode metrics
                metric_names = [m['MetricName'] for m in metrics_data]
                assert 'Availability' in metric_names
                assert 'Latency' in metric_names
                assert 'StatusCode' in metric_names

                # Check dimensions are set correctly
                availability_metric = next(m for m in metrics_data if m['MetricName'] == 'Availability')
                assert availability_metric['Value'] == 1  # Success
                assert len(availability_metric['Dimensions']) == 2