import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()


import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(DISCORD_BOT_TOKEN)

async def on_ready():
    print(f'Logged in as {bot.user}')

botToken = os.getenv("botToken")
bot.run(botToken)
