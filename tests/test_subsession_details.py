#!/usr/bin/env python3

"""
Unit tests for subsession details functionality in the iRacing API wrapper.
Tests the enhanced race result formatting and caching mechanisms.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import os
import sys

# Add src directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from iracing_api import iRacingClient, iracing_api

class TestSubsessionDetails(unittest.TestCase):
    """Test cases for subsession details functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock client
        self.mock_client = MagicMock()
        
        # Create a test race object
        self.test_race = {
            'start_time': '2023-01-01 12:00:00',
            'series_name': 'Test Series',
            'track_name': 'Test Track',
            'track_config': 'Test Config',
            'car_name': 'Test Car',
            'car_class': 'Test Class',
            'session_type_name': 'Race',
            'num_drivers': 20,
            'start_position': 5,
            'finish_position': 3,
            'irating_delta': 10,
            'championship_points': 50,
            'subsession_id': 12345
        }
        
        # Create a test subsession details object
        self.test_subsession_details = {
            'session_id': 123,
            'subsession_id': 12345,
            'session_results': [
                {
                    'simsession_type_name': 'Race',
                    'results': [
                        {
                            'cust_id': 123,
                            'finish_position': 3,
                            'car_name': 'Test Car',
                            'car_class_name': 'Test Class',
                            'fastest_lap': 60.5,
                            'average_lap': 62.3
                        }
                    ]
                }
            ],
            'track': {
                'track_name': 'Enhanced Track',
                'config_name': 'Enhanced Config',
                'country': 'Test Country'
            },
            'start_time': '2023-01-01 12:00:00',
            'session_info': {
                'track': {
                    'track_name': 'Enhanced Track',
                    'config_name': 'Enhanced Config',
                    'country': 'Test Country'
                },
                'event': {
                    'series_name': 'Enhanced Series',
                    'series_type': 'Official',
                    'event_name': 'Enhanced Event'
                },
                'weather': {
                    'condition': 'Sunny',
                    'temp': 25
                }
            }
        }

    def test_should_fetch_subsession_details(self):
        """Test the should_fetch_subsession_details method"""
        # Create a client instance
        client = iRacingClient()
        
        # Test with a race that has some data
        result = client.should_fetch_subsession_details(self.test_race)
        self.assertTrue(result, "Should always return True for now")

    def test_format_race_result_with_subsession_details(self):
        """Test formatting race results with subsession details"""
        # Create a client instance
        client = iRacingClient()
        
        # Set cust_id for testing user position detection
        client.cust_id = 123
        
        # Format the race result
        formatted = client.format_race_result(self.test_race, self.test_subsession_details)
        
        # Check that enhanced fields are present and correct
        self.assertEqual(formatted['track_name'], 'Enhanced Track')
        self.assertEqual(formatted['track_config'], 'Enhanced Config')
        self.assertEqual(formatted['track_country'], 'Test Country')
        self.assertEqual(formatted['series_name'], 'Enhanced Series')
        self.assertEqual(formatted['series_type'], 'Official')
        self.assertEqual(formatted['event_name'], 'Enhanced Event')
        self.assertEqual(formatted['weather_condition'], 'Sunny (25°C)')
        self.assertEqual(formatted['your_position'], '3')
        self.assertEqual(formatted['fastest_lap_time'], '1:00.500')
        self.assertEqual(formatted['average_lap_time'], '1:02.300')

    def test_format_lap_time(self):
        """Test the _format_lap_time helper method"""
        # Create a client instance
        client = iRacingClient()
        
        # Test with valid lap times
        self.assertEqual(client._format_lap_time(60.5), '1:00.500')  # Updated to match our implementation
        self.assertEqual(client._format_lap_time(120.3), '2:00.300')
        self.assertEqual(client._format_lap_time(0), 'N/A')
        
        # Test with invalid input
        self.assertEqual(client._format_lap_time(-10), 'N/A')
        self.assertEqual(client._format_lap_time('invalid'), 'N/A')

    def test_format_session_duration(self):
        """Test the _format_session_duration helper method"""
        # Create a client instance
        client = iRacingClient()
        
        # Test with valid durations
        self.assertEqual(client._format_session_duration(3600), '01:00:00')
        self.assertEqual(client._format_session_duration(1800), '30:00')
        self.assertEqual(client._format_session_duration(60), '1:00')
        self.assertEqual(client._format_session_duration(30), '0:30')
        
        # Test with invalid input
        self.assertEqual(client._format_session_duration(0), 'N/A')
        self.assertEqual(client._format_session_duration(-10), 'N/A')
        self.assertEqual(client._format_session_duration('invalid'), 'N/A')

    @patch('iracing_api.irDataClient.result')
    def test_get_race_details_caching(self, mock_result):
        """Test that subsession details are cached properly"""
        # Create a client instance
        client = iRacingClient()
        
        # Set up the mock
        mock_result.return_value = self.test_subsession_details
        
        # First call - should fetch from API
        result1 = client.get_race_details(12345)
        self.assertEqual(result1, self.test_subsession_details)
        mock_result.assert_called_once()
        
        # Second call - should use cache
        result2 = client.get_race_details(12345)
        self.assertEqual(result2, self.test_subsession_details)
        # mock_result should not be called again
        mock_result.assert_called_once()

if __name__ == '__main__':
    unittest.main()