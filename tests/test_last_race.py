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

# Import the functions we want to test
from last_race_details import (
    authenticate,
    get_recent_races,
    get_race_details,
    get_lap_data,
    format_timestamp,
    display_race_summary
)

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
    
    def test_authenticate_empty_username(self):
        """Test authentication with empty username"""
        # Mock to return empty username and bypass environment variables
        with patch('os.environ.get', side_effect=[None, 'test_pass']), \
             patch('builtins.input', return_value=""), \
             patch('getpass.getpass', return_value="test_pass"):
            
            # Should exit with error code 1
            with pytest.raises(SystemExit) as excinfo:
                authenticate()
            
            assert excinfo.value.code == 1
    
    def test_authenticate_empty_password(self):
        """Test authentication with empty password"""
        # Mock to return empty password and bypass environment variables
        with patch('os.environ.get', side_effect=['test_user', None]), \
             patch('builtins.input', return_value="test_user"), \
             patch('getpass.getpass', return_value=""):
            
            # Should exit with error code 1
            with pytest.raises(SystemExit) as excinfo:
                authenticate()
            
            assert excinfo.value.code == 1
    
    def test_get_recent_races_no_races(self):
        """Test handling of no recent races"""
        # Create a mock client
        mock_client = Mock()
        mock_client.stats_member_recent_races.return_value = {"races": []}
        
        # Should exit with code 0 (clean exit)
        with pytest.raises(SystemExit) as excinfo:
            get_recent_races(mock_client)
        
        assert excinfo.value.code == 0
    
    def test_get_recent_races_invalid_format(self):
        """Test handling of invalid response format"""
        # Create a mock client
        mock_client = Mock()
        mock_client.stats_member_recent_races.return_value = {"invalid_key": []}
        
        # Should exit with code 1
        with pytest.raises(SystemExit) as excinfo:
            get_recent_races(mock_client)
        
        assert excinfo.value.code == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])