from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class RaceDetails:
    """Data class for storing iRacing race details"""
    series_name: str
    track_name: str
    field_size: int
    positions: List[dict]  # List of driver positions
    irating_delta: int
    points: int
    timestamp: datetime
    subsession_id: int
    customer_id: int
    
    def __post_init__(self):
        """Convert timestamp string to datetime object if needed"""
        if isinstance(self.timestamp, str):
            try:
                self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, keep as string
                pass

@dataclass
class DriverPosition:
    """Data class for individual driver position in a race"""
    cust_id: int
    display_name: str
    finish_position: int
    laps_complete: int
    irating_change: int
    points: int
    car_number: str
    car_model: str

@dataclass
class RecentRace:
    """Data class for recent race information"""
    subsession_id: int
    start_time: datetime
    series_name: str
    track_name: str
    field_size: int
    customer_id: int