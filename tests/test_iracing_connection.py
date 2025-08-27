#!/usr/bin/env python3

"""
Test script to verify iRacing API connection and functionality
"""

import sys
import os
from src.iracing_api import iracing_api

def test_iracing_connection():
    """Test if we can connect to iRacing API and get recent races"""
    
    print("Testing iRacing API connection...")
    
    # Try to authenticate
    print("1. Authenticating with iRacing...")
    success = iracing_api.authenticate()
    print(f"   Authentication successful: {success}")
    
    if not success:
        print("   Failed to authenticate - check credentials")
        return False
    
    # Try to get recent races for a test customer ID (using the authenticated user's ID)
    print("2. Fetching recent races...")
    recent_races = iracing_api.get_recent_races(iracing_api.cust_id)
    
    if recent_races:
        print(f"   Found {len(recent_races)} recent races")
        print(f"   First race: {recent_races[0].get('track_name', 'Unknown')}")
        
        # Try to get race details for the first race
        subsession_id = recent_races[0].get('subsession_id')
        if subsession_id:
            print("3. Fetching race details...")
            race_details = iracing_api.get_race_details(subsession_id)
            if race_details:
                print("   Successfully fetched race details")
                formatted = iracing_api.format_race_result(recent_races[0], race_details)
                print(f"   Formatted result: {formatted.get('track_name')}, {formatted.get('timestamp')}")
    else:
        print("   No recent races found")
    
    return True

if __name__ == "__main__":
    try:
        test_iracing_connection()
        print("\n✅ iRacing API test completed")
    except Exception as e:
        print(f"\n❌ Error in iRacing API test: {e}")
        sys.exit(1)