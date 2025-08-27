#!/usr/bin/env python3

"""
Test suite for the iracing_api module.
Tests authentication, API calls, and data formatting functionality.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime

# Add src directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import the classes/functions we want to test
from iracing_api import iRacingClient, iRacingAPIError

class TestiRacingAPI:
    """Test cases for the iRacing API wrapper"""

    def test_client_initialization_missing_credentials(self):
        """Test client initialization with missing environment variables"""
        # Mock os.environ to return None for credentials
        with patch('os.environ.get', side_effect=[None, None]):
            with pytest.raises(iRacingAPIError) as excinfo:
                iRacingClient()
            
            assert "iRacing credentials not found in environment variables" in str(excinfo.value)

    def test_client_initialization_with_credentials(self):
        """Test client initialization with valid environment variables"""
        # Mock os.environ to return valid credentials
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            # Mock irDataClient to avoid actual API calls
            with patch('iracing_api.irDataClient') as mock_client_class:
                # Configure the mock
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                mock_client_class.return_value = mock_client
                
                # This should not raise an exception
                client = iRacingClient()
                
                # Verify client was created with correct credentials
                mock_client_class.assert_called_once_with(username='test_user', password='test_pass')
                assert client.username == 'test_user'
                assert client.password == 'test_pass'

    def test_authenticate_success(self):
        """Test successful authentication"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                result = client.authenticate()
                
                assert result is True
                assert client.cust_id == 12345
                mock_client.member_info.assert_called_once()

    def test_authenticate_failure(self):
        """Test authentication failure due to missing cust_id"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {}  # Missing cust_id
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                result = client.authenticate()
                
                assert result is False
                assert client.cust_id is None

    def test_get_recent_races_success(self):
        """Test successful fetching of recent races"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                mock_client.stats_member_recent_races.return_value = {
                    'races': [
                        {
                            'subsession_id': 123,
                            'start_time': '2025-08-25 14:30:00',
                            'track_name': 'Daytona International Speedway',
                            'track_config': 'Road Course',
                            'car_name': 'Ford Mustang GT4',
                            'car_class': 'DPI',
                            'session_type_name': 'Official Race',
                            'num_drivers': 24,
                            'start_position': 5,
                            'finish_position': 3,
                            'irating_delta': 15,
                            'championship_points': 25
                        }
                    ]
                }
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                races = client.get_recent_races(12345)
                
                assert races is not None
                assert len(races) == 1
                assert races[0]['subsession_id'] == 123
                mock_client.stats_member_recent_races.assert_called_once_with(cust_id=12345)

    def test_get_recent_races_no_races(self):
        """Test handling of no recent races"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                mock_client.stats_member_recent_races.return_value = {'races': []}
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                races = client.get_recent_races(12345)
                
                assert races is None  # Returns None when no races found

    def test_get_recent_races_invalid_format(self):
        """Test handling of invalid response format"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                mock_client.stats_member_recent_races.return_value = {'invalid_key': []}
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                races = client.get_recent_races(12345)
                
                assert races is None

    def test_format_race_result_basic(self):
        """Test formatting of basic race result"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                
                # Test with basic race data
                race_data = {
                    'start_time': '2025-08-25 14:30:00',
                    'series_name': 'IMSA WeatherTech SportsCar Championship',
                    'track_name': 'Daytona International Speedway',
                    'track_config': 'Road Course',
                    'car_name': 'Ford Mustang GT4',
                    'car_class': 'DPI',
                    'session_type_name': 'Official Race',
                    'num_drivers': 24,
                    'start_position': 5,
                    'finish_position': 3,
                    'irating_delta': 15,
                    'championship_points': 25
                }
                
                formatted = client.format_race_result(race_data)
                
                # Check that required fields are formatted correctly
                assert formatted['timestamp'] == '2025-08-25 14:30:00 UTC'
                assert formatted['series_name'] == 'IMSA WeatherTech SportsCar Championship'
                assert formatted['track_name'] == 'Daytona International Speedway'
                assert formatted['track_config'] == 'Road Course'
                assert formatted['car_name'] == 'Ford Mustang GT4'
                assert formatted['car_class'] == 'DPI'
                assert formatted['field_size'] == '24'
                assert formatted['start_position'] == '5'
                assert formatted['finish_position'] == '3'

    def test_format_race_result_missing_fields(self):
        """Test formatting of race result with missing fields"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                
                # Test with minimal race data
                race_data = {
                    'start_time': '2025-08-25 14:30:00',
                    'track_name': 'Unknown Track'
                }
                
                formatted = client.format_race_result(race_data)
                
                # Check that missing fields are set to N/A
                assert formatted['timestamp'] == '2025-08-25 14:30:00 UTC'
                assert formatted['track_name'] == 'Unknown Track'
                assert formatted['series_name'] == 'N/A'
                assert formatted['track_config'] == 'N/A'
                assert formatted['car_name'] == 'N/A'

    def test_format_timestamp(self):
        """Test timestamp formatting function"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                
                # Test standard format
                result = client._format_timestamp("2025-08-25 14:30:00")
                assert result == "2025-08-25 14:30:00 UTC"
                
                # Test invalid format (should return original)
                result = client._format_timestamp("invalid timestamp")
                assert result == "invalid timestamp"

    def test_get_race_details_success(self):
        """Test successful fetching of race details"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                # Return sample race details that match the required structure
                mock_client.result.return_value = {
                    'session_id': 123,
                    'subsession_id': 456,
                    'session_results': [
                        {
                            'simsession_type_name': 'Race',
                            'results': [
                                {
                                    'cust_id': 12345,
                                    'display_name': 'Test Driver',
                                    'car_name': 'Ford Mustang GT4',
                                    'car_class_name': 'DPI',
                                    'finish_position': 3,
                                    'start_position': 5
                                }
                            ]
                        }
                    ],
                    'track': {
                        'track_name': 'Daytona International Speedway',
                        'config_name': 'Road Course'
                    },
                    'start_time': '2025-08-25 14:30:00',
                    'event_type_name': 'Official Race'
                }
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                details = client.get_race_details(456)
                
                assert details is not None
                assert details['subsession_id'] == 456
                assert details['track']['track_name'] == 'Daytona International Speedway'
                mock_client.result.assert_called_once_with(subsession_id=456, include_licenses=True)

    def test_get_race_details_missing_fields(self):
        """Test handling of missing required fields in race details"""
        with patch('os.environ.get', side_effect=['test_user', 'test_pass']):
            with patch('iracing_api.irDataClient') as mock_client_class:
                mock_client = Mock()
                mock_client.member_info.return_value = {'cust_id': 12345}
                # Return race details missing required field
                mock_client.result.return_value = {
                    'session_id': 123,
                    # 'subsession_id' is missing
                    'session_results': [],
                    'track': {},
                    'start_time': '2025-08-25 14:30:00'
                }
                mock_client_class.return_value = mock_client
                
                client = iRacingClient()
                details = client.get_race_details(456)
                
                assert details is None  # Should return None when required field is missing

if __name__ == "__main__":
    pytest.main([__file__, "-v"])