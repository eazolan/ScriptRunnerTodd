import discord
from discord.ext import commands
import subprocess
import json
from datetime import datetime
import os
import yaml

def load_config():
    """Load configuration from config.yml"""
    with open('config.yml', 'r') as file:
        return yaml.safe_load(file)

# Load configuration
config = load_config()

# Bot configuration
bot = commands.Bot(
    command_prefix=config['discord']['command_prefix'],
    intents=discord.Intents.all()
)

# State tracking
STATE_FILE = config['state']['file_path']

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'last_run': None}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Options Trading Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )
        
        for command in self.context.bot.commands:
            # Skip the help command itself
            if command.name == "help":
                continue
            embed.add_field(
                name=f"{config['discord']['command_prefix']}{command.name}",
                value=command.help or "No description available",
                inline=False
            )
            
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=f"Command: {config['discord']['command_prefix']}{command.name}",
            description=command.help or "No description available",
            color=discord.Color.blue()
        )
        await self.get_destination().send(embed=embed)

# Set up the custom help command
bot.help_command = CustomHelpCommand()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='collect')
async def collect_data(ctx):
    """Collects fresh options data from the market.
    
    This command runs the data collection script to fetch the latest
    options trading data. It must be run before analysis can be performed.
    """
    # Check if channel is allowed (if configured)
    if 'allowed_channels' in config['discord'] and \
       ctx.channel.id not in config['discord']['allowed_channels']:
        return

    await ctx.send("Starting data collection...")
    
    try:
        # Run your data collection script
        result = subprocess.run(
            ['python', config['scripts']['data_collection']['path']], 
            capture_output=True, 
            text=True
        )
        
        # Update state
        state = load_state()
        state['last_run'] = datetime.now().isoformat()
        save_state(state)
        
        if result.returncode == 0:
            await ctx.send("✅ Data collection completed successfully!")
        else:
            await ctx.send(f"❌ Error in data collection:\n```{result.stderr}```")
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='analyze')
async def analyze_options(ctx, *args):
    """Analyzes collected options data with specified filters.
    
    Usage: !analyze [filters]
    Example: !analyze --min-volume 100 --max-strike 50
    
    The analysis will use the most recently collected data.
    Run !collect first if you need fresh data.
    """
    # Check if channel is allowed (if configured)
    if 'allowed_channels' in config['discord'] and \
       ctx.channel.id not in config['discord']['allowed_channels']:
        return

    state = load_state()
    if not state.get('last_run'):
        await ctx.send("⚠️ No data collected yet. Please run !collect first.")
        return
        
    await ctx.send("Starting analysis...")
    
    try:
        # Construct command with arguments
        cmd = ['python', config['scripts']['analysis']['path']] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Format the output nicely for Discord
            output = f"Analysis Results:\n```{result.stdout}```"
            await ctx.send(output)
        else:
            await ctx.send(f"❌ Error in analysis:\n```{result.stderr}```")
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='status')
async def check_status(ctx):
    """Shows when data was last collected.
    
    This command displays the timestamp of the most recent
    data collection and how long ago it was performed.
    """
    # Check if channel is allowed (if configured)
    if 'allowed_channels' in config['discord'] and \
       ctx.channel.id not in config['discord']['allowed_channels']:
        return

    state = load_state()
    last_run = state.get('last_run')
    
    if last_run:
        last_run_dt = datetime.fromisoformat(last_run)
        time_diff = datetime.now() - last_run_dt
        await ctx.send(f"Last data collection: {last_run_dt.strftime('%Y-%m-%d %H:%M:%S')} "
                      f"({time_diff.seconds // 3600} hours {(time_diff.seconds // 60) % 60} minutes ago)")
    else:
        await ctx.send("No data has been collected yet.")

if __name__ == "__main__":
    # Run the bot with token from config
    bot.run(config['discord']['token'])
