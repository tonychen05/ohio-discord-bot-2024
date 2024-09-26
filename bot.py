import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import sqlite3

#Load in Bot Key
load_dotenv()

#Init Bot Settings
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
   
#---------------------Constants----------------------

MAX_TEAM_SIZE = 4
TEAM_FORMATION_TIMEOUT = 60
TEAM_DATABASE = 'db.sqlite'
USER_DATABASE = None

# --------------------Helper Methods-------------------
def connect_to_team_db(filename):
    #Check if database exists
    conn = sqlite3.connect(filename)
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

    return cursor

def connect_to_user_db(filename){
    #Check if database exists
    conn = sqlite3.connect(filename)
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

    return cursor
}

# ---------------------Classes-------------------------

#Retrieves Member username (Can be used for adding members)
class userFlag(commands.FlagConverter):
    member: discord.Member = commands.flag(description='The member to ban')

#Retrieves Email
class emailFlag(commands.FlagConverter):
    email: str = commands.flag(description = 'Email Address used to Register')

#Retrieves Team Name
class teamNameFlag(commands.FlagConverter):
    teamName: str = commands.flag(description = "Name of your team")

#Details to register user to database (Expected to be called by Qualtrics Workflow)
class registerFlag(commands.FlagConverter):
    email: str = commands.flag(description="User Email Address")
    username: str = commands.flag(description="Discord Username")
    role: str = commands.flag(desription="User Role")

#-------------------"/" Command Methods-----------------------------
#Init DB's
team_cursor = connect_to_team_db(TEAM_DATABASE)
user_cursor = connect_to_user_db(USER_DATABASE)


#Test Greet Command
@bot.command()
async def greet(ctxt, name: str):
    await ctxt.send(f'Hi {name}, how\'s your day going? ')

'''
* @requires 
    - Email entered is in database
    - Discord Username matches the user whose email was entered
* @ensures
    - User gains "verified" role
    - User in database is updated to verified
'''
@bot.command()
async def verify(Context, flags: emailFlag):
    username = Context.author
    email = flags.email

    #Search Database for user with matching email

    #If user exists, check if discord username exists

    # else, respond saying either email not found or discord username doesn't match and to contact administration
    
'''

'''
@bot.command()
async def overify(Context, flags: emailFlag):
    username = Context.author
    email = flags.email

    #Search Database for user with matching email

    #If user exists, check if discord username exists

    # else, respond saying either email not found or discord username doesn't match and to contact administration
    

'''
* @requires 
    - Cannot already be in a team
    - Must be Verified
    - Team cannot already exist

* @ensures
    - Team is added to database
    - Format is [Team Token, Team Name, Members...]
'''
@bot.command()
async def createTeam(ctxt, *, args: str, flags: teamNameFlag):
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

@bot.command()
async def registerUser(ctxt, *, flags: emailFlag):
    cursor.execute('INSERT INTO users (name) VALUES (?)', (flags.emal))
    conn.commit()

    #send success message
    await ctxt.send(f'Email: {flags.email} was successfully added')

@bot.command()
async def deleteTeam(ctxt):
    pass


#When the bot is ready, this automatically runs
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


#Get Bot Token and start running on server
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(DISCORD_BOT_TOKEN)