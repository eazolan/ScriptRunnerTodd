# ScriptRunnerTodd

A Discord bot for automating options trading analysis scripts. This bot allows you to remotely trigger data collection and analysis through Discord commands.

## Features

- Run data collection scripts remotely via Discord
- Execute options analysis with custom parameters
- Track when data was last collected
- Receive analysis results directly in Discord

## Setup

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

- `!collect` - Collect fresh options data from the market
- `!analyze [filters]` - Analyze collected data with optional filters
- `!status` - Check when data was last collected
- `!help` - Show available commands and usage information

Example:
```
!analyze --min-volume 100 --max-strike 50
```

## Security Notes

- Keep your `config.yml` file private and never commit it to version control
- If your bot token is ever exposed, immediately reset it in the Discord Developer Portal

## Contributing

Feel free to open issues or submit pull requests with improvements.

## License

[Add your chosen license here]