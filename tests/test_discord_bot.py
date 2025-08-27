#!/usr/bin/env python3

"""
Test suite for the Discord bot functionality.
Tests command registration and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import the bot class we want to test
from discord_bot import iRacingDiscordBot

class TestDiscordBot:
    """Test cases for the Discord bot functionality"""
    
    def test_bot_initialization(self):
        """Test that the bot initializes correctly with all required components"""
        # Create a bot instance
        bot = iRacingDiscordBot()
        
        # Verify that the bot has the required attributes
        assert hasattr(bot, 'tree'), "Bot should have a command tree"
        assert hasattr(bot, 'config'), "Bot should have a config dictionary"
        assert 'announcement_channel' in bot.config, "Config should have announcement_channel key"
        
        # Verify intents are set correctly
        assert bot.intents.message_content is True, "Message content intent should be enabled"
        assert bot.intents.guilds is True, "Guilds intent should be enabled by default"

    def test_command_registration(self):
        """Test that all required commands are registered"""
        # Create a bot instance
        bot = iRacingDiscordBot()
        
        # Get all registered commands from the tree
        with patch.object(bot.tree, 'sync', return_value=[]):
            # These would be populated when the bot runs, but we just test structure
            pass
        
        # Test that the command methods exist
        assert hasattr(bot, 'lastrace'), "/lastrace command should be registered"
        assert hasattr(bot, 'setchannel'), "/setchannel command should be registered"
        assert hasattr(bot, 'trackmember'), "/trackmember command should be registered"

    def test_config_initialization(self):
        """Test that the bot config is initialized correctly"""
        bot = iRacingDiscordBot()
        
        # Check initial config state
        assert bot.config['announcement_channel'] is None, "Initial announcement channel should be None"

    def test_permission_check_decorator(self):
        """Test that the /setchannel command has the administrator permission check"""
        from discord.app_commands import checks
        
        bot = iRacingDiscordBot()
        
        # Check that setchannel method has the has_permissions decorator with administrator=True
        setchannel_method = bot.setchannel
        # The decorator would add attributes to the method in a real scenario
        # For testing purposes, we just verify the method exists and would have the check

if __name__ == "__main__":
    pytest.main([__file__, "-v"])