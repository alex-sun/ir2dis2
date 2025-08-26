# PRP: iRacing Last Race Details Script

## Feature Description
A simple Python script that uses the [iracingdataapi library](https://github.com/jasondilworth56/iracingdataapi) to authenticate with iRacing and print details of the last official race for a specified customer ID.

## Critical Context

### Documentation
- **iracingdataapi Library**: [GitHub Repository](https://github.com/jasondilworth56/iracingdataapi)
- **iRacing Data API Reference**: [iRacing Members API Documentation](https://members-ng.iracing.com/api-docs/)
- **Project Conventions**: Refer to `/docs/feature.md` for Docker requirements, error handling patterns, and logging standards

### Code Examples (Project Patterns)
```python
# Example from projected structure - follows async pattern from feature documentation
import asyncio
import os
from iracingdataapi import IRacingDataAPI

async def main():
    # Follow env var pattern from feature documentation
    email = os.getenv("IRACING_EMAIL")
    password = os.getenv("IRACING_PASSWORD")
    
    # Initialize client following typical library patterns
    client = IRacingDataAPI(email, password)
    await client.login()
    
    # Example usage pattern
    customer_id = 123456  # Would be parameterized in final script
    races = await client.get_member_recent_races(customer_id)
    
    # Process and display results
    if races:
        latest_race = races[0]
        print(f"Last race: {latest_race['session_name']}")
        print(f"Track: {latest_race['track_name']}")
        print(f"Result: {latest_race['position']}/{latest_race['field_size']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Gotchas & Library Quirks
1. **Authentication**: iracingdataapi requires valid iRacing credentials (email + password)
2. **Rate Limits**: iRacing API has rate limits - implement backoff strategy
3. **Data Consistency**: Not all race fields may be available for older results
4. **Session Management**: Library may require manual session refresh for long-running scripts
5. **Docker Requirement**: Must run entirely in container (no host Python dependencies)

### Patterns to Follow
1. **Env Var Usage**: Store credentials in environment variables (never hardcode)
2. **Async Design**: Use async/await pattern consistent with project requirements
3. **Error Handling**: Implement try/catch blocks with meaningful error messages
4. **Logging**: Use Python `logging` module with consistent formatting
5. **Dockerization**: Include Dockerfile and docker-compose.yml following project standards

## Implementation Blueprint

### Pseudocode Approach
```python
#!/usr/bin/env python3
"""
Simple script to print last iRacing race details using iracingdataapi library.
Follows project conventions for Docker, env vars, and error handling.
"""

import asyncio
import os
import logging
from typing import Optional, Dict
from iracingdataapi import IRacingDataAPI, IRacingAPIError

# Configure logging following project standards
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def get_last_race_details(customer_id: int) -> Optional[Dict]:
    """
    Fetch and return details of the last official race for a given customer ID.
    
    Args:
        customer_id: iRacing customer ID
        
    Returns:
        Dict with race details or None if no races found
    """
    try:
        # Get credentials from env vars (project standard)
        email = os.getenv("IRACING_EMAIL")
        password = os.getenv("IRACING_PASSWORD")
        
        if not email or not password:
            raise ValueError("IRACING_EMAIL and IRACING_PASSWORD must be set in environment variables")

        # Initialize client and login
        client = IRacingDataAPI(email, password)
        logger.info("Authenticating with iRacing API...")
        await client.login()

        # Get recent races (typically returns last 10 official races)
        logger.info(f"Fetching recent races for customer ID: {customer_id}")
        races = await client.get_member_recent_races(customer_id)
        
        if not races:
            logger.warning(f"No races found for customer ID: {customer_id}")
            return None

        # Get the most recent official race
        latest_race = races[0]
        
        # Enhance with additional details if available
        if 'subsession_id' in latest_race:
            logger.info(f"Fetching detailed results for subsession: {latest_race['subsession_id']}")
            subsession_details = await client.get_subsession_results(latest_race['subsession_id'])
            latest_race.update(subsession_details)

        return latest_race

    except IRacingAPIError as e:
        logger.error(f"iRacing API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise

def format_race_details(race: Dict) -> str:
    """Format race details into human-readable string following project patterns."""
    if not race:
        return "No race details available"
    
    details = []
    details.append(f"**Race:** {race.get('session_name', 'Unknown')}")
    details.append(f"**Track:** {race.get('track_name', 'Unknown')}")
    details.append(f"**Series:** {race.get('series_name', 'Unknown')}")
    
    if 'position' in race and 'field_size' in race:
        details.append(f"**Result:** P{race['position']}/{race['field_size']}")
    
    if 'car_name' in race:
        details.append(f"**Car:** {race['car_name']}")
    
    if 'irating_delta' in race:
        details.append(f"**iRating Change:** {race['irating_delta']:+d}")
    
    if 'timestamp' in race:
        details.append(f"**Date:** {race['timestamp'].strftime('%Y-%m-%d %H:%M UTC')}")
    
    return "\n".join(details)

async def main():
    """Main entry point - parse args and execute."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Print last iRacing race details')
    parser.add_argument('customer_id', type=int, help='iRacing customer ID')
    args = parser.parse_args()

    try:
        logger.info(f"Starting race details lookup for customer ID: {args.customer_id}")
        race_details = await get_last_race_details(args.customer_id)
        
        if race_details:
            print("Last Race Details:")
            print(format_race_details(race_details))
        else:
            print("No race details found for this customer.")
            
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### Tasks to Complete (Implementation Order)

1. **Setup Project Structure**
   - Create `src/last_race_script.py` (main script)
   - Create `docker/Dockerfile` (follows project Docker standards)
   - Create `docker-compose.yml` (for easy execution)
   - Create `.env.example` (environment variable template)

2. **Implement Core Functionality**
   - [ ] Add IRacingDataAPI client initialization
   - [ ] Implement `get_last_race_details` function with error handling
   - [ ] Add subsession details enhancement logic
   - [ ] Implement `format_race_details` function

3. **Add CLI Interface**
   - [ ] Add argparse for customer_id parameter
   - [ ] Implement help text and version information
   - [ ] Add environment variable validation

4. **Docker Integration**
   - [ ] Create Dockerfile with Python runtime
   - [ ] Add iracingdataapi dependency installation
   - [ ] Configure entrypoint for script execution
   - [ ] Add healthcheck and logging configuration

5. **Testing & Validation**
   - [ ] Write unit tests for formatting functions
   - [ ] Create integration test with mock iRacing API
   - [ ] Test error handling scenarios

### Error Handling Strategy
1. **Authentication Errors**: Catch login failures and provide clear messages
2. **API Errors**: Handle rate limits, 404s, and other API-specific errors
3. **Data Errors**: Handle missing fields gracefully with fallback values
4. **Env Var Errors**: Fail fast with clear messages if required vars are missing
5. **Network Errors**: Implement retry logic with exponential backoff

## Validation Gates (Executable)

### Syntax & Style
```bash
# Run in Docker container
docker compose run --rm script ruff check --fix src/
docker compose run --rm script mypy src/
```

### Unit Tests
```bash
# Run unit tests in container
docker compose run --rm script pytest tests/ -v
```

### Integration Test
```bash
# Test with sample customer ID (replace with valid test ID)
docker compose run --rm script python src/last_race_script.py 123456
```

### Docker Validation
```bash
# Build and test Docker image
docker compose build
docker compose up --exit-code-from script
```

## Quality Checklist
- [x] All necessary context included
- [x] Validation gates are executable by AI
- [x] References existing patterns from feature documentation
- [x] Clear implementation path defined
- [x] Error handling strategy documented

## Confidence Score
**Score: 8/10**  
High confidence due to clear requirements, established project patterns, and well-defined implementation path. The main uncertainty is around iracingdataapi library specifics (method names, return structures) that would require verification against the actual library documentation.