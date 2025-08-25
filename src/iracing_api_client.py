import asyncio
import aiohttp
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IRacingCredentials:
    email: str
    password: str

class IRacingAPIClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://members-ng.iracing.com"
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._create_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _create_session(self):
        """Create and configure aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'iRacing-Last-Race-Printer/1.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
            
    async def authenticate(self) -> bool:
        """Authenticate with iRacing API using email and password"""
        if not self.session:
            await self._create_session()
            
        try:
            auth_data = {
                "email": self.email,
                "password": self.password
            }
            
            # Note: This is a simplified version. Real implementation 
            # would need to handle 2FA and proper session management
            async with self.session.post(
                f"{self.base_url}/auth", 
                json=auth_data
            ) as response:
                if response.status == 200:
                    logger.info("Successfully authenticated with iRacing API")
                    return True
                else:
                    logger.error(f"Authentication failed with status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
            
    async def get_recent_races(self, customer_id: int) -> Optional[Dict[Any, Any]]:
        """Get recent races for a given customer ID"""
        if not self.session:
            await self._create_session()
            
        try:
            async with self.session.get(
                f"{self.base_url}/data/stats/member_recent_races?cust_id={customer_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved recent races for customer {customer_id}")
                    return data
                else:
                    logger.error(f"Failed to get recent races: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting recent races: {e}")
            return None
            
    async def get_session_results(self, subsession_id: int) -> Optional[Dict[Any, Any]]:
        """Get detailed results for a specific race session"""
        if not self.session:
            await self._create_session()
            
        try:
            async with self.session.get(
                f"{self.base_url}/data/results/get?subsession_id={subsession_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved session results for subsession {subsession_id}")
                    return data
                else:
                    logger.error(f"Failed to get session results: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting session results: {e}")
            return None