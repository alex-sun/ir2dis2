import pytest
import discord
from discord.ext import commands
from discord import app_commands
from src.discord_bot import iRacingDiscordBot

def test_setchannel_command_signature():
    """Test that /setchannel command has the correct signature and properties"""
    # Create a test bot instance
    intents = discord.Intents.default()
    intents.guilds = True
    bot = iRacingDiscordBot()
    
    # Register commands (this would happen in on_ready in real usage)
    import asyncio
    asyncio.run(bot._register_commands())
    
    # Check that the command is registered
    commands_in_tree = [cmd.name for cmd in bot.tree.get_commands()]
    assert "setchannel" in commands_in_tree, "setchannel command should be registered in the tree"
    
    # Get the specific command
    setchannel_cmd = None
    for cmd in bot.tree.get_commands():
        if cmd.name == "setchannel":
            setchannel_cmd = cmd
            break
    
    assert setchannel_cmd is not None, "Could not find setchannel command in tree"
    
    # Verify command properties
    assert setchannel_cmd.name == "setchannel", f"Command name should be 'setchannel', got '{setchannel_cmd.name}'"
    assert setchannel_cmd.description == "Set the channel for iRacing race announcements", \
        f"setchannel description should be 'Set the channel for iRacing race announcements', got '{setchannel_cmd.description}'"
    
    # Verify parameter count and names
    assert len(setchannel_cmd.parameters) == 1, \
        f"setchannel should have exactly 1 parameter, got {len(setchannel_cmd.parameters)}"
    
    param = setchannel_cmd.parameters[0]
    assert param.name == "channel", \
        f"setchannel parameter should be named 'channel', got '{param.name}'"
    
    # Verify parameter type is Channel with text restriction (or compatible)
    from discord import app_commands, ChannelType
    assert isinstance(param.type, app_commands.Channel), \
        f"setchannel parameter should be of type app_commands.Channel, got '{param.type}'"
    
    # Verify the channel type restriction includes text channels
    assert ChannelType.text in param.type.channel_types, \
        f"setchannel parameter should accept text channels, got '{param.type.channel_types}'"
    assert ChannelType.news in param.type.channel_types, \
        f"setchannel parameter should accept news channels, got '{param.type.channel_types}'"
    
    # Verify it's the only command with this name
    setchannel_commands = [cmd for cmd in bot.tree.get_commands() if cmd.name == "setchannel"]
    assert len(setchannel_commands) == 1, \
        f"Found {len(setchannel_commands)} commands named 'setchannel', expected exactly 1"

def test_command_signature_lock():
    """Test that command signatures are locked to prevent unexpected changes"""
    intents = discord.Intents.default()
    intents.guilds = True
    bot = iRacingDiscordBot()
    
    import asyncio
    asyncio.run(bot._register_commands())
    
    # Define the expected command structure
    EXPECTED_COMMANDS = {
        "setchannel": {
            "description": "Set the channel for iRacing race announcements",
            "parameters": [
                {
                    "name": "channel",
                    "type": discord.TextChannel
                }
            ]
        },
        "lastrace": {
            "description": "Get details about a user's most recent iRacing race",
            "parameters": [
                {
                    "name": "customer_id",
                    "type": str
                }
            ]
        },
        "trackmember": {
            "description": "Track a specific iRacing member's activity",
            "parameters": [
                {
                    "name": "customer_id",
                    "type": str
                }
            ]
        }
    }
    
    # Verify each command matches expected structure
    for cmd_name, expected in EXPECTED_COMMANDS.items():
        cmd = None
        for c in bot.tree.get_commands():
            if c.name == cmd_name:
                cmd = c
                break
        
        assert cmd is not None, f"Command '{cmd_name}' not found in command tree"
        assert cmd.description == expected["description"], \
            f"Command '{cmd_name}' description mismatch: expected '{expected['description']}', got '{cmd.description}'"
        
        # Verify parameters
        assert len(cmd.parameters) == len(expected["parameters"]), \
            f"Command '{cmd_name}' parameter count mismatch: expected {len(expected['parameters'])}, got {len(cmd.parameters)}"
        
        for i, expected_param in enumerate(expected["parameters"]):
            actual_param = cmd.parameters[i]
            assert actual_param.name == expected_param["name"], \
                f"Parameter {i} name mismatch in '{cmd_name}': expected '{expected_param['name']}', got '{actual_param.name}'"
            assert actual_param.type == expected_param["type"], \
                f"Parameter {i} type mismatch in '{cmd_name}': expected {expected_param['type']}, got {actual_param.type}"

def test_hard_reset_procedure():
    """Test that hard reset procedure can be called without errors"""
    intents = discord.Intents.default()
    intents.guilds = True
    bot = iRacingDiscordBot()
    
    import asyncio
    
    # Mock the necessary methods to prevent actual API calls
    original_clear_commands = bot.tree.clear_commands
    original_sync = bot.tree.sync
    original_register_commands = bot._register_commands
    
    # Mock implementations that don't make real API calls
    bot.tree.clear_commands = lambda *args, **kwargs: None
    bot.tree.sync = lambda *args, **kwargs: []
    bot._register_commands = lambda: None
    
    try:
        # This should not raise exceptions
        asyncio.run(bot.hard_reset_all_commands())
        assert True, "Hard reset procedure should complete without errors"
    finally:
        # Restore original methods
        bot.tree.clear_commands = original_clear_commands
        bot.tree.sync = original_sync
        bot._register_commands = original_register_commands

def test_diagnostic_function():
    """Test that diagnostic function can be called without errors"""
    intents = discord.Intents.default()
    intents.guilds = True
    bot = iRacingDiscordBot()
    
    import asyncio
    
    # Mock the necessary methods to prevent actual API calls
    original_get_commands = bot.tree.get_commands
    original_fetch_commands = bot.tree.fetch_commands
    
    # Mock implementations that don't make real API calls
    bot.tree.get_commands = lambda: []
    bot.tree.fetch_commands = lambda *args, **kwargs: []
    
    try:
        # This should not raise exceptions
        asyncio.run(bot.diagnose_command_shapes())
        assert True, "Diagnostic function should complete without errors"
    finally:
        # Restore original methods
        bot.tree.get_commands = original_get_commands
        bot.tree.fetch_commands = original_fetch_commands