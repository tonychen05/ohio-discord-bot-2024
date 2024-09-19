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
cursor.execute('''
CREATE TABLE IF NOT EXISTS teams (
    teamName TEXT PRIMARY KEY NOT NULL,
    email1 TEXT NOT NULL,
    email2 TEXT NOT NULL,
    email3 TEXT NOT NULL,
    email4 TEXT NOT NULL
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

#team formation
#inputs: 4 emails
#result: add a row where emails are added
@bot.command()
async def addTeam(ctxt, *, args: str):
    try:
        #Split arguments by space into a list of strings
        split_args = args.split()

        #ensure there are at least 5 elements in the list (1 team name + 4 emails)
        if len(split_args) < 5:
            await ctxt.send("You need to provide the team name followed by 4 email addresses.")
            return

        #get the last 4 elements as emails
        email1 = split_args[-4]
        email2 = split_args[-3]
        email3 = split_args[-2]
        email4 = split_args[-1]

        #join everything before the last 4 emails as the team name
        teamName = " ".join(split_args[:-4])

        # Insert these 5 variables into the sql database
        cursor.execute('INSERT INTO teams VALUES (?,?,?,?,?)', (teamName, email1, email2, email3, email4))
        conn.commit()

        #send success message
        await ctxt.send(f'{teamName} was successfully registered! Happy hacking!')

    except Exception as e:
        #Catch any unexpected errors and log them
        await ctxt.send(f"An error occurred: {e}")


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(DISCORD_BOT_TOKEN)