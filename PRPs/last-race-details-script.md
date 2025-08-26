# PRP: Last Race Details Script

## Feature Description
Create a simple Python script that uses the [iracingdataapi library](https://github.com/jasondilworth56/iracingdataapi) to authenticate with iRacing and print detailed information about the user's most recent race participation.

## Critical Context

### Library Documentation & References
- **GitHub Repository**: [jasondilworth56/iracingdataapi](https://github.com/jasondilworth56/iracingdataapi)
- **Client.py Analysis**: Key race-related methods identified:
  - `member_recent_races(self, cust_id: Optional[int] = None) -> Dict`: Gets latest member races
  - `result(self, subsession_id: int, include_licenses: bool = False) -> Dict`: Gets detailed results for a specific session
  - `result_lap_data(self, subsession_id: int, simsession_number: int = 0, cust_id: Optional[int] = None, team_id: Optional[int] = None) -> list[Optional[Dict]]`: Gets lap data
  - `result_event_log(self, subsession_id: int, simsession_number: int = 0) -> list[Dict]`: Gets event logs

### Codebase Patterns
- The library uses OAuth2 authentication flow
- All API calls return JSON data that needs parsing
- Rate limiting is handled automatically in the client
- Error handling for network issues and API errors is built into the client

### Gotchas & Quirks
- Requires valid iRacing credentials (username/password)
- API has 90-day data limitation for result searches
- `member_recent_races()` returns data in reverse chronological order (most recent first)
- Subsessions have different types: -2 (practice), -1 (qualify), 0 (race)

## Implementation Blueprint

### Pseudocode Approach
```python
# 1. Import the library
from iracingdataapi import irDataClient

# 2. Get user credentials (should be secure - not hardcoded)
username = input("Enter iRacing username: ")
password = input("Enter iRacing password: ")

# 3. Create client instance
client = irDataClient(username=username, password=password)

try:
    # 4. Get recent races for authenticated user
    recent_races = client.member_recent_races()
    
    if not recent_races.get('races'):
        print("No recent races found")
        exit()
    
    # 5. Get the most recent race (first in list)
    last_race = recent_races['races'][0]
    subsession_id = last_race['subsession_id']
    
    # 6. Get detailed results for the last race
    race_details = client.result(subsession_id=subsession_id, include_licenses=True)
    
    # 7. Get lap data for the user in this race
    lap_data = client.result_lap_data(
        subsession_id=subsession_id, 
        simsession_number=0,  # 0 = race
        cust_id=client.username  # Use authenticated user's ID
    )
    
    # 8. Print formatted results
    print("=== Last Race Details ===")
    print(f"Race Date: {race_details['session_info']['start_time']}")
    print(f"Track: {race_details['session_info']['track']['name']}")
    print(f"Car: {race_details['session_info']['car']['name']}")
    print(f"Session Type: {race_details['session_info']['event_type']}")
    print(f"Your Position: {race_details['results']['your_position']}")
    print(f"Number of Laps: {len(lap_data)}")
    
    # 9. Print top 5 finishers
    print("\n=== Top 5 Finishers ===")
    for i, driver in enumerate(race_details['results']['drivers'][:5]):
        print(f"{i+1}. {driver['name']} - {driver['position']}")

except Exception as e:
    print(f"Error: {str(e)}")
    exit(1)
```

### Step-by-Step Implementation Tasks
1. **[Task 1]** Create script file structure
   - File: `src/last_race_details.py`
   - Shebang: `#!/usr/bin/env python3`
   - Import necessary modules

2. **[Task 2]** Implement authentication flow
   - Get credentials from user input (securely)
   - Create irDataClient instance
   - Handle authentication errors

3. **[Task 3]** Fetch recent races
   - Call `member_recent_races()` method
   - Validate response format
   - Handle "no races found" case

4. **[Task 4]** Get detailed race information
   - Extract subsession_id from most recent race
   - Call `result()` method with include_licenses=True
   - Parse session_info and results structure

5. **[Task 5]** Fetch and display lap data
   - Call `result_lap_data()` for the authenticated user
   - Calculate and display key lap statistics

6. **[Task 6]** Implement user-friendly output
   - Format timestamps for readability
   - Display track/car/session information
   - Show top finishers and user position
   - Include lap count and key metrics

### Error Handling Strategy
- **Authentication Errors**: Catch login failures and display user-friendly messages
- **API Errors**: Handle non-200 responses and rate limiting (built into client)
- **Data Parsing Errors**: Validate JSON structure before accessing nested fields
- **Network Errors**: Catch connection timeouts and retry logic
- **Empty Results**: Handle cases where no races are found gracefully

## Validation Gates

### Syntax & Style Validation
```bash
# Check for syntax errors and style issues
ruff check last_race_details.py --fix
mypy last_race_details.py --strict
```

### Unit Tests
```bash
# Create test file: tests/test_last_race.py
uv run pytest tests/test_last_race.py -v
```

**Test Cases to Implement:**
1. Test authentication failure handling
2. Test "no recent races" scenario
3. Test data parsing for different race types
4. Test edge cases (empty lap data, etc.)

### Integration Test
```bash
# Requires actual iRacing credentials (for development only)
python last_race_details.py --test-mode
```

## Quality Checklist
- [ ] All necessary context included about iracingdataapi
- [ ] Implementation blueprint with clear task breakdown
- [ ] Error handling strategy documented
- [ ] Validation gates are executable
- [ ] References existing library patterns
- [ ] Clear implementation path provided

## Confidence Score
9/10 - High confidence due to comprehensive library analysis and clear implementation path. The main uncertainty is around the exact data structure returned by `member_recent_races()` which would require testing with actual credentials.