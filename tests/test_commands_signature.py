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
    
    # Verify it's the only command with this name
    setchannel_commands = [cmd for cmd in bot.tree.get_commands() if cmd.name == "setchannel"]
    assert len(setchannel_commands) == 1, \
        f"Found {len(setchannel_commands)} commands named 'setchannel', expected exactly 1"