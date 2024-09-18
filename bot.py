import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import sqlite3

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

conn = sqlite3.connect('db.sqlite')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')
conn.commit()

#when the bot is ready, this automatically runs
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

#greeting command as a test
@bot.command()
async def greet(ctxt, name: str):
    await ctxt.send(f'Hi {name}, how\'s your day going? ')

#adding an email to database
@bot.command()
async def register(ctxt, email: str):
    cursor.execute('INSERT INTO users (name) VALUES (?)', (email,))
    conn.commit()
    await ctxt.send(f'Email: {email} was successfully added')

#print all
@bot.command()
async def showAll(ctxt):
    cursor.execute('SELECT name FROM users')
    users = cursor.fetchall()
    list = "\n".join([user[0] for user in users])
    await ctxt.send(f'People:\n{list}')

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(DISCORD_BOT_TOKEN)