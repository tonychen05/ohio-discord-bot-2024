import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

#when the bot is ready, this automatically runs
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

#greeting command as a test
@bot.command()
async def greet(ctxt, name: str):
    await ctxt.send(f'Hi {name}, how\'s your day going? ')

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(DISCORD_BOT_TOKEN)