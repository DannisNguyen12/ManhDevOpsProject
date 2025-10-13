import pytest
import json
from unittest.mock import patch, MagicMock


class TestAlarmHandler:
    """Unit tests for alarm handler message parsing"""

    @patch('modules.alarm.alarm_handler.dynamodb')
    def test_lambda_handler_successful_parsing(self, mock_dynamodb):
        """Test successful alarm message parsing and storage"""
        from modules.alarm.alarm_handler import lambda_handler

        # Mock DynamoDB table
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Sample SNS alarm message
        alarm_message = {
            'AlarmName': 'TestWebsite-Availability',
            'AlarmDescription': 'Test alarm description',
            'NewStateValue': 'ALARM',
            'NewStateReason': 'Threshold Crossed',
            'Region': 'us-east-1'
        }

        event = {
            'Records': [{
                'Sns': {
                    'Message': json.dumps(alarm_message),
                    'Subject': 'ALARM: TestWebsite-Availability',
                    'Timestamp': '2025-01-15T10:00:00.000Z'
                }
            }]
        }

        # Call the handler
        result = lambda_handler(event, None)

        # Verify the response
        assert result['statusCode'] == 200
        assert 'Alarm processing complete' in result['body']

        # Verify DynamoDB put_item was called
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']

        # Verify parsed data
        assert call_args['alarm_name'] == 'TestWebsite-Availability'
        assert call_args['website'] == 'Availability'  # Parsed from alarm name
        assert call_args['metric_type'] == 'availability'
        assert call_args['state'] == 'ALARM'
        assert call_args['region'] == 'us-east-1'

    @patch('modules.alarm.alarm_handler.dynamodb')
    def test_lambda_handler_latency_alarm(self, mock_dynamodb):
        """Test parsing of latency alarm messages"""
        from modules.alarm.alarm_handler import lambda_handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        alarm_message = {
            'AlarmName': 'Google-Latency',
            'NewStateValue': 'OK',
            'Region': 'us-west-2'
        }

        event = {
            'Records': [{
                'Sns': {
                    'Message': json.dumps(alarm_message),
                    'Subject': 'OK: Google-Latency',
                    'Timestamp': '2025-01-15T11:00:00.000Z'
                }
            }]
        }

        result = lambda_handler(event, None)

        assert result['statusCode'] == 200
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']

        assert call_args['metric_type'] == 'latency'
        assert call_args['website'] == 'Latency'
        assert call_args['state'] == 'OK'

    @patch('modules.alarm.alarm_handler.dynamodb')
    def test_lambda_handler_malformed_message(self, mock_dynamodb):
        """Test handling of malformed alarm messages"""
        from modules.alarm.alarm_handler import lambda_handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Malformed message without proper JSON
        event = {
            'Records': [{
                'Sns': {
                    'Message': 'not-json',
                    'Subject': 'Test Subject',
                    'Timestamp': '2025-01-15T12:00:00.000Z'
                }
            }]
        }

        result = lambda_handler(event, None)

        # Should still return success but with default values
        assert result['statusCode'] == 200
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']

        assert call_args['alarm_name'] == ''
        assert call_args['website'] == 'Unknown'
        assert call_args['metric_type'] == 'unknown'

    @patch('modules.alarm.alarm_handler.dynamodb')
    def test_lambda_handler_multiple_records(self, mock_dynamodb):
        """Test processing multiple SNS records"""
        from modules.alarm.alarm_handler import lambda_handler

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        event = {
            'Records': [
                {
                    'Sns': {
                        'Message': json.dumps({'AlarmName': 'Site1-Availability'}),
                        'Subject': 'ALARM: Site1-Availability',
                        'Timestamp': '2025-01-15T10:00:00.000Z'
                    }
                },
                {
                    'Sns': {
                        'Message': json.dumps({'AlarmName': 'Site2-Latency'}),
                        'Subject': 'OK: Site2-Latency',
                        'Timestamp': '2025-01-15T11:00:00.000Z'
                    }
                }
            ]
        }

        result = lambda_handler(event, None)

        assert result['statusCode'] == 200
        # Should have called put_item twice
        assert mock_table.put_item.call_count == 2