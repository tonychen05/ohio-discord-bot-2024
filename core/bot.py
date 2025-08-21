
import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.logger import setup_logging
import config

#Init Bot Settings
intents = discord.Intents.all()

setup_logging()
logger = logging.getLogger('bot')

class OHIOBot(commands.Bot):
    async def setup_hook(self):
        self.logger = logger
        # Load cogs
        await self.load_extension('cogs.verify')
        await self.load_extension('cogs.teams')

    async def on_ready(self):
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        self.logger.info('------')
        # try:
        #     synced = await self.tree.sync()
        #     self.logger.info(f'Synced {len(synced)} command(s)')
        # except Exception as e:
        #     self.logger.error(f'Error syncing commands: {e}')

bot = OHIOBot(command_prefix='!', intents=intents)

def start():
    # Load the bot token from an environment variable or a config file
    bot.run(config.discord_token, log_handler=None)

if __name__ == "__main__":
    start()

# ------------------------------------------------------------------


