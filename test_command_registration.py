#!/usr/bin/env python3

"""
Test script to verify that command registration works correctly.
This script mocks the Discord API to test command registration without
needing a real Discord token or connection.
"""

import os
import sys
from unittest.mock import Mock, patch
import asyncio

# Add src directory to path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the bot class we want to test
from discord_bot import iRacingDiscordBot

async def test_command_registration():
    """Test that commands are properly registered before syncing"""
    print("Testing command registration...")
    
    # Create a mock for the command tree
    mock_tree = Mock()
    mock_tree.add_command.return_value = None
    mock_tree.sync.return_value = [Mock(name="command1"), Mock(name="command2"), Mock(name="command3")]
    
    # Create bot instance with mocked tree
    bot = iRacingDiscordBot()
    
    # Replace the real tree with our mock
    bot.tree = mock_tree
    
    # Call the on_ready method which should register and sync commands
    await bot.on_ready()
    
    # Verify that add_command was called for each command
    assert mock_tree.add_command.call_count == 3, f"Expected 3 add_command calls, got {mock_tree.add_command.call_count}"
    
    # Verify the specific commands that were registered
    command_calls = [call[0].__name__ for call in mock_tree.add_command.call_args_list]
    expected_commands = ["lastrace", "setchannel", "trackmember"]
    
    for cmd in expected_commands:
        assert cmd in command_calls, f"Expected command {cmd} to be registered, but it wasn't"
    
    print("✅ All commands were successfully registered!")
    print(f"   Registered commands: {command_calls}")
    print(f"   Expected commands: {expected_commands}")

if __name__ == "__main__":
    asyncio.run(test_command_registration())