import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.logger import setup_logging
import config
import traceback

#Init Bot Settings
intents = discord.Intents.all()

setup_logging()
logger = logging.getLogger('bot')

class OHIOBot(commands.Bot):
    async def setup_hook(self):
        self.logger = logger
        self.tree.on_error = self.on_app_command_error

        # Load cogs
        await self.load_extension('cogs.verify')
        await self.load_extension('cogs.teams')
        await self.load_extension('cogs.fun')
        await self.load_extension('cogs.admin')

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                content=(
                    "You do not have permission to run this command.\n"
                    "If you think this is a mistake, please contact server admins."
                ), 
                ephemeral=True)
        else:
            await interaction.response.send_message(
                content="An error occurred. Please try again later or contact server admins.",
                ephemeral=True)
            self.logger.error(error)
            traceback.print_exc()
            
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


