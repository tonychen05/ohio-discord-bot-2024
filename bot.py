import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import data


#Load in Bot Key
load_dotenv()

#Init Bot Settings
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
   
#---------------------Constants----------------------

MAX_TEAM_SIZE = 4
TEAM_FORMATION_TIMEOUT = 60

# --------------------Helper Methods-------------------



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
    role: str = commands.flag(description="User Role")

#-------------------"/" Command Methods-----------------------------
#Init DB's


#Test Greet Command
@bot.tree.command(description="test command")
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
@bot.tree.command(description="Verify your Discord account for this event.")
async def verify(Context, email: str): #TODO
    username = Context.author
    # email = flags.email

    #Search Database for user with matching email
    
    #If user exists, check if discord username exists

    # else, respond saying either email not found or discord username doesn't match and to contact administration
    
'''
* @requires
    - User sending command is admin
* @ensures
    - User gains assigned role
    - Database is updated accordingly
'''
@bot.tree.command(description="Manually verify a Discord account for this event.")
async def overify(Context, email: str, role: str):  #TODO
    admin_username = Context.author
    # user = flags.username
    # email = flags.email

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
    - Discord Channels are created
    - User gets role updated
'''
@bot.tree.command(description="Create a new team for this event") #TODO
async def createteam(ctxt, *, teamname: str):
    pass

'''
* @requires
    - User calling command is in the team or an admin
* @ensures
    - Team is removed from Databse
    - Discord Channels are removed
    - Rolls are removed from Users
'''
@bot.tree.command(description="Remove a team from this event") #TODO
async def deleteteam(ctxt, teamname: str):
    pass
    
'''
* @requires
    - Member is in the server
    - Member is not currently in a team
    - Member is Verified
* @ensures
    - Member is added to team in db
    - Member is given the team role
    - Send message to team channel
'''
@bot.tree.command(description="Add a member to your team.") # TODO
async def addmember(ctxt, username: discord.Member):
    pass

'''
* @requires
    - Member is in a team
* @ensures
    - Member is removed from team db
    - Member has team role removed
    - Send message to team channel
'''
@bot.tree.command(description="Leave your current team.") #TODO
async def leaveteam(ctxt):
    pass

'''
* @requires
    - Must be an admin
    - Must provide 2 arguments for (previous name, new name)
* @ensures
    - Team name is altered in db
    - Role name is changed
    - Users are assigned the new role
    - Channel names are changed
'''
@bot.tree.command(description="Rename a team in the event.") #TODO
async def renameteam(ctxt, oldname: str, newname: str):
    pass



#When the bot is ready, this automatically runs
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')



#Get Bot Token and start running on server
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(DISCORD_BOT_TOKEN)