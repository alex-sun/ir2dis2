#!/usr/bin/env python3

"""
Discord bot for iRacing integration with slash commands.
Uses discord.py 2.x and app_commands for slash command support.
"""

import os
import signal
import sys
from typing import Optional, Literal
from src.logging_config import setup_logging, get_logger, add_correlation_id, generate_correlation_id
from src.circuit_breaker import discord_api_circuit_breaker, CircuitBreakerError

# Import database functionality
from src.database import init_db, SessionLocal
from src.database.crud import (
    get_guild_config, set_guild_config,
    get_tracked_member, add_tracked_member,
    get_last_published, set_last_published
)
from src.database.models import TrackedMember
from src.database.utils import cleanup_resources

# Import iRacing API wrapper
from src.iracing_api import iracing_api

# Set up structured logging
setup_logging()
logger = get_logger(__name__)
add_correlation_id(logger, "bot-main")

# Environment variables
POLL_INTERVAL_SECONDS = int(os.environ.get('POLL_INTERVAL_SECONDS', 60))

# Required intents for the bot
intents = Intents.default()
intents.message_content = True  # Needed for some interactions

class iRacingDiscordBot(Client):
    """Main Discord bot class for iRacing integration"""
    
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.is_shutting_down = False
        
        # Initialize database on bot startup
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()

    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown"""
        logger.info("Registering signal handlers for SIGINT and SIGTERM")
        
        # Store reference to self for signal handlers
        global bot
        bot = self
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Signal handlers registered successfully")

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('Syncing slash commands...')
        
        # Sync commands globally (may take up to 1 hour to propagate)
        # For development, you can use guild-specific sync which is instant
        try:
            synced = await self.tree.sync()
            logger.info(f'Successfully synced {len(synced)} command(s)')
        except Exception as e:
            logger.error(f'Failed to sync commands: {e}')
        
        # Start the background poller task
        if not self.background_poller.is_running():
            self.background_poller.start()
            logger.info(f"Background poller started with interval: {POLL_INTERVAL_SECONDS} seconds")
        else:
            logger.info("Background poller is already running")
        
        logger.info('Bot is ready!')

    # ------------------------------
    # Helper Methods
    # ------------------------------
    async def get_guild_announcement_channel(self, guild_id: int) -> Optional[int]:
        """Get the announcement channel for a specific guild"""
        try:
            async with SessionLocal() as db:
                config = get_guild_config(db, guild_id)
                return config.channel_id if config else None
        except Exception as e:
            logger.error(f"Error getting guild announcement channel: {e}")
            return None

    async def set_guild_announcement_channel(self, guild_id: int, channel_id: int) -> bool:
        """Set the announcement channel for a specific guild"""
        try:
            async with SessionLocal() as db:
                result = set_guild_config(db, guild_id, channel_id)
                return result is not None
        except Exception as e:
            logger.error(f"Error setting guild announcement channel: {e}")
            return False

    async def is_member_tracked(self, guild_id: int, customer_id: str) -> bool:
        """Check if an iRacing member is tracked in a specific guild"""
        try:
            async with SessionLocal() as db:
                return get_tracked_member(db, guild_id, int(customer_id))
        except Exception as e:
            logger.error(f"Error checking if member is tracked: {e}")
            return False

    async def track_member(self, guild_id: int, customer_id: str) -> bool:
        """Track an iRacing member in a specific guild"""
        try:
            async with SessionLocal() as db:
                return add_tracked_member(db, guild_id, int(customer_id))
        except Exception as e:
            logger.error(f"Error tracking member: {e}")
            return False

    async def get_last_published_subsession(self, guild_id: int, customer_id: str) -> Optional[str]:
        """Get the last published subsession ID for a member"""
        try:
            async with SessionLocal() as db:
                return get_last_published(db, guild_id, int(customer_id))
        except Exception as e:
            logger.error(f"Error getting last published subsession: {e}")
            return None

    async def set_last_published_subsession(self, guild_id: int, customer_id: str, subsession_id: str) -> bool:
        """Set the last published subsession ID for a member"""
        try:
            async with SessionLocal() as db:
                result = set_last_published(db, guild_id, int(customer_id), subsession_id)
                return result is not None
        except Exception as e:
            logger.error(f"Error setting last published subsession: {e}")
            return False

    # ------------------------------
    # Background Poller Task
    # ------------------------------
    @tasks.loop(seconds=POLL_INTERVAL_SECONDS)
    async def background_poller(self):
        """Periodically check for new race results and post them to configured channels"""
        correlation_id = generate_correlation_id()
        logger.info(f"Starting background poller run (interval: {POLL_INTERVAL_SECONDS}s)", extra_fields={'correlation_id': correlation_id})
        
        try:
            # Get all guilds the bot is in
            guilds = list(self.guilds)
            logger.info(f"Poller found {len(guilds)} guilds to process", extra_fields={'correlation_id': correlation_id})
            
            for guild in guilds:
                guild_correlation_id = f"{correlation_id}-{guild.id}"
                logger.info(f"Processing guild: {guild.name} (ID: {guild.id})", extra_fields={'correlation_id': guild_correlation_id})
                
                try:
                    # Get configured channel for this guild
                    channel_id = await self.get_guild_announcement_channel(guild.id)
                    
                    if not channel_id:
                        logger.warning(f"Guild {guild.name} (ID: {guild.id}) has no configured announcement channel. Skipping.", extra_fields={'correlation_id': guild_correlation_id})
                        continue
                    
                    # Get all tracked members for this guild
                    tracked_members = await self._get_tracked_members_for_guild(guild.id)
                    
                    if not tracked_members:
                        logger.info(f"No tracked members in guild {guild.name} (ID: {guild.id}). Skipping.", extra_fields={'correlation_id': guild_correlation_id})
                        continue
                    
                    logger.info(f"Found {len(tracked_members)} tracked members in guild {guild.name} (ID: {guild.id})", extra_fields={'correlation_id': guild_correlation_id})
                    
                    # Process each tracked member
                    for customer_id in tracked_members:
                        member_correlation_id = f"{guild_correlation_id}-{customer_id}"
                        try:
                            await self._process_tracked_member(guild.id, customer_id, channel_id, member_correlation_id)
                        except Exception as e:
                            logger.error(f"Error processing member {customer_id} in guild {guild.id}: {str(e)}", extra_fields={'correlation_id': member_correlation_id})
                            continue
                    
                except Exception as e:
                    logger.error(f"Error processing guild {guild.name} (ID: {guild.id}): {str(e)}", extra_fields={'correlation_id': guild_correlation_id})
                    continue
        
        except Exception as e:
            logger.error(f"Critical error in background poller: {str(e)}", extra_fields={'correlation_id': correlation_id})
        finally:
            logger.info("Background poller run completed", extra_fields={'correlation_id': correlation_id})

    async def _get_tracked_members_for_guild(self, guild_id: int) -> list[int]:
        """Get all tracked customer IDs for a specific guild"""
        try:
            async with SessionLocal() as db:
                members = db.query(TrackedMember).filter(TrackedMember.guild_id == guild_id).all()
                return [member.customer_id for member in members]
        except Exception as e:
            logger.error(f"Error getting tracked members for guild {guild_id}: {e}")
            return []

    async def _process_tracked_member(self, guild_id: int, customer_id: int, channel_id: int, correlation_id: str):
        """Process a single tracked member: check for new races and post if needed"""
        logger.info(f"Processing tracked member {customer_id} in guild {guild_id}", extra_fields={'correlation_id': correlation_id})
        
        try:
            # Get recent races for this member
            recent_races = iracing_api.get_recent_races(customer_id)
            
            if not recent_races:
                logger.info(f"No recent races found for member {customer_id} in guild {guild_id}", extra_fields={'correlation_id': correlation_id})
                return
            
            # Get the latest race (first in the list)
            latest_race = recent_races[0]
            latest_subsession_id = latest_race.get('subsession_id')
            
            if not latest_subsession_id:
                logger.warning(f"Latest race for member {customer_id} missing subsession_id. Skipping.", extra_fields={'correlation_id': correlation_id})
                return
            
            logger.info(f"Latest subsession_id for member {customer_id}: {latest_subsession_id}", extra_fields={'correlation_id': correlation_id})
            
            # Check if we've already published this subsession
            last_published = await self.get_last_published_subsession(guild_id, customer_id)
            
            if last_published == latest_subsession_id:
                logger.info(f"Subsession {latest_subsession_id} for member {customer_id} already published. Skipping.", extra_fields={'correlation_id': correlation_id})
                return
            
            # We have a new subsession to publish!
            logger.info(f"New subsession found for member {customer_id}: {latest_subsession_id}", extra_fields={'correlation_id': correlation_id})
            
            # Determine if we need to fetch detailed subsession data
            should_fetch_details = iracing_api.should_fetch_subsession_details(latest_race)
            
            # Fetch detailed race information if needed
            race_details = None
            if should_fetch_details:
                logger.info(f"Fetching detailed results for subsession ID: {latest_subsession_id}", extra_fields={'correlation_id': correlation_id})
                race_details = iracing_api.get_race_details(latest_subsession_id)
            
            # Format the race result
            formatted_result = iracing_api.format_race_result(latest_race, race_details)
            
            # Build Discord message
            message_lines = [
                f"🚨 **New Race Result for Member {customer_id}**",
                "=" * 50,
                f"📅 Timestamp: {formatted_result.get('timestamp', 'N/A')}",
                f"🏎️ Track: {formatted_result.get('track_name', 'N/A')} ({formatted_result.get('track_config', 'N/A')}), {formatted_result.get('track_country', 'N/A')}",
                f"🌦️ Weather: {formatted_result.get('weather_condition', 'N/A')}",
                f"🚗 Car: {formatted_result.get('car_name', 'N/A')} ({formatted_result.get('car_class', 'N/A')})",
                f"🏁 Session Type: {formatted_result.get('session_type', 'N/A')}",
                f"⏱️ Session Duration: {formatted_result.get('session_duration', 'N/A')}",
                f"👥 Field Size: {formatted_result.get('field_size', 'N/A')}",
                f"🏆 Finish Position: {formatted_result.get('finish_position', 'N/A')}",
                f"⚡ Fastest Lap: {formatted_result.get('fastest_lap_time', 'N/A')}",
                f"📊 iRating Delta: {formatted_result.get('irating_delta', 'N/A')}",
                f"🏆 Championship Points: {formatted_result.get('championship_points', 'N/A')}",
                "=" * 50,
                f"📋 Series: {formatted_result.get('series_name', 'N/A')}",
                f"🏟️ Event: {formatted_result.get('event_name', 'N/A')}"
            ]
            
            # Remove empty lines and join into final message
            message = "\n".join(line for line in message_lines if line.strip())
            
            # Post to Discord channel with circuit breaker protection
            try:
                def _post_to_discord():
                    channel = self.get_channel(channel_id)
                    if not channel:
                        logger.error(f"Could not find channel with ID {channel_id} in guild {guild_id}", extra_fields={'correlation_id': correlation_id})
                        return False
                    
                    await channel.send(message)
                    logger.info(f"Successfully posted new race result for member {customer_id} to guild {guild.name}", extra_fields={'correlation_id': correlation_id})
                    
                    # Update last published subsession ID
                    await self.set_last_published_subsession(guild_id, customer_id, latest_subsession_id)
                    logger.info(f"Updated last published subsession ID to {latest_subsession_id} for member {customer_id} in guild {guild_id}", extra_fields={'correlation_id': correlation_id})
                    
                    return True

                success = discord_api_circuit_breaker.call(_post_to_discord)
                return success
                
            except CircuitBreakerError as e:
                logger.error(f"Discord API circuit breaker open: {str(e)}", extra_fields={'correlation_id': correlation_id})
                logger.info("Skipping Discord post due to circuit breaker - will retry later", extra_fields={'correlation_id': correlation_id})
                return False
            except HTTPException as e:
                logger.error(f"Discord API error posting to channel {channel_id}: {str(e)}", extra_fields={'correlation_id': correlation_id})
                if e.status == 403:
                    logger.error("Missing permissions: Ensure the bot has 'Send Messages' and 'Embed Links' permissions in the target channel", extra_fields={'correlation_id': correlation_id})
                return False
            except Exception as e:
                logger.error(f"Error posting to Discord channel {channel_id}: {str(e)}", extra_fields={'correlation_id': correlation_id})
                return False
        
        except Exception as e:
            logger.error(f"Error processing member {customer_id} in guild {guild_id}: {str(e)}", extra_fields={'correlation_id': correlation_id})
            return False

    # ------------------------------
    # Slash Command: /lastrace
    # ------------------------------
    @app_commands.command(name="lastrace", description="Get details about a user's most recent iRacing race")
    @app_commands.describe(customer_id="iRacing customer ID of the user")
    async def lastrace(self, interaction: Interaction, customer_id: str):
        """Handle /lastrace command"""
        correlation_id = generate_correlation_id()
        logger.info(f"/lastrace command called by {interaction.user.id} for customer ID: {customer_id}", extra_fields={'correlation_id': correlation_id})
        
        try:
            # Validate customer ID is a number
            customer_id_int = int(customer_id)
            
            # Defer response to allow longer processing time
            await interaction.response.defer(ephemeral=False)
            
            # Fetch recent races with circuit breaker protection
            try:
                def _get_recent_races():
                    logger.info(f"Fetching recent races for customer ID: {customer_id_int}", extra_fields={'correlation_id': correlation_id})
                    return iracing_api.get_recent_races(customer_id_int)
                
                recent_races = discord_api_circuit_breaker.call(_get_recent_races)
                
                if not recent_races:
                    await interaction.followup.send(
                        f"❌ No recent races found for customer ID {customer_id}. "
                        "The user may have no official races in their history or there was an API error."
                    )
                    return
                
                # Get most recent race
                last_race = recent_races[0]
                subsession_id = last_race.get('subsession_id')
                
                if not subsession_id:
                    await interaction.followup.send(
                        f"❌ Invalid race data for customer ID {customer_id}: Missing subsession ID"
                    )
                    return
                
                # Determine if we need to fetch subsession details
                should_fetch_details = iracing_api.should_fetch_subsession_details(last_race)
                
                # Fetch detailed race information if needed
                race_details = None
                if should_fetch_details:
                    logger.info(f"Fetching detailed results for subsession ID: {subsession_id}", extra_fields={'correlation_id': correlation_id})
                    race_details = iracing_api.get_race_details(subsession_id)
                
                # Format the race result with enhanced details
                formatted_result = iracing_api.format_race_result(last_race, race_details)
                
                # Build response with enhanced fields
                response_lines = [
                    f"🔍 **Last Race Results for Customer ID {customer_id}**",
                    "=" * 50,
                    f"📅 Timestamp: {formatted_result.get('timestamp', 'N/A')}",
                    f"🏎️ Track: {formatted_result.get('track_name', 'N/A')} ({formatted_result.get('track_config', 'N/A')}), {formatted_result.get('track_country', 'N/A')}",
                    f"🌦️ Weather: {formatted_result.get('weather_condition', 'N/A')}",
                    f"🚗 Car: {formatted_result.get('car_name', 'N/A')} ({formatted_result.get('car_class', 'N/A')})",
                    f"🏁 Session Type: {formatted_result.get('session_type', 'N/A')}",
                    f"⏱️ Session Duration: {formatted_result.get('session_duration', 'N/A')}",
                    f"👥 Field Size: {formatted_result.get('field_size', 'N/A')}",
                    f"🏆 Your Position: {formatted_result.get('your_position', 'N/A')}",
                    f"🚦 Start Position: {formatted_result.get('start_position', 'N/A')}",
                    f"🏅 Finish Position: {formatted_result.get('finish_position', 'N/A')}",
                    f"⚡ Fastest Lap: {formatted_result.get('fastest_lap_time', 'N/A')}",
                    f"⏱️ Average Lap: {formatted_result.get('average_lap_time', 'N/A')}",
                    f"📊 iRating Delta: {formatted_result.get('irating_delta', 'N/A')}",
                    f"🏆 Championship Points: {formatted_result.get('championship_points', 'N/A')}",
                    "=" * 50,
                    f"📋 Series: {formatted_result.get('series_name', 'N/A')} ({formatted_result.get('series_type', 'N/A')})",
                    f"🏟️ Event: {formatted_result.get('event_name', 'N/A')}"
                ]
                
                # Remove empty lines and send response
                response = "\n".join(line for line in response_lines if line.strip())
                await interaction.followup.send(response)
                
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker open during /lastrace command: {str(e)}", extra_fields={'correlation_id': correlation_id})
                await interaction.followup.send(
                    "❌ The iRacing API is currently unavailable. Please try again later."
                )
        
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid customer ID. Please provide a numeric iRacing customer ID.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in /lastrace command: {str(e)}", extra_fields={'correlation_id': correlation_id})
            await interaction.followup.send(
                "❌ An error occurred while fetching race data. Please try again later.",
                ephemeral=True
            )

    # ------------------------------
    # Slash Command: /setchannel
    # ------------------------------
    @app_commands.command(name="setchannel", description="Set the channel for iRacing race announcements")
    @app_commands.describe(channel="Text channel for announcements")
    @checks.has_permissions(administrator=True)
    async def setchannel(self, interaction: Interaction, channel: TextChannel):
        """Handle /setchannel command with administrator permission check"""
        correlation_id = generate_correlation_id()
        logger.info(f"/setchannel command called by {interaction.user.id} for channel: {channel.id}", extra_fields={'correlation_id': correlation_id})
        
        # Save the channel ID to database
        success = await self.set_guild_announcement_channel(interaction.guild_id, channel.id)
        
        if success:
            await interaction.response.send_message(
                f"✅ Announcement channel successfully set to {channel.mention}\n"
                f"All future race announcements will be sent to this channel."
            )
        else:
            await interaction.response.send_message(
                "❌ Failed to set announcement channel. Please try again later.",
                ephemeral=True
            )

    # ------------------------------
    # Slash Command: /trackmember
    # ------------------------------
    @app_commands.command(name="trackmember", description="Track a specific iRacing member's activity")
    @app_commands.describe(customer_id="iRacing customer ID of the member to track")
    async def trackmember(self, interaction: Interaction, customer_id: str):
        """Handle /trackmember command"""
        correlation_id = generate_correlation_id()
        logger.info(f"/trackmember command called by {interaction.user.id} for customer ID: {customer_id}", extra_fields={'correlation_id': correlation_id})
        
        try:
            # Validate customer ID is a number
            customer_id_int = int(customer_id)
            
            # Check if already tracked
            if await self.is_member_tracked(interaction.guild_id, customer_id):
                await interaction.response.send_message(
                    f"⚠️ iRacing member {customer_id} is already being tracked in this server."
                )
                return
            
            # Add to tracked members
            success = await self.track_member(interaction.guild_id, customer_id)
            
            if success:
                await interaction.response.send_message(
                    f"📌 Now tracking iRacing member with customer ID {customer_id}\n\n"
                    "🔔 You will receive notifications for:\n"
                    "• New race results\n"
                    "• Practice/l qualifying sessions\n"
                    "• Driver rating changes\n"
                    "• iRacing news related to this member"
                )
            else:
                await interaction.response.send_message(
                    f"❌ Failed to track iRacing member {customer_id}. Please try again later.",
                    ephemeral=True
                )
                
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid customer ID. Please provide a numeric iRacing customer ID.",
                ephemeral=True
            )

    # ------------------------------
    # Error Handling for Commands
    # ------------------------------
    async def on_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        """Handle errors for app commands"""
        correlation_id = generate_correlation_id()
        logger.error(f"Command error for {interaction.command.name}: {error}", extra_fields={'correlation_id': correlation_id})
        
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command. "
                "Administrator permissions are required.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ An error occurred: {str(error)}",
                ephemeral=True
            )

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    """Handle SIGINT and SIGTERM signals for graceful shutdown"""
    logger.info(f"Received signal {sig}: Starting graceful shutdown...")
    
    # Set shutdown flag to prevent new tasks from starting
    bot.is_shutting_down = True
    
    # Stop background tasks
    if bot.background_poller.is_running():
        bot.background_poller.cancel()
        logger.info("Background poller task stopped")
    
    # Clean up resources
    try:
        cleanup_resources()
        logger.info("All resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during resource cleanup: {str(e)}")
    
    # Log final shutdown message
    logger.info("Graceful shutdown completed successfully")
    
    # Exit with success code
    sys.exit(0)

def main():
    """Main entry point for the Discord bot"""
    # Get Discord token from environment variable
    discord_token = os.environ.get('DISCORD_TOKEN')
    
    if not discord_token:
        logger.error("DISCORD_TOKEN environment variable is not set")
        return
    
    try:
        # Create and run the bot
        global bot
        bot = iRacingDiscordBot()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting iRacing Discord Bot...")
        bot.run(discord_token)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return

if __name__ == "__main__":
    main()