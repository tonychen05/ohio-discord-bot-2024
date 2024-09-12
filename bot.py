import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def on_ready():
    print(f'Logged in as {bot.user}')

botToken = os.getenv("botToken")
bot.run(botToken)