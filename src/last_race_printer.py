#!/usr/bin/env python3
"""
iRacing Last Race Printer
Fetches and prints details of the last race for a given iRacing member.
"""

import asyncio
import os
import sys
import logging
from typing import Optional
from dataclasses import asdict

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.iracing_api_client import IRacingAPIClient, IRacingCredentials
from src.models import RaceDetails

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fetch_last_race_details(customer_id: int, email: str, password: str) -> Optional[RaceDetails]:
    """Fetch and parse details of the last race for a given customer ID"""
    
    try:
        async with IRacingAPIClient(email, password) as client:
            # Authenticate first
            if not await client.authenticate():
                logger.error("Failed to authenticate with iRacing API")
                return None
                
            # Get recent races
            recent_races = await client.get_recent_races(customer_id)
            if not recent_races or 'results' not in recent_races:
                logger.error("No recent races found or invalid response")
                return None
                
            # Get the most recent race (first in list)
            if not recent_races['results']:
                logger.error("No races found for customer")
                return None
                
            latest_race = recent_races['results'][0]
            subsession_id = latest_race.get('subsession_id')
            
            # Fetch detailed results for that race
            race_results = await client.get_session_results(subsession_id)
            if not race_results:
                logger.error("Failed to get race results")
                return None
                
            # Parse the race details (simplified parsing based on typical iRacing API structure)
            # This would need to be adjusted based on actual API response format
            series_name = latest_race.get('series_name', 'Unknown Series')
            track_name = latest_race.get('track_name', 'Unknown Track')
            field_size = latest_race.get('field_size', 0)
            
            # Extract positions from race results
            positions = []
            if 'results' in race_results and race_results['results']:
                for result in race_results['results']:
                    position_data = {
                        'cust_id': result.get('cust_id'),
                        'display_name': result.get('display_name'),
                        'finish_position': result.get('finish_position'),
                        'laps_complete': result.get('laps_complete'),
                        'irating_change': result.get('irating_change'),
                        'points': result.get('points'),
                        'car_number': result.get('car_number'),
                        'car_model': result.get('car_model')
                    }
                    positions.append(position_data)
            
            # Calculate iRating delta and points (simplified)
            irating_delta = 0
            points = 0
            
            # Find the player's position in the race
            for pos in positions:
                if pos['cust_id'] == customer_id:
                    irating_delta = pos['irating_change']
                    points = pos['points']
                    break
                    
            # Get timestamp from latest_race
            timestamp_str = latest_race.get('start_time', '')
            
            # Create RaceDetails object
            race_details = RaceDetails(
                series_name=series_name,
                track_name=track_name,
                field_size=field_size,
                positions=positions,
                irating_delta=irating_delta,
                points=points,
                timestamp=timestamp_str,
                subsession_id=subsession_id,
                customer_id=customer_id
            )
            
            return race_details
            
    except Exception as e:
        logger.error(f"Error fetching last race details: {e}")
        return None

def print_race_details(race_details: RaceDetails):
    """Print formatted race details"""
    if not race_details:
        print("No race details to display")
        return
        
    print("=" * 60)
    print("iRACING LAST RACE DETAILS")
    print("=" * 60)
    print(f"Series: {race_details.series_name}")
    print(f"Track: {race_details.track_name}")
    print(f"Field Size: {race_details.field_size} drivers")
    print(f"Timestamp: {race_details.timestamp}")
    print(f"Subsession ID: {race_details.subsession_id}")
    print(f"iRating Delta: {race_details.irating_delta}")
    print(f"Points Earned: {race_details.points}")
    print("-" * 60)
    print("RACE RESULTS:")
    print("-" * 60)
    
    # Print positions
    for position in race_details.positions:
        if position['finish_position'] <= 10:  # Only show top 10 for brevity
            print(f"{position['finish_position']:2d}. {position['display_name']:<20} "
                  f"Car #{position['car_number']:<3} "
                  f"Points: {position['points']:3d} "
                  f"iRating: {position['irating_change']:4d}")

async def main():
    """Main function to run the last race printer"""
    
    # Get customer ID from environment variable or command line argument
    customer_id = os.environ.get('IRACING_CUSTOMER_ID')
    email = os.environ.get('IRACING_EMAIL')
    password = os.environ.get('IRACING_PASSWORD')
    
    if not customer_id:
        print("Error: IRACING_CUSTOMER_ID environment variable not set")
        print("Usage: export IRACING_CUSTOMER_ID=<customer_id> && python last_race_printer.py")
        sys.exit(1)
        
    if not email or not password:
        print("Error: IRACING_EMAIL and IRACING_PASSWORD environment variables not set")
        print("Usage: export IRACING_EMAIL=<email> && export IRACING_PASSWORD=<password>")
        sys.exit(1)
        
    customer_id = int(customer_id)
    
    # Fetch race details
    logger.info(f"Fetching last race details for customer ID {customer_id}")
    race_details = await fetch_last_race_details(customer_id, email, password)
    
    if race_details:
        print_race_details(race_details)
        logger.info("Successfully printed race details")
    else:
        print("Failed to fetch race details")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())