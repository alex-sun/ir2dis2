# iRacing Discord Bot

A production-grade Discord bot that tracks iRacing race results for selected drivers and posts them automatically to designated Discord channels. The bot operates entirely within Docker, requires no host Python installation, and includes robust reliability features for extended operation.

## ✨ Features

- **Slash Commands**: `/lastrace`, `/setchannel`, `/trackmember`
- **Auto-Posting**: Periodically checks for new race results and posts them to configured channels
- **De-duplication**: Ensures each race result is posted only once per guild+member
- **Structured Logging**: JSON-formatted logs with configurable log levels
- **Graceful Shutdown**: Proper handling of SIGINT/SIGTERM signals
- **Circuit Breakers**: Prevents repeated API failures from crashing the bot
- **Docker-Only**: No host Python required - runs entirely in containers
- **Persistence**: SQLite database for tracking lists, configs, and last-published results

## 🚀 Quickstart

### Prerequisites

1. Docker and Docker Compose installed
2. iRacing account with API access (enable "Legacy Read Only Authentication" in settings)
3. Discord bot token (create at [Discord Developer Portal](https://discord.com/developers/applications))

### Environment Variables

Create a `.env` file in the project root with these variables:

```env
# Required: Discord bot token
DISCORD_TOKEN=your-discord-bot-token-here

# Required: iRacing credentials (for API access)
IRACING_USERNAME=your-iracing-username
IRACING_PASSWORD=your-iracing-password

# Optional: Configure these as needed
POLL_INTERVAL_SECONDS=60                # How often to check for new races (default: 60)
LOG_LEVEL=INFO                          # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
SQLITE_DB_PATH=/app/data/iresults.db    # Database path (default: /app/data/iresults.db)
```

### Docker Setup

1. **Build and start the bot**:
   ```bash
   docker compose up -d
   ```

2. **Stop the bot**:
   ```bash
   docker compose down
   ```

3. **View logs**:
   ```bash
   docker compose logs -f
   ```

## 📖 Usage

### Slash Commands

| Command                | Description                                                                 | Permissions       |
|-------------------------|-----------------------------------------------------------------------------|-------------------|
| `/lastrace customer_id`  | Get details about a user's most recent iRacing race                         | Everyone          |
| `/trackmember customer_id` | Add a member to the bot's tracking list for this server                    | Everyone          |
| `/setchannel #channel`   | Set the channel for auto-posted race results (admin only)                  | Administrator     |

### Examples

```bash
# Get last race for customer ID 123456
/lastrace customer_id:123456

# Track member with customer ID 789012
/trackmember customer_id:789012

# Set announcements to #iracing-results channel (admin only)
/setchannel channel:#iracing-results
```

## 🔧 Development

### Local Development

Create a `docker-compose.override.example` file for local testing:

```yaml
services:
  python:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./data:/app/data  # Persist database across restarts
```

### Testing

Run the test suite:
```bash
make tests
```

### Database

The bot uses SQLite for persistence. The database file is stored at `./data/iresults.db` by default and contains three tables:

- `guild_config`: Stores per-guild announcement channel settings
- `tracked_member`: Stores per-guild tracked iRacing member lists
- `last_published`: Stores the most recent subsession ID posted for each member

## 🛡️ Reliability Features

### Structured Logging

- JSON-formatted logs to stdout for easy parsing
- Configurable log levels via `LOG_LEVEL` environment variable
- Correlation IDs for tracking related events
- Detailed error information with stack traces when available

### Graceful Shutdown

- Proper handling of SIGINT/SIGTERM signals
- Clean termination of background tasks
- Graceful closure of database connections
- Timestamps for all shutdown events

### Circuit Breakers

- Prevents repeated API failures from causing cascading failures
- Automatic recovery after timeout periods
- Fallback behavior using cached data when possible
- Different timeout thresholds for different service types

### Exception Handling

- Comprehensive try/catch blocks around all external API calls
- Fallback behavior for critical failures
- No unhandled exceptions - all errors are logged and handled gracefully

## 🎯 Edge Cases Handled

- No tracked members in a guild
- No configured announcement channel
- API authentication failures
- Missing or invalid race data
- Discord permission errors
- Database connection issues
- Rate limiting from iRacing API
- Concurrent API call failures

## 🐋 Docker-Only Operation

This project is designed to run **exclusively within Docker**. All dependencies are installed inside the container, and no host Python installation is required. The Docker setup includes:

- Automatic dependency installation via `make install`
- Persistent SQLite database storage
- Environment variable configuration
- Logging to stdout (compatible with Docker logging drivers)

## 📝 Troubleshooting

### Common Issues

1. **Bot not responding to commands**:
   - Verify the bot has the correct permissions in your Discord server
   - Check that the bot is online and connected
   - Review logs for authentication or command registration errors

2. **No race results being posted**:
   - Ensure members are tracked using `/trackmember`
   - Verify an announcement channel is set using `/setchannel`
   - Check that the poll interval is configured correctly
   - Review logs for API or database errors

3. **API errors**:
   - Verify iRacing credentials are correct
   - Ensure "Legacy Read Only Authentication" is enabled in iRacing settings
   - Check for circuit breaker state in logs
   - Review iRacing API status at [iRacing Status](https://status.iracing.com/)

### Log Analysis

All logs are output in JSON format to stdout, making them easy to parse with tools like:

- `docker compose logs -f | jq '.level == "ERROR"'`
- `docker compose logs -f | grep "ERROR"`
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk or other SIEM tools

## 📁 Project Structure

```
├── src/                          # Source code
│   ├── discord_bot.py           # Main bot implementation
│   ├── iracing_api.py           # iRacing API wrapper with circuit breakers
│   ├── logging_config.py        # Structured logging configuration
│   ├── circuit_breaker.py       # Circuit breaker implementation
│   └── database/                # Database models and utilities
│       ├── models.py            # SQLAlchemy models
│       ├── crud.py              # Database operations
│       └── utils.py             # Database utility functions
├── tests/                       # Test suite
├── docker-compose.yml           # Docker Compose configuration
├── Dockerfile                   # Docker image definition
├── Makefile                     # Build and test scripts
├── requirements.txt             # Python dependencies
└── README.md                    # This documentation
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'feat: add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

Please ensure all tests pass before submitting a pull request.