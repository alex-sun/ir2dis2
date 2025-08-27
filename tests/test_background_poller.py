#!/usr/bin/env python3

"""
Integration test for the background poller functionality in the Discord bot.
Tests the core polling logic, race detection, and posting behavior.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import asyncio
from datetime import datetime

# Add src directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import the bot class and necessary modules
from discord_bot import iRacingDiscordBot
from src.database.crud import get_tracked_member, set_last_published, get_last_published
from src.iracing_api import iracing_api


class TestBackgroundPollerIntegration:
    """Integration test cases for the background poller"""

    @patch('discord.ext.tasks.loop')
    @patch.dict(os.environ, {'POLL_INTERVAL_SECONDS': '10', 'DISCORD_TOKEN': 'test_token'})
    def test_poller_initialization(self, mock_loop):
        """Test that the background poller initializes correctly"""
        # Create bot instance
        bot = iRacingDiscordBot()
        
        # Verify poller was created with correct interval
        mock_loop.assert_called_once_with(seconds=10)
        
        # Verify poller has expected attributes and methods
        assert hasattr(bot, 'background_poller'), "Bot should have background_poller task"
        assert callable(bot.background_poller), "background_poller should be callable"
        assert hasattr(bot.background_poller, 'is_running'), "poller should have is_running method"
        assert hasattr(bot.background_poller, 'start'), "poller should have start method"

    def test_poller_starts_on_ready(self):
        """Test that the poller starts automatically when bot is ready"""
        async def run_test():
            # Create bot instance
            bot = iRacingDiscordBot()
            
            # Mock the poller is_running method to return False initially
            with patch.object(bot.background_poller, 'is_running', return_value=False):
                with patch.object(bot.background_poller, 'start') as mock_start:
                    # Call on_ready directly
                    await bot.on_ready()
                    
                    # Verify poller start was called
                    mock_start.assert_called_once()
            
            # Test case where poller is already running
            with patch.object(bot.background_poller, 'is_running', return_value=True):
                with patch.object(bot.background_poller, 'start') as mock_start:
                    # Call on_ready again
                    await bot.on_ready()
                    
                    # Verify poller start was NOT called again
                    mock_start.assert_not_called()

        asyncio.run(run_test())

    def test_guild_processing_logic(self):
        """Test that the poller correctly processes guilds"""
        async def run_test():
            # Create bot instance
            bot = iRacingDiscordBot()
            
            # Mock guilds
            mock_guild1 = Mock()
            mock_guild1.id = 123
            mock_guild1.name = "Test Guild 1"
            
            mock_guild2 = Mock()
            mock_guild2.id = 456
            mock_guild2.name = "Test Guild 2"
            
            # Set up mock guilds list
            bot.guilds = [mock_guild1, mock_guild2]
            
            # Mock get_guild_announcement_channel to return different values
            with patch.object(bot, 'get_guild_announcement_channel', side_effect=[
                789,  # guild1 has channel
                None   # guild2 has no channel
            ]):
                with patch.object(bot, '_get_tracked_members_for_guild', return_value=[12345]):
                    with patch.object(bot, '_process_tracked_member') as mock_process_member:
                        with patch.object(bot, 'logger') as mock_logger:
                            # Run the poller logic directly (simplified test)
                            # Note: In real testing, we'd mock the loop to run once
                            await bot.background_poller()
                            
                            # Verify guild processing logic
                            assert mock_process_member.call_count == 1  # Only guild1 should process members
                            mock_logger.info.assert_any_call("Processing guild: Test Guild 1 (ID: 123)")
                            mock_logger.warning.assert_any_call("Guild Test Guild 2 (ID: 456) has no configured announcement channel. Skipping.")

        asyncio.run(run_test())

    def test_tracked_member_processing(self):
        """Test that tracked members are processed correctly"""
        async def run_test():
            # Create bot instance
            bot = iRacingDiscordBot()
            
            # Mock race data
            mock_recent_races = [
                {
                    'subsession_id': '123456789',
                    'start_time': '2023-01-01 12:00:00',
                    'track_name': 'Test Track',
                    'track_config': 'Test Config',
                    'car_name': 'Test Car',
                    'car_class': 'Test Class',
                    'session_type_name': 'Race',
                    'num_drivers': 20,
                    'start_position': 5,
                    'finish_position': 3,
                    'irating_delta': 15,
                    'championship_points': 10
                }
            ]
            
            # Mock iracing_api methods
            with patch.object(iracing_api, 'get_recent_races', return_value=mock_recent_races):
                with patch.object(iracing_api, 'should_fetch_subsession_details', return_value=True):
                    with patch.object(iracing_api, 'get_race_details', return_value={}):
                        with patch.object(iracing_api, 'format_race_result', return_value={
                            'timestamp': '2023-01-01 12:00:00 UTC',
                            'track_name': 'Test Track',
                            'track_config': 'Test Config',
                            'car_name': 'Test Car',
                            'car_class': 'Test Class',
                            'session_type': 'Race',
                            'field_size': '20',
                            'start_position': '5',
                            'finish_position': '3',
                            'irating_delta': '15',
                            'championship_points': '10'
                        }):
                            # Mock database methods
                            with patch('src.discord_bot.get_last_published', return_value=None):  # No previous subsession
                                with patch('src.discord_bot.set_last_published', return_value=True):
                                    with patch.object(bot, 'get_channel', return_value=Mock()):
                                        with patch.object(bot, 'logger') as mock_logger:
                                            # Mock Discord channel
                                            mock_channel = Mock()
                                            mock_channel.send = Mock()
                                            bot.get_channel.return_value = mock_channel
                                            
                                            # Process a tracked member
                                            await bot._process_tracked_member(123, 12345, 789)
                                            
                                            # Verify processing logic
                                            mock_logger.info.assert_any_call("Latest subsession_id for member 12345: 123456789")
                                            mock_logger.info.assert_any_call("New subsession found for member 12345: 123456789")
                                            mock_channel.send.assert_called_once()  # Message should be sent
                                            assert "New Race Result for Member 12345" in mock_channel.send.call_args[0][0]

        asyncio.run(run_test())

    def test_de_duplication_prevention(self):
        """Test that duplicate posts are prevented using last_published"""
        async def run_test():
            # Create bot instance
            bot = iRacingDiscordBot()
            
            # Mock race data (same subsession)
            mock_recent_races = [
                {
                    'subsession_id': '123456789',
                    # ... other race data ...
                }
            ]
            
            # Mock iracing_api methods
            with patch.object(iracing_api, 'get_recent_races', return_value=mock_recent_races):
                # First call: no previous subsession (should post)
                with patch('src.discord_bot.get_last_published', return_value=None):
                    with patch('src.discord_bot.set_last_published', return_value=True):
                        with patch.object(bot, 'get_channel', return_value=Mock()):
                            with patch.object(bot, 'logger') as mock_logger:
                                mock_channel = Mock()
                                mock_channel.send = Mock()
                                bot.get_channel.return_value = mock_channel
                                
                                await bot._process_tracked_member(123, 12345, 789)
                                
                                # Should have sent a message
                                assert mock_channel.send.call_count == 1
                                mock_logger.info.assert_any_call("New subsession found for member 12345: 123456789")
                
                # Reset mock
                mock_channel.send.reset_mock()
                
                # Second call: same subsession (should NOT post)
                with patch('src.discord_bot.get_last_published', return_value='123456789'):
                    with patch.object(bot, 'get_channel', return_value=Mock()):
                        with patch.object(bot, 'logger') as mock_logger:
                            mock_channel = Mock()
                            mock_channel.send = Mock()
                            bot.get_channel.return_value = mock_channel
                            
                            await bot._process_tracked_member(123, 12345, 789)
                            
                            # Should NOT have sent a message
                            assert mock_channel.send.call_count == 0
                            mock_logger.info.assert_any_call("Subsession 123456789 for member 12345 already published. Skipping.")

        asyncio.run(run_test())

    def test_error_handling(self):
        """Test that errors are handled gracefully without crashing the poller"""
        async def run_test():
            # Create bot instance
            bot = iRacingDiscordBot()
            
            # Mock guilds with errors in different parts of the process
            mock_guild = Mock()
            mock_guild.id = 123
            mock_guild.name = "Error Test Guild"
            bot.guilds = [mock_guild]
            
            # Test different error scenarios
            error_scenarios = [
                # Scenario 1: Error getting guild config
                (
                    Exception("DB error"),
                    "Error getting guild announcement channel"
                ),
                # Scenario 2: Error getting tracked members
                (
                    Exception("DB error"),
                    "Error getting tracked members for guild"
                ),
                # Scenario 3: Error processing member
                (
                    Exception("API error"),
                    "Error processing member"
                )
            ]
            
            for i, (error, expected_log) in enumerate(error_scenarios):
                with patch.object(bot, 'get_guild_announcement_channel', return_value=789):
                    with patch.object(bot, '_get_tracked_members_for_guild', return_value=[12345]):
                        with patch.object(bot, '_process_tracked_member', side_effect=error):
                            with patch.object(bot, 'logger') as mock_logger:
                                # Run poller
                                await bot.background_poller()
                                
                                # Should log error but continue running
                                mock_logger.error.assert_any_call(expected_log)
                                # Should NOT crash - poller should complete

        asyncio.run(run_test())

    def test_empty_states(self):
        """Test poller behavior with empty states (no guilds, no tracked members, no races)"""
        async def run_test():
            # Create bot instance
            bot = iRacingDiscordBot()
            
            # Test 1: No guilds
            bot.guilds = []
            with patch.object(bot, 'logger') as mock_logger:
                await bot.background_poller()
                mock_logger.info.assert_any_call("Poller found 0 guilds to process")
            
            # Test 2: Guild with no tracked members
            mock_guild = Mock()
            mock_guild.id = 123
            mock_guild.name = "Empty Guild"
            bot.guilds = [mock_guild]
            
            with patch.object(bot, 'get_guild_announcement_channel', return_value=789):
                with patch.object(bot, '_get_tracked_members_for_guild', return_value=[]):
                    with patch.object(bot, 'logger') as mock_logger:
                        await bot.background_poller()
                        mock_logger.info.assert_any_call("No tracked members in guild Empty Guild (ID: 123). Skipping.")
            
            # Test 3: Member with no recent races
            mock_guild = Mock()
            mock_guild.id = 123
            bot.guilds = [mock_guild]
            
            with patch.object(bot, 'get_guild_announcement_channel', return_value=789):
                with patch.object(bot, '_get_tracked_members_for_guild', return_value=[12345]):
                    with patch.object(iracing_api, 'get_recent_races', return_value=None):
                        with patch.object(bot, 'logger') as mock_logger:
                            await bot.background_poller()
                            mock_logger.info.assert_any_call("No recent races found for member 12345 in guild 123")

        asyncio.run(run_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])