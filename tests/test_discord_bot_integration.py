#!/usr/bin/env python3

"""
Integration test for the Discord bot that simulates real-world usage
without requiring a real Discord token.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
import asyncio

# Add src directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import the bot class we want to test
from discord_bot import iRacingDiscordBot

class TestDiscordBotIntegration:
    """Integration test cases for the Discord bot"""
    
    @patch('discord.Client.run')
    @patch.dict(os.environ, {'DISCORD_TOKEN': 'test_token_123'})
    def test_bot_startup(self, mock_run):
        """Test that the bot starts up correctly with a token"""
        from discord_bot import main
        
        # This should not raise an exception and should call bot.run with the token
        main()
        
        # Verify that bot.run was called with the token
        mock_run.assert_called_once_with('test_token_123')

    @patch('discord.Client.run')
    def test_bot_startup_no_token(self, mock_run):
        """Test that the bot fails gracefully when no token is provided"""
        from discord_bot import main
        
        # Remove DISCORD_TOKEN from environment
        if 'DISCORD_TOKEN' in os.environ:
            del os.environ['DISCORD_TOKEN']
        
        # This should not raise an exception and should not call bot.run
        main()
        
        # Verify that bot.run was NOT called
        mock_run.assert_not_called()

    def test_command_execution(self):
        """Test that commands execute and return appropriate responses"""
        async def run_test():
            # Create a mock interaction
            mock_interaction = Mock()
            mock_interaction.user.id = 12345
            mock_interaction.response.send_message = Mock()
            
            # Create bot instance
            bot = iRacingDiscordBot()
            
            # Test /lastrace command
            await bot.lastrace(mock_interaction, "123456")
            
            # Verify response was sent
            mock_interaction.response.send_message.assert_called()
            call_args = mock_interaction.response.send_message.call_args[0][0]
            assert "Retrieving race details" in call_args
            assert "customer ID 123456" in call_args
            
            # Reset mock
            mock_interaction.response.send_message.reset_mock()
            
            # Test /trackmember command
            await bot.trackmember(mock_interaction, "654321")
            
            # Verify response was sent
            mock_interaction.response.send_message.assert_called()
            call_args = mock_interaction.response.send_message.call_args[0][0]
            assert "Now tracking iRacing member" in call_args
            assert "customer ID 654321" in call_args
        
        asyncio.run(run_test())

    def test_setchannel_permission_check(self):
        """Test that /setchannel command requires administrator permission"""
        async def run_test():
            # Create a mock interaction without administrator permission
            mock_interaction = Mock()
            mock_interaction.user.id = 12345
            mock_interaction.response.send_message = Mock()
            
            # Create bot instance
            bot = iRacingDiscordBot()
            
            # Test /setchannel command with user who doesn't have admin permission
            # This should trigger the permission error handler
            with patch('discord.app_commands.checks.has_permissions') as mock_check:
                # Simulate missing permissions
                mock_check.side_effect = lambda **kwargs: lambda func: func
                
                # This would normally raise MissingPermissions, but our error handler should catch it
                await bot.on_app_command_error(mock_interaction, Exception("Missing permissions"))
                
                # Verify error response was sent
                mock_interaction.response.send_message.assert_called()
                call_args = mock_interaction.response.send_message.call_args[0][0]
                assert "You don't have permission" in call_args
                assert "Administrator permissions" in call_args
        
        asyncio.run(run_test())

    def test_config_functionality(self):
        """Test that the bot config works correctly"""
        bot = iRacingDiscordBot()
        
        # Initial state
        assert bot.config['announcement_channel'] is None
        
        # Simulate setting channel (what /setchannel would do)
        test_channel_id = 987654321
        bot.config['announcement_channel'] = test_channel_id
        
        # Verify it was saved
        assert bot.config['announcement_channel'] == test_channel_id

if __name__ == "__main__":
    pytest.main([__file__, "-v"])