# ScriptRunnerTodd

A Discord bot for automating options trading analysis scripts. This bot allows you to remotely trigger data collection and analysis through Discord commands.

## Related Projects

This bot is designed to work with [SchwabV2](https://github.com/eazolan/SchwabV2), a collection of scripts for options trading analysis. ScriptRunnerTodd provides a Discord interface to trigger and manage these analysis scripts remotely.

To use this bot effectively:
1. First install and configure [SchwabV2](https://github.com/eazolan/SchwabV2)
2. Then set up this bot following the instructions below

## Features

- Run data collection scripts remotely via Discord
- Execute options analysis with custom parameters
- Track when data was last collected
- Receive analysis results directly in Discord

## Setup

### Prerequisites
- Python 3.8-3.11 (3.11 recommended)
- Git

1. Clone this repository
2. Create a virtual environment and install dependencies:
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows
# or source .venv/bin/activate  # On Linux/Mac

# Make sure pip is up to date
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

3. Create a Discord bot:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Add a bot to the application
   - Under "Bot" settings:
     - Enable "Message Content Intent" under Privileged Gateway Intents
     - Enable "Server Members Intent" if you need member-related features
   - Copy the bot token

4. Configure the bot:
   - Copy `config.yml.example` to `config.yml`
   - Add your Discord bot token to `config.yml`
   - Configure any other settings as needed

5. Invite the bot to your server using the OAuth2 URL generator in the Developer Portal
   - Select 'bot' scope
   - Select required permissions (Send Messages, Read Messages/View Channels)

## Usage

Start the bot:
```bash
python SRT_main.py
```

### Available Commands

- `!srt_collect` - Collect fresh options data from the market
- `!srt_analyze [puts/calls]` - Analyze collected data with optional filters
- `!srt_status` - Check when data was last collected
- `!srt_help` - Show available commands and usage information
- `!srt_restart` - Owner-only command to restart the bot (useful for maintenance or recovery)


Example:
```
!srt_analyze puts -f 19000 -r 20
!srt_analyze calls aapl
```

## Security Notes

- Keep your `config.yml` file private and never commit it to version control
- If your bot token is ever exposed, immediately reset it in the Discord Developer Portal

## Contributing

Feel free to open issues or submit pull requests with improvements.

## License

[Add your chosen license here]