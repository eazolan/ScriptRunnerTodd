import discord
from discord.ext import commands
import subprocess
import json
from datetime import datetime
import sys
import os
import yaml
import asyncio
import time
from discord.ext.commands import is_owner
import logging

logging.getLogger('discord').setLevel(logging.WARNING)  # Reduce Discord.py logging verbosity


async def run_script(cmd, cwd=None):
    """Run a script asynchronously using asyncio with real-time output processing"""
    try:
        print(f"Running command: {cmd}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env={
                **os.environ,
                'PYTHONUNBUFFERED': '1'  # Disable Python output buffering
            }
        )

        # Initialize output collectors
        stdout_data = []
        stderr_data = []

        # Read output stream while process is running
        async def read_stream(stream, collector):
            while True:
                line = await stream.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                collector.append(line_str)
                print(f"Output: {line_str}")  # Print for debugging

        # Create tasks for reading both streams
        stdout_task = asyncio.create_task(read_stream(process.stdout, stdout_data))
        stderr_task = asyncio.create_task(read_stream(process.stderr, stderr_data))

        # Wait for the process to complete and streams to be fully read
        await asyncio.gather(stdout_task, stderr_task)
        await process.wait()

        # Join the collected output
        stdout_output = '\n'.join(stdout_data)
        stderr_output = '\n'.join(stderr_data)

        return process.returncode, stdout_output, stderr_output
    except Exception as e:
        print(f"Error in run_script: {e}")
        return 1, "", str(e)


def load_config():
    """Load configuration from config.yml"""
    with open('config.yml', 'r') as file:
        return yaml.safe_load(file)


# Load configuration
config = load_config()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # Needed to read message content
intents.members = True  # Needed for member-related features


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config['discord']['command_prefix'],
            intents=intents
        )
        self._restart_flag = False
    
    async def setup_hook(self):
        print(f"Bot setup completed!")
        for command in self.commands:
            print(f'Registered command: {self.command_prefix}{command.name}')
    
    async def close(self):
        """Cleanly close the bot connection"""
        if self._restart_flag:
            print("Restarting bot...")
        else:
            print("Shutting down bot...")
        await super().close()

# Initialize bot
bot = MyBot()

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


# Remove default help command and add our custom one
bot.remove_command('help')


@bot.command(name='srt_help')
async def help_command(ctx, command_name=None):
    """Shows the list of available commands and their usage.

    Use !srt_help [command] to get detailed help for a specific command.
    Example: !srt_help srt_analyze
    """
    if command_name:
        # Get specific command help
        command = bot.get_command(command_name)
        if command:
            embed = discord.Embed(
                title=f"Command: {config['discord']['command_prefix']}{command.name}",
                description=command.help or "No description available",
                color=discord.Color.blue()
            )
        else:
            await ctx.send(f"❌ Command '{command_name}' not found.")
            return
    else:
        # Show all commands
        embed = discord.Embed(
            title="Script Runner Todd - Options Trading Bot",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )

        for command in bot.commands:
            embed.add_field(
                name=f"{config['discord']['command_prefix']}{command.name}",
                value=command.help.split('\n')[0] if command.help else "No description available",
                inline=False
            )

    await ctx.send(embed=embed)

@bot.command(name='srt_restart')
@commands.is_owner()
async def restart_bot(ctx):
    """Restarts the bot.
    
    This command can only be used by the bot owner.
    It will safely shut down the bot and start it again.
    """
    try:
        # Set restart flag
        bot._restart_flag = True
        
        # Start new process
        script_path = os.path.abspath(__file__)
        python_executable = sys.executable
        subprocess.Popen([python_executable, script_path])
        
        # Send a single message and close bot
        await ctx.send("🔄 Restarting bot... I'll be back in a moment!")
        
        # Brief pause to ensure message is sent
        await asyncio.sleep(1)
        await bot.close()
        
        # Exit without triggering traceback
        os._exit(0)
        
    except Exception as e:
        bot._restart_flag = False
        await ctx.send(f"❌ Error during restart: {str(e)}")
        print(f"Restart error: {str(e)}")
        return


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Connected to {len(bot.guilds)} guilds:')
    for guild in bot.guilds:
        print(f' - {guild.name} (id: {guild.id})')
        # If allowed_channels is configured, send startup message to those channels
        if 'allowed_channels' in config['discord']:
            for channel_id in config['discord']['allowed_channels']:
                channel = guild.get_channel(channel_id)
                if channel:
                    await channel.send("🟢 ScriptRunnerTodd is now online and ready!")
    print(f'Available commands: {[command.name for command in bot.commands]}')


@bot.event
async def on_message(message):
    print(f'Message received: {message.content}')
    if message.author == bot.user:
        return
    print(f'Processing command: {message.content}')
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    print(f'Error processing command: {error}')
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!srt_help` to see available commands.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")


@bot.command(name='srt_collect')
async def collect_data(ctx):
    """Collects fresh options data from the market.

    This command runs the data collection script to fetch the latest
    options trading data. It must be run before analysis can be performed.
    """
    print("Starting collection...")
    
    # Check if channel is allowed (if configured)
    if 'allowed_channels' in config['discord'] and \
            ctx.channel.id not in config['discord']['allowed_channels']:
        return

    status_message = await ctx.send("Starting data collection...")
    progress_message = None

    try:
        # Get the executable path
        exe_path = config['scripts']['virtual_env'].replace('python.exe', 'collect-data.exe')
        print(f"Using executable: {exe_path}")
        
        # Run the collection command
        returncode, stdout, stderr = await run_script(
            [exe_path],
            cwd=config['scripts']['base_path']
        )

        # Update state
        state = load_state()
        state['last_run'] = datetime.now().isoformat()
        save_state(state)

        if returncode == 0:
            await status_message.edit(content="✅ Data collection completed!")
            
            # Extract important information
            output_lines = stdout.split('\n')
            for line in output_lines:
                if "Found" in line and "stocks with volume > 1M and > 5$" in line:
                    await ctx.send(f"📊 {line.strip()}")
                elif "Processing batch" in line:
                    continue  # Skip batch processing messages
                elif "Completed processing options" in line:
                    await ctx.send(f"✨ {line.strip()}")
                elif "Final row count in database" in line:
                    await ctx.send(f"📈 {line.strip()}")

        else:
            error_msg = stderr or "No error message available"
            await status_message.edit(content=f"❌ Error in data collection:\n```{error_msg[:1900]}```")

    except Exception as e:
        await status_message.edit(content=f"❌ Error: {str(e)}")
        print(f"Error details: {str(e)}")


@bot.command(name='srt_analyze')
async def analyze_options(ctx, *args):
    """Analyzes collected options data with specified filters.

    Usage: 
    For put options:
        !srt_analyze puts -f <funds> -r <results>
        Example: !srt_analyze puts -f 10000 -r 20

    For call options:
        !srt_analyze calls <symbol>
        Example: !srt_analyze calls AAPL

    Arguments:
    puts mode:
        -f, --funds: Available funds for trading
        -r, --results: Number of top results to show (optional, default: 10)
        --include-nonstandard: Include non-standard options (optional)

    calls mode:
        symbol: Stock symbol to analyze for covered calls
        --include-nonstandard: Include non-standard options (optional)

    The analysis will use the most recently collected data.
    Run !srt_collect first if you need fresh data.
    """
    if 'allowed_channels' in config['discord'] and \
            ctx.channel.id not in config['discord']['allowed_channels']:
        return

    state = load_state()
    if not state.get('last_run'):
        await ctx.send("⚠️ No data collected yet. Please run !srt_collect first.")
        return

    if not args:
        await ctx.send("⚠️ Please specify 'puts' or 'calls' and required arguments. Use !srt_help srt_analyze for more information.")
        return

    await ctx.send("Starting analysis...")

    try:
        # Get the executable path
        exe_path = config['scripts']['virtual_env'].replace('python.exe', 'analyze-options.exe')
        cmd = [exe_path] + list(args)
        print(f"Using command: {cmd}")
        
        # Run the analysis command
        returncode, stdout, stderr = await run_script(
            cmd,
            cwd=config['scripts']['base_path']
        )

        if returncode == 0:
            # Split output into chunks if it's too long for Discord
            output = stdout or "No output generated"
            chunks = [output[i:i+1900] for i in range(0, len(output), 1900)]
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")
        else:
            error_msg = stderr or "No error message available"
            await ctx.send(f"❌ Error in analysis:\n```{error_msg[:1900]}```")

    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")
        print(f"Error details: {str(e)}")


@bot.command(name='srt_status')
async def check_status(ctx):
    """Shows when data was last collected.

    This command displays the timestamp of the most recent
    data collection and how long ago it was performed.
    """
    print("Status command started")
    print(f"Command received in channel: {ctx.channel.name} (ID: {ctx.channel.id})")

    # Check if channel is allowed (if configured)
    if 'allowed_channels' in config['discord']:
        allowed_channels = config['discord']['allowed_channels']
        print(f"Allowed channels configured: {allowed_channels}")
        if ctx.channel.id not in allowed_channels:
            print(f"Channel {ctx.channel.id} not in allowed list")
            await ctx.send("❌ This command can only be used in designated channels.")
            return

    print("Channel check passed or no channel restrictions")

    try:
        print(f"Looking for state file: {STATE_FILE}")
        if not os.path.exists(STATE_FILE):
            print("State file does not exist")
            await ctx.send("No data has been collected yet. Use !srt_collect to fetch new data.")
            return

        state = load_state()
        print(f"Loaded state: {state}")
        last_run = state.get('last_run')
        print(f"Last run: {last_run}")

        if last_run:
            last_run_dt = datetime.fromisoformat(last_run)
            time_diff = datetime.now() - last_run_dt
            await ctx.send(f"Last data collection: {last_run_dt.strftime('%Y-%m-%d %H:%M:%S')} "
                          f"({time_diff.seconds // 3600} hours {(time_diff.seconds // 60) % 60} minutes ago)")
        else:
            await ctx.send("No data has been collected yet. Use !srt_collect to fetch new data.")
    except Exception as e:
        print(f"Error in status command: {str(e)}")
        await ctx.send(f"❌ Error checking status: {str(e)}")


# Modify your main block to include error handling
if __name__ == "__main__":
    try:
        bot.run(config['discord']['token'])
    except KeyboardInterrupt:
        print("\nBot shutdown via keyboard interrupt")
    except Exception as e:
        print(f"Error running bot: {str(e)}")
