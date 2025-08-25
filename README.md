# iRacing Last Race Printer

A Python script that uses the jasondilworth56/iracingdataapi library to fetch and print details of the last race for a given iRacing member.

## Features

- Fetches recent races for a specified iRacing customer ID
- Retrieves detailed results for the most recent race
- Displays formatted race information including:
  - Series name and track
  - Field size
  - Race results with driver positions
  - iRating changes and points earned
  - Timestamp of the race

## Requirements

- Python 3.8+
- aiohttp library
- iRacing credentials (with 2FA disabled for script access)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install aiohttp
   ```

## Usage

Set environment variables with your iRacing credentials and customer ID:

```bash
export IRACING_EMAIL="your_email@example.com"
export IRACING_PASSWORD="your_password"
export IRACING_CUSTOMER_ID=123456
```

Then run the script:

```bash
python src/last_race_printer.py
```

## API Endpoints Used

- `https://members-ng.iracing.com/data/stats/member_recent_races?cust_id={customer_id}` - Get recent races
- `https://members-ng.iracing.com/data/results/get?subsession_id={subsession_id}` - Get detailed results

## Configuration

The script expects the following environment variables:
- `IRACING_EMAIL` - Your iRacing email address
- `IRACING_PASSWORD` - Your iRacing password  
- `IRACING_CUSTOMER_ID` - The customer ID of the iRacing member

## Important Notes

1. **2FA Requirement**: iRacing API requires 2FA to be disabled for script access (Legacy Read Only Authentication)
2. **Session Management**: Session cookies may expire and need to be refreshed
3. **Rate Limiting**: Be mindful of rate limiting during high-volume requests
4. **Data Fields**: Some data fields might be missing in API responses

## Testing

Run the unit tests with:

```bash
python -m pytest tests/ -v
```

## Validation

The implementation follows these validation gates from the PRP:

```bash
# Syntax/Style
ruff check --fix && mypy .

# Unit Tests  
uv run pytest tests/ -v
```

## Error Handling

The script includes comprehensive error handling for:
- Authentication failures
- Network errors
- Missing data fields
- Session management issues

## License

This project is licensed under the MIT License.