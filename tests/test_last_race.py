#!/usr/bin/env python3

"""
Test suite for the last_race_details script.
Tests authentication, data handling, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from last_race_details import (
    authenticate,
    get_recent_races,
    get_race_details,
    get_lap_data,
    format_timestamp,
    display_race_summary
)

# Mock the iracingdataapi client for testing
import sys
from unittest.mock import Mock
sys.modules['iracingdataapi.client'] = Mock()
sys.modules['iracingdataapi.client'].irDataClient = Mock

class TestLastRaceDetails:
    """Test cases for the last race details functionality"""
    
    def test_format_timestamp(self):
        """Test timestamp formatting function"""
        # Test standard format
        result = format_timestamp("2023-01-15 14:30:00")
        assert "January 15" in result
        assert "2:30 PM" in result
        
        # Test invalid format (should return original)
        result = format_timestamp("invalid timestamp")
        assert result == "invalid timestamp"
    
    @patch('builtins.input', side_effect=["test_user", "test_pass"])
    @patch('builtins.getpass.getpass', return_value="test_pass")
    @patch('iracingdataapi.irDataClient')
    def test_authenticate_success(self, mock_client_class, mock_getpass, mock_input):
        """Test successful authentication"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Should not raise exception and should return client
        client = authenticate()
        assert client == mock_client
        mock_client_class.assert_called_once()
    
    @patch('builtins.input', side_effect=["", "test_pass"])
    @patch('builtins.getpass.getpass', return_value="test_pass")
    def test_authenticate_empty_username(self, mock_getpass, mock_input):
        """Test authentication with empty username"""
        # Should exit with error
        with pytest.raises(SystemExit) as excinfo:
            authenticate()
        assert excinfo.value.code == 1
    
    @patch('iracingdataapi.irDataClient')
    def test_get_recent_races_no_races(self, mock_client_class):
        """Test handling of no recent races"""
        mock_client = Mock()
        mock_client.stats_member_recent_races.return_value = {"races": []}
        
        with pytest.raises(SystemExit) as excinfo:
            get_recent_races(mock_client)
        assert excinfo.value.code == 0  # Clean exit for no races
    
    @patch('iracingdataapi.irDataClient')
    def test_get_recent_races_invalid_format(self, mock_client_class):
        """Test handling of invalid response format"""
        mock_client = Mock()
        mock_client.stats_member_recent_races.return_value = {"invalid_key": []}
        
        with pytest.raises(SystemExit) as excinfo:
            get_recent_races(mock_client)
        assert excinfo.value.code == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])