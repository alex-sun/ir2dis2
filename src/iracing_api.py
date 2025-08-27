#!/usr/bin/env python3

"""
iRacing API wrapper for Discord bot integration.
Handles authentication, API calls, and data formatting for race results.
"""

from iracingdataapi.client import irDataClient
from typing import Optional, Dict, List, Any
import os
from datetime import datetime

# Import logging configuration and circuit breaker
from src.logging_config import get_logger, add_correlation_id
from src.circuit_breaker import iracing_api_circuit_breaker, CircuitBreakerError

# Set up logging with correlation ID
logger = get_logger(__name__)
add_correlation_id(logger, "api-client")

class iRacingAPIError(Exception):
    """Custom exception for iRacing API errors"""
    pass

class iRacingClient:
    """Wrapper class for iRacing API interactions"""
    
    def __init__(self):
        """Initialize the iRacing client with credentials from environment variables"""
        self.username = os.environ.get('IRACING_USERNAME')
        self.password = os.environ.get('IRACING_PASSWORD')
        self.client = None
        self.cust_id = None
        self.subsession_cache = {}  # Cache for subsession details: {subsession_id: race_details}
        self.cache_timeout = 3600  # Cache timeout in seconds (1 hour)
        
        if not self.username or not self.password:
            raise iRacingAPIError("iRacing credentials not found in environment variables")

    def authenticate(self) -> bool:
            """
            Authenticate with iRacing API using environment variables.
            Returns True if authentication succeeds, False otherwise.
            """
            try:
                logger.info("Authenticating with iRacing API...")
                
                # Create client and authenticate (circuit breaker protects this call)
                def _authenticate():
                    self.client = irDataClient(username=self.username, password=self.password)
                    
                    # Get member info to verify authentication and get cust_id
                    member_info = self.client.member_info()
                    if not member_info or 'cust_id' not in member_info:
                        logger.error("Authentication failed: Could not retrieve customer information")
                        return False
                    
                    self.cust_id = member_info['cust_id']
                    logger.info(f"Authentication successful for cust_id: {self.cust_id}")
                    return True
    
                return iracing_api_circuit_breaker.call(_authenticate)
    
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker open: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                return False

    def get_recent_races(self, customer_id: int) -> Optional[List[Dict[str, Any]]]:
            """
            Fetch recent official races for a specific member.
            
            Args:
                customer_id: iRacing customer ID
                
            Returns:
                List of recent races or None if no races found/error occurred
            """
            try:
                if not self.client:
                    if not self.authenticate():
                        return None
                    
                logger.info(f"Fetching recent races for customer_id: {customer_id}")
                
                # Get recent races using circuit breaker to prevent repeated failures
                def _get_recent_races():
                    recent_races_response = self.client.stats_member_recent_races(cust_id=customer_id)
                    
                    if not recent_races_response or 'races' not in recent_races_response:
                        logger.warning("Invalid response format from stats_member_recent_races")
                        return None
                         
                    races = recent_races_response['races']
                    
                    if not races:
                        logger.info("No recent races found for this member")
                        return None
                         
                    logger.info(f"Found {len(races)} recent races for customer_id: {customer_id}")
                    return races
    
                return iracing_api_circuit_breaker.call(_get_recent_races)
    
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker open: {str(e)}")
                # Return empty result as fallback during circuit breaker open state
                logger.info("Returning empty races list as fallback due to circuit breaker")
                return None
            except Exception as e:
                logger.error(f"Error fetching recent races: {str(e)}")
                return None

    def should_fetch_subsession_details(self, race: Dict[str, Any]) -> bool:
        """
        Determine if we need to fetch subsession details for a race.
        
        Returns True if basic race data is insufficient or if we want to enhance the display
        with additional details from subsession data.
        """
        try:
            # Always fetch subsession details for enhanced display
            # This provides additional fields like track country, weather, session duration, etc.
            return True
            
            # Alternative logic: Only fetch if basic data is insufficient
            # return (race.get('track_name') == 'N/A' or
            #         race.get('car_name') == 'N/A' or
            #         race.get('num_drivers') is None or
            #         race.get('finish_position') == 'N/A')
            
        except Exception as e:
            logger.error(f"Error determining if subsession details should be fetched: {str(e)}")
            return True  # Default to fetching details if there's an error

    def get_race_details(self, subsession_id: int) -> Optional[Dict[str, Any]]:
            """
            Fetch detailed information for a specific race subsession.
            
            Args:
                subsession_id: Unique identifier for the race subsession
                
            Returns:
                Dict with race details or None if error occurred
            """
            try:
                # Check cache first
                now = datetime.utcnow().timestamp()
                cache_entry = self.subsession_cache.get(str(subsession_id))
                
                if cache_entry:
                    cached_time, race_details = cache_entry
                    # Return cached data if it's not expired (within cache_timeout seconds)
                    if now - cached_time < self.cache_timeout:
                        logger.info(f"Using cached subsession details for subsession_id: {subsession_id}")
                        return race_details
                
                # If not in cache or expired, fetch from API with circuit breaker protection
                if not self.client:
                    if not self.authenticate():
                        return None
                    
                logger.info(f"Fetching details for subsession_id: {subsession_id}")
                
                # Get detailed results using circuit breaker to prevent repeated failures
                def _get_race_details():
                    race_details = self.client.result(subsession_id=subsession_id, include_licenses=True)
                    
                    # Validate basic structure
                    required_fields = ['session_id', 'subsession_id', 'session_results', 'track', 'start_time']
                    for field in required_fields:
                        if field not in race_details:
                            logger.error(f"Missing required field '{field}' in race details")
                            return None
                    
                    # Store in cache with timestamp
                    self.subsession_cache[str(subsession_id)] = (now, race_details)
                    
                    return race_details
    
                return iracing_api_circuit_breaker.call(_get_race_details)
    
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker open: {str(e)}")
                # Return cached data if available as fallback
                cache_entry = self.subsession_cache.get(str(subsession_id))
                if cache_entry:
                    logger.info(f"Returning cached race details for subsession_id: {subsession_id} as fallback")
                    return cache_entry[1]
                logger.info("No cached data available - returning None as fallback")
                return None
            except Exception as e:
                logger.error(f"Error fetching race details: {str(e)}")
                return None
    def format_race_result(self, race: Dict[str, Any], race_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format race result into a user-friendly structure with required fields.
        
        Args:
            race: Basic race information from stats_member_recent_races
            race_details: Optional detailed race information from result()
            
        Returns:
            Formatted race result with required fields
        """
        try:
            # Start with all fields set to N/A
            formatted = {
                'timestamp': 'N/A',
                'series_name': 'N/A',
                'track_name': 'N/A',
                'track_config': 'N/A',
                'car_name': 'N/A',
                'car_class': 'N/A',
                'session_type': 'N/A',
                'field_size': 'N/A',
                'start_position': 'N/A',
                'finish_position': 'N/A',
                'irating_delta': 'N/A',
                'championship_points': 'N/A',
                'series_type': 'N/A',
                'event_name': 'N/A',
                'track_country': 'N/A',
                'weather_condition': 'N/A',
                'session_duration': 'N/A',
                'your_position': 'N/A',
                'fastest_lap_time': 'N/A',
                'average_lap_time': 'N/A',
                'raw_data': race
            }
            
            # Populate fields from race data if available
            if race:
                formatted['timestamp'] = self._format_timestamp(race.get('start_time', '')) or 'N/A'
                formatted['series_name'] = race.get('series_name') or 'N/A'
                formatted['track_name'] = race.get('track_name') or 'N/A'
                formatted['track_config'] = race.get('track_config') or 'N/A'
                formatted['car_name'] = race.get('car_name') or 'N/A'
                formatted['car_class'] = race.get('car_class') or 'N/A'
                formatted['session_type'] = race.get('session_type_name') or 'N/A'
                
                # Convert field_size to string if available
                num_drivers = race.get('num_drivers')
                formatted['field_size'] = str(num_drivers) if num_drivers is not None else 'N/A'
                
                formatted['start_position'] = race.get('start_position') or 'N/A'
                formatted['finish_position'] = race.get('finish_position') or 'N/A'
                formatted['irating_delta'] = race.get('irating_delta') or 'N/A'
                formatted['championship_points'] = race.get('championship_points') or 'N/A'
            
            # Add detailed information if available
            if race_details:
                # Extract session information
                if race_details.get('session_info') and isinstance(race_details['session_info'], dict):
                    track_info = race_details['session_info'].get('track', {})
                    formatted['track_name'] = track_info.get('track_name') or formatted['track_name']
                    formatted['track_config'] = track_info.get('config_name') or formatted['track_config']
                    formatted['track_country'] = track_info.get('country', 'N/A')
                    
                    # Extract event/series information
                    event_info = race_details['session_info'].get('event', {})
                    formatted['series_name'] = event_info.get('series_name', formatted['series_name'])
                    formatted['series_type'] = event_info.get('series_type', 'N/A')
                    formatted['event_name'] = event_info.get('event_name', 'N/A')
                    
                    # Extract weather information if available
                    weather_info = race_details['session_info'].get('weather', {})
                    if weather_info:
                        condition = weather_info.get('condition', 'N/A')
                        temp = weather_info.get('temp', 'N/A')
                        formatted['weather_condition'] = f"{condition} ({temp}°C)" if temp else condition
                
                # Extract car info from first driver if available
                if race_details.get('session_results') and isinstance(race_details['session_results'], list):
                    for session in race_details['session_results']:
                        if isinstance(session, dict) and session.get('simsession_type_name') == 'Race':
                            if session.get('results') and isinstance(session['results'], list):
                                if session['results']:
                                    # Get user's result if we have a customer ID
                                    if hasattr(self, 'cust_id') and self.cust_id:
                                        for driver in session['results']:
                                            if driver.get('cust_id') == self.cust_id:
                                                formatted['your_position'] = str(driver.get('finish_position', 'N/A'))
                                                formatted['fastest_lap_time'] = self._format_lap_time(driver.get('fastest_lap', 0))
                                                formatted['average_lap_time'] = self._format_lap_time(driver.get('average_lap', 0))
                                                break
                                    
                                    # Fall back to first driver if user not found
                                    driver = session['results'][0]
                                    formatted['car_name'] = driver.get('car_name') or formatted['car_name']
                                    formatted['car_class'] = driver.get('car_class_name') or formatted['car_class']
                                    
                                    # Get field size from number of results
                                    formatted['field_size'] = str(len(session['results'])) if session['results'] else 'N/A'
                            
                            # Extract session duration
                            session_duration = session.get('session_duration', 0)
                            formatted['session_duration'] = self._format_session_duration(session_duration) if session_duration else 'N/A'
                            break
            
            # Ensure all fields are strings and not empty
            for key in list(formatted.keys()):
                if key != 'raw_data':  # Skip raw_data as it should preserve original type
                    if formatted[key] == '':
                        formatted[key] = 'N/A'
                    elif not isinstance(formatted[key], str):
                        formatted[key] = str(formatted[key])
            
            return formatted
        except Exception as e:
            logger.error(f"Error formatting race result: {str(e)}")
            # Return what we have even if there's an error
            return race

    def _format_timestamp(self, timestamp: str) -> str:
        """Format iRacing timestamp string into a human-readable format"""
        try:
            # Convert to datetime object and format
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except ValueError:
            return timestamp  # Return original if format doesn't match
            
    def _format_lap_time(self, lap_time: float) -> str:
        """Format lap time in seconds to a human-readable string (MM:SS.mmm)"""
        try:
            if lap_time <= 0 or not isinstance(lap_time, (int, float)):
                return 'N/A'
                
            minutes = int(lap_time // 60)
            seconds = int(lap_time % 60)
            milliseconds = int((lap_time % 1) * 1000)
            return f"{minutes:01d}:{seconds:02d}.{milliseconds:03d}"
        except (ValueError, TypeError):
            return 'N/A'
            
    def _format_session_duration(self, duration: int) -> str:
        """Format session duration in seconds to a human-readable string (HH:MM:SS)"""
        try:
            if duration <= 0 or not isinstance(duration, int):
                return 'N/A'
                
            hours = duration // 3600
            remaining = duration % 3600
            minutes = remaining // 60
            seconds = remaining % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
        except (ValueError, TypeError):
            return 'N/A'


# Singleton instance for the bot to use
iracing_api = iRacingClient()