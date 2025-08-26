#!/usr/bin/env python3

"""
Script to retrieve and display detailed information about a user's most recent iRacing race.
Uses the iracingdataapi library for authentication and API calls.
"""

# Import necessary modules
from iracingdataapi.client import irDataClient
from typing import Optional, Dict, List, Any
import sys
import datetime
import getpass
import os

def authenticate() -> irDataClient:
    """
    Handle user authentication with iRacing.
    Supports environment variables for credentials: IRACING_USERNAME, IRACING_PASSWORD
    
    Returns:
        irDataClient: Authenticated client instance
        
    Raises:
        SystemExit: If authentication fails or is cancelled
    """
    print("=== iRacing Last Race Details ===")
    
    # Get credentials - first check environment variables, then fall back to input
    username = os.environ.get('IRACING_USERNAME')
    password = os.environ.get('IRACING_PASSWORD')
    
    # Fall back to user input if not provided via environment variables
    if not username:
        username = input("Enter iRacing username: ").strip()
        if not username:
            print("Error: Username cannot be empty")
            sys.exit(1)
    
    if not password:
        password = getpass.getpass("Enter iRacing password: ").strip()
        if not password:
            print("Error: Password cannot be empty")
            sys.exit(1)
    
    try:
        # Create client instance and authenticate
        client = irDataClient(username=username, password=password)
        
        # Try to get member info to ensure authentication worked and get cust_id
        member_info = client.member_info()
        if not member_info or 'cust_id' not in member_info:
            print("Error: Could not retrieve customer information after authentication")
            sys.exit(1)
            
        client.cust_id = member_info['cust_id']
        print("Authentication successful!")
        return client
        
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        print("Please check your credentials and try again.")
        sys.exit(1)

def get_recent_races(client: irDataClient) -> Dict[str, Any]:
    """
    Fetch the most recent races for the authenticated user.
    
    Args:
        client: Authenticated irDataClient instance
        
    Returns:
        Dict: Race data containing 'races' list
        
    Raises:
        SystemExit: If no races are found or API call fails
    """
    try:
        # Get recent races (most recent first according to PRP)
        recent_races = client.stats_member_recent_races()
        
        # Validate response format and check for races
        if not isinstance(recent_races, dict) or 'races' not in recent_races:
            print("Error: Invalid response format from API")
            sys.exit(1)
            
        races = recent_races['races']
        
        if not races:
            print("No recent races found in your iRacing account")
            sys.exit(0)  # Exit cleanly, not an error
            
        print(f"Found {len(races)} recent race(s)")
        return recent_races
        
    except Exception as e:
        print(f"Error fetching recent races: {str(e)}")
        sys.exit(1)

def get_race_details(client: irDataClient, subsession_id: int) -> Dict[str, Any]:
    """
    Fetch detailed information for a specific race subsession.
    
    Args:
        client: Authenticated irDataClient instance
        subsession_id: Unique identifier for the race subsession
        
    Returns:
        Dict: Detailed race results and session information
        
    Raises:
        SystemExit: If API call fails or data parsing issues occur
    """
    try:
        # Get detailed results with license information
        race_details = client.result(subsession_id=subsession_id, include_licenses=True)
        
        # Validate basic structure based on actual API response
        required_fields = ['session_id', 'subsession_id', 'session_results', 'track', 'start_time']
        for field in required_fields:
            if field not in race_details:
                print(f"Error: Missing required field '{field}' in race details")
                sys.exit(1)
        
        # Debug: Print session_results structure
        print(f"DEBUG: session_results type: {type(race_details.get('session_results'))}")
        print(f"DEBUG: session_results value: {race_details.get('session_results')}")
        
        # Extract car information from the first result (race session)
        car_info = {
            'name': 'Unknown',
            'class': 'Unknown'
        }
        
        if race_details.get('session_results') and isinstance(race_details['session_results'], list):
            for session in race_details['session_results']:
                if isinstance(session, dict) and session.get('simsession_type_name') == 'Race':
                    if session.get('results') and isinstance(session['results'], list) and session['results']:
                        car_info = {
                            'name': session['results'][0].get('car_name', 'Unknown'),
                            'class': session['results'][0].get('car_class_name', 'Unknown')
                        }
                    break

        # Transform the response to match the expected structure in the PRP
        transformed = {
            'session_info': {
                'start_time': race_details['start_time'],
                'track': {
                    'name': race_details.get('track', {}).get('track_name', 'Unknown Track'),
                    'config': race_details.get('track', {}).get('config_name', 'Unknown Config')
                },
                'car': car_info,
                'event_type': race_details.get('event_type_name', 'Race'),
                'num_drivers': race_details.get('num_drivers', 0)
            },
            'results': {
                'drivers': race_details.get('session_results', []),
                'your_position': None  # We'll populate this later
            }
        }
        
        print("Successfully retrieved and transformed race details")
        return transformed
        
    except Exception as e:
        print(f"Error fetching race details: {str(e)}")
        sys.exit(1)

def get_lap_data(client: irDataClient, subsession_id: int, cust_id: int) -> List[Any]:
    """
    Fetch lap data for a specific user in a race subsession.
    
    Args:
        client: Authenticated irDataClient instance
        subsession_id: Unique identifier for the race subsession
        cust_id: iRacing customer ID of the user
        
    Returns:
        List: Lap data entries
        
    Raises:
        SystemExit: If API call fails or data parsing issues occur
    """
    try:
        # Get lap data for the race session (simsession_number=0 for race according to PRP)
        lap_data = client.result_lap_data(
            subsession_id=subsession_id,
            simsession_number=0,  # 0 = race session
            cust_id=cust_id
        )
        
        print(f"Retrieved lap data for {len(lap_data)} laps")
        return lap_data
        
    except Exception as e:
        print(f"Error fetching lap data: {str(e)}")
        sys.exit(1)

def find_user_position(drivers: List[Any], cust_id: int) -> Optional[int]:
    """
    Find the user's position in the driver results list.
    
    Args:
        drivers: List of driver results
        cust_id: iRacing customer ID of the user
        
    Returns:
        Optional[int]: User's position (1-based) or None if not found
    """
    for i, driver in enumerate(drivers, 1):  # 1-based indexing for positions
        if driver.get('cust_id') == cust_id:
            return i
    return None

def format_timestamp(timestamp: str) -> str:
    """
    Format iRacing timestamp string into a human-readable format.
    
    Args:
        timestamp: iRacing timestamp string (format: 'YYYY-MM-DD HH:MM:SS')
        
    Returns:
        str: Formatted timestamp string
    """
    try:
        # Convert to datetime object and format
        dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%A, %B %d, %Y at %I:%M %p %Z')
    except ValueError:
        return timestamp  # Return original if format doesn't match

def display_race_summary(race_details: Dict[str, Any], lap_data: List[Any]) -> None:
    """
    Display a user-friendly summary of the race results.
    
    Args:
        race_details: Detailed race information from API
        lap_data: Lap data for the user
    """
    session_info = race_details['session_info']
    results = race_details['results']
    
    print("\n" + "="*50)
    print("          LAST RACE DETAILS SUMMARY")
    print("="*50)
    
    # Basic race information
    print(f"\n📅 Race Date: {format_timestamp(session_info['start_time'])}")
    print(f"🏎️  Track: {session_info['track']['name']} ({session_info['track']['config']})")
    print(f"🚗 Car: {session_info['car']['name']} ({session_info['car']['class']})")
    print(f"🏁 Session Type: {session_info['event_type'].capitalize()}")
    print(f"👥 Competitors: {len(results['drivers'])} drivers")
    
    # User position and stats
    if 'your_position' in results:
        print(f"🏆 Your Position: {results['your_position']}")
    
    # Lap data summary
    if lap_data:
        print("\n📊 Lap Statistics:")
        print(f"   Total Laps Completed: {len(lap_data)}")
        
        # Calculate basic lap metrics if data is available
        if lap_data and isinstance(lap_data[0], dict):
            lap_times = []
            for lap in lap_data:
                if 'lap_time' in lap and lap['lap_time'] > 0:
                    lap_times.append(lap['lap_time'])
            
            if lap_times:
                print(f"   Fastest Lap Time: {min(lap_times):.3f} seconds")
                print(f"   Average Lap Time: {sum(lap_times)/len(lap_times):.3f} seconds")
    
    print("\n" + "="*50)
    print("          TOP 5 FINISHERS")
    print("="*50)
    
    # Display top 5 finishers
    top_finishers = results['drivers'][:5]
    for i, driver in enumerate(top_finishers, 1):
        position = driver.get('position', 'N/A')
        name = driver.get('name', 'N/A')
        car = driver.get('car', {}).get('name', 'N/A')
        print(f"{i}. {position}. {name} - {car}")

def main() -> None:
    """Main entry point for the script"""
    try:
        # Step 1: Authenticate with iRacing
        print("🔒 Authenticating with iRacing...")
        client = authenticate()
        
        # Step 2: Get recent races
        print("\n📋 Fetching recent races...")
        recent_races = get_recent_races(client)
        
        # Step 3: Get most recent race details
        last_race = recent_races['races'][0]
        subsession_id = last_race['subsession_id']
        cust_id = client.cust_id  # Get authenticated user's ID
        
        print(f"\n🔍 Analyzing most recent race (Subsession ID: {subsession_id})...")
        race_details = get_race_details(client, subsession_id)
        
        # Find user's position in results
        if race_details['results']['drivers']:
            user_position = find_user_position(race_details['results']['drivers'], cust_id)
            if user_position is not None:
                race_details['results']['your_position'] = user_position
                print(f"Found your position: {user_position}")
            else:
                print("User not found in results list")
        
        # Step 4: Get user's lap data
        print("\n📊 Fetching your lap data...")
        lap_data = get_lap_data(client, subsession_id, cust_id)
        
        # Step 5: Display results
        print("\n📝 Generating race summary...")
        display_race_summary(race_details, lap_data)
        
        print("\n✅ Operation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in main workflow: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()