# PRP: iRacing Last Race Printer

## Feature Description
Create a Python script that uses the jasondilworth56/iracingdataapi library to fetch and print details of the last race for a given iRacing member.

## Research Process

### Codebase Analysis
Based on the existing documentation, this project is an iRacing Discord bot that:
- Uses discord.py 2.x for Discord integration
- Employs aiohttp for async HTTP requests to iRacing API
- Uses SQLite for persistence with aiosqlite
- Follows a modular structure with separate files for bot logic, database operations, and API interactions

### External Research
The iRacing data API requires:
- Authentication against `https://members-ng.iracing.com/auth` with iRacing credentials
- Use of `/data/stats/member_recent_races?cust_id={customer_id}` endpoint to get recent races
- Use of `/data/results/get?subsession_id={subsession_id}` endpoint for detailed results
- Session management with cookies and proper error handling

### User Clarification
The feature should integrate with the existing iRacing Discord bot architecture, following the same patterns for:
- API authentication
- HTTP client setup
- Error handling
- Data parsing

## Implementation Blueprint

### Pseudocode Approach
```
1. Initialize iRacing API client with credentials
2. Authenticate with iRacing using provided credentials
3. Get recent races for a given customer ID
4. Select the most recent race (first in list)
5. Fetch detailed results for that race subsession
6. Format and print race details
```

### Key Files to Reference
- `src/iracing_api.py` - For API interaction patterns
- `src/models.py` - For data structures 
- `src/settings.py` - For environment variable handling

### Error Handling Strategy
- Handle authentication failures gracefully
- Implement retry logic for network errors
- Gracefully handle missing data fields
- Log errors without exposing credentials

## Validation Gates

```bash
# Syntax/Style
ruff check --fix && mypy .

# Unit Tests  
uv run pytest tests/ -v
```

## Implementation Tasks

1. **Create API client module** (`iracing_api_client.py`)
   - Implement authentication logic
   - Create methods for recent races and session results endpoints
   - Handle session management with cookies

2. **Implement data models** (`models.py`)
   - Define dataclasses for race details
   - Include fields for: series name, track name, field size, positions, iRating delta, points, timestamp

3. **Create main script** (`last_race_printer.py`)
   - Parse command line arguments or environment variables for customer ID
   - Initialize API client
   - Fetch and display race details
   - Handle errors gracefully

4. **Add unit tests** (`tests/test_iracing_api.py`)
   - Test authentication flow
   - Test data parsing
   - Test error conditions

5. **Update documentation**
   - Add usage instructions for the new script
   - Document required environment variables

## Critical Context for AI Agent

### Documentation
- iRacing API Documentation: https://github.com/jasondilworth56/iracingdataapi
- iRacing Data API Endpoints: https://members-ng.iracing.com/data/
- Discord.py 2.x Documentation: https://discordpy.readthedocs.io/en/stable/

### Code Examples
```python
# Example from existing codebase for API setup
import aiohttp
import asyncio

class IRacingAPIClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = None
        
    async def authenticate(self):
        # Implementation for authentication
        pass
        
    async def get_recent_races(self, customer_id):
        # Implementation for recent races endpoint
        pass
```

### Gotchas
- iRacing API requires 2FA disabled for script access (Legacy Read Only Authentication)
- Session cookies expire and need to be refreshed
- Rate limiting may occur during high-volume requests
- Some data fields might be missing in API responses

### Patterns to Follow
- Use async/await pattern consistently
- Follow existing codebase's error handling approach
- Implement proper logging instead of print statements
- Use environment variables for credentials
- Structure code with clear separation of concerns

## Quality Checklist
- [x] All necessary context included
- [x] Validation gates are executable by AI
- [x] References existing patterns
- [x] Clear implementation path
- [x] Error handling documented

## Confidence Score: 8/10

This PRP provides comprehensive context for implementing the iRacing last race printer script. It follows the established patterns in the codebase and includes all necessary information for one-pass implementation.