import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.iracing_api_client import IRacingAPIClient, IRacingCredentials
from src.models import RaceDetails, DriverPosition, RecentRace

@pytest.mark.asyncio
async def test_client_initialization():
    """Test that IRacingAPIClient initializes correctly"""
    client = IRacingAPIClient("test@example.com", "password123")
    assert client.email == "test@example.com"
    assert client.password == "password123"
    assert client.session is None

@pytest.mark.asyncio
async def test_create_session():
    """Test session creation"""
    # Test that _create_session creates a session when called
    client = IRacingAPIClient("test@example.com", "password123")
    
    # Mock the aiohttp.ClientSession to avoid actual HTTP calls
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session_instance = AsyncMock()
        mock_session_class.return_value = mock_session_instance
        
        await client._create_session()
        
        assert client.session is not None
        mock_session_class.assert_called_once()

@pytest.mark.asyncio
async def test_client_context_manager():
    """Test that IRacingAPIClient works as async context manager"""
    # Test the __aenter__ and __aexit__ methods directly without mocking complex session behavior
    client = IRacingAPIClient("test@example.com", "password123")
    
    # Verify initial state
    assert client.session is None
    
    # This should create a session when entering context manager
    async with client as c:
        assert c.session is not None  # Should have created the session
        
    # The __aexit__ method would normally close the session, but we're just testing that it doesn't crash

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_authenticate_success(mock_session_class):
    """Test successful authentication"""
    # Setup mock response for auth endpoint
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"success": True})
    
    # Configure the session properly to return our mock response when post() is called
    mock_session_instance = AsyncMock()
    mock_session_instance.post.return_value.__aenter__.return_value = mock_response
    mock_session_class.return_value = mock_session_instance
    
    client = IRacingAPIClient("test@example.com", "password123")
    
    # Instead of mocking _create_session, we'll directly set the session to avoid
    # the complex mocking that's causing issues with async context managers
    original_session = client.session
    client.session = mock_session_instance
    
    try:
        result = await client.authenticate()
        assert result is True
    finally:
        # Restore original session
        client.session = original_session

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_authenticate_failure(mock_session_class):
    """Test authentication failure"""
    # Setup mock response for auth endpoint
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.json = AsyncMock(return_value={"error": "Unauthorized"})
    
    # Configure the session properly to return our mock response when post() is called
    mock_session_instance = AsyncMock()
    mock_session_instance.post.return_value.__aenter__.return_value = mock_response
    mock_session_class.return_value = mock_session_instance
    
    client = IRacingAPIClient("test@example.com", "password123")
    
    # Mock the _create_session method to avoid creating a real session 
    with patch.object(client, '_create_session', return_value=None):
        result = await client.authenticate()
        
    assert result is False

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_get_recent_races_success(mock_session_class):
    """Test successful retrieval of recent races"""
    # Setup mock response for get endpoint
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"results": [{"subsession_id": 12345}]})
    
    # Configure the session properly to return our mock response when get() is called
    mock_session_instance = AsyncMock()
    mock_session_instance.get.return_value.__aenter__.return_value = mock_response
    mock_session_class.return_value = mock_session_instance
    
    client = IRacingAPIClient("test@example.com", "password123")
    
    # Instead of mocking _create_session, we'll directly set the session to avoid
    # the complex mocking that's causing issues with async context managers
    original_session = client.session
    client.session = mock_session_instance
    
    try:
        result = await client.get_recent_races(12345)
        assert result is not None
        assert "results" in result
    finally:
        # Restore original session
        client.session = original_session

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_get_recent_races_failure(mock_session_class):
    """Test failure when retrieving recent races"""
    # Setup mock response for get endpoint
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.json = AsyncMock(return_value={"error": "Server Error"})
    
    # Configure the session properly to return our mock response when get() is called
    mock_session_instance = AsyncMock()
    mock_session_instance.get.return_value.__aenter__.return_value = mock_response
    mock_session_class.return_value = mock_session_instance
    
    client = IRacingAPIClient("test@example.com", "password123")
    
    # Mock the _create_session method to avoid creating a real session 
    with patch.object(client, '_create_session', return_value=None):
        result = await client.get_recent_races(12345)
        
    assert result is None

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_get_session_results_success(mock_session_class):
    """Test successful retrieval of session results"""
    # Setup mock response for get endpoint
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"results": [{"cust_id": 12345}]})
    
    # Configure the session properly to return our mock response when get() is called
    mock_session_instance = AsyncMock()
    mock_session_instance.get.return_value.__aenter__.return_value = mock_response
    mock_session_class.return_value = mock_session_instance
    
    client = IRacingAPIClient("test@example.com", "password123")
    
    # Instead of mocking _create_session, we'll directly set the session to avoid
    # the complex mocking that's causing issues with async context managers
    original_session = client.session
    client.session = mock_session_instance
    
    try:
        result = await client.get_session_results(12345)
        assert result is not None
        assert "results" in result
    finally:
        # Restore original session
        client.session = original_session

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_get_session_results_failure(mock_session_class):
    """Test failure when retrieving session results"""
    # Setup mock response for get endpoint
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.json = AsyncMock(return_value={"error": "Server Error"})
    
    # Configure the session properly to return our mock response when get() is called
    mock_session_instance = AsyncMock()
    mock_session_instance.get.return_value.__aenter__.return_value = mock_response
    mock_session_class.return_value = mock_session_instance
    
    client = IRacingAPIClient("test@example.com", "password123")
    
    # Mock the _create_session method to avoid creating a real session 
    with patch.object(client, '_create_session', return_value=None):
        result = await client.get_session_results(12345)
        
    assert result is None

def test_race_details_model():
    """Test RaceDetails dataclass"""
    race = RaceDetails(
        series_name="Formula 1",
        track_name="Monaco Grand Prix",
        field_size=20,
        positions=[],
        irating_delta=50,
        points=100,
        timestamp="2023-01-01T12:00:00Z",
        subsession_id=12345,
        customer_id=54321
    )
    
    assert race.series_name == "Formula 1"
    assert race.track_name == "Monaco Grand Prix"
    assert race.field_size == 20
    assert race.irating_delta == 50
    assert race.points == 100

def test_driver_position_model():
    """Test DriverPosition dataclass"""
    driver = DriverPosition(
        cust_id=12345,
        display_name="John Doe",
        finish_position=1,
        laps_complete=50,
        irating_change=25,
        points=100,
        car_number="1",
        car_model="Ferrari F1"
    )
    
    assert driver.display_name == "John Doe"
    assert driver.finish_position == 1
    assert driver.car_model == "Ferrari F1"

def test_recent_race_model():
    """Test RecentRace dataclass"""
    race = RecentRace(
        subsession_id=12345,
        start_time="2023-01-01T12:00:00Z",
        series_name="Formula 1",
        track_name="Monaco Grand Prix",
        field_size=20,
        customer_id=54321
    )
    
    assert race.series_name == "Formula 1"
    assert race.field_size == 20