import os
import records
import config
import web

import discord
from discord.ext import commands
import math
import asyncio
from aiohttp import web
import random
import smtplib
from email.mime.text import MIMEText

"""
Valid Roles:
    - participant
    - mentor
    - judge
    - organizer
"""

#Init Bot Settings
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='/', intents=intents)

#---------------------Constants----------------------

MAX_TEAM_SIZE = 4
TEAM_FORMATION_TIMEOUT = 20

# --------------------Helper Methods-------------------
async def assign_user_roles(user, roles: list):
    for role in roles:
        if (role == "participant"):
            await user.add_roles(discord.utils.get(user.guild.roles, id=config.discord_participant_role_id))
        elif (role == "mentor"):
            await user.add_roles(discord.utils.get(user.guild.roles, id=config.discord_mentor_role_id))
        elif (role == "judge"):
            await user.add_roles(discord.utils.get(user.guild.roles, id=config.discord_judge_role_id))
        elif (role == "organizer"):
            await user.add_roles(discord.utils.get(user.guild.roles, id=config.discord_organizer_role_id))
        elif (role == 'verified'):
            await user.add_roles(discord.utils.get(user.guild.roles, id=config.discord_verified_role_id)) 

def generate_random_string(n):
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.choices(characters, k=n))    

async def handle_team_formation_timeout(ctxt: discord.Interaction, team_id: int):
    if records.team_exists(team_id) and records.get_team_size(team_id) <= 1:
        # Remove Role and team_id from each user on team
        for member in records.get_team_members(team_id):
            await remove_roles(ctxt.guild.get_member(member[0]), [ctxt.guild.get_role(config.discord_team_assigned_role_id)])
            records.drop_team(member[0])
        # Remove all Channels
        await delete_team(team_id)
        await ctxt.send(ephemeral=True,
                        content=f'Team formation timed out. Teams must have at least two members {round(TEAM_FORMATION_TIMEOUT/60, 2)} minutes after creation to be saved. You must re-create your team and use the `/addmember` command to add members to your team within one minute of using the `/createteam` command.')

async def send_verification_email(recipient, CODE, username):
    #Generate one time code
    LINK = f"http://{config.email_domain_name}:{config.email_get_port}/verify?code={CODE}"

    body = f"""Dear {records.get_first_name(recipient)},<br>
        To verify that your email is associated with the discord account: {username}, please click the link below:<br><br>
        <a href="{LINK}">{LINK}</a><br><br>
        If you didn’t attempt to verify your account, you can safely ignore this email.<br><br>
        This link will expire in {round(config.email_code_expiration_time/60, 2)} minutes. If it has expired, please request a new verification email.<br><br>
        Thank you,<br>
        OHI/O Hackathon Team<br><br>
        If you have any issues or questions, please contact us at {config.contact_organizer_email} or message in the Ask an Organizer channel on discord
        """
    msg = MIMEText(body, 'html')
    msg['Subject'] = 'Verify your Discord Account'
    msg['From'] = config.email_address
    msg['To'] = recipient
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(config.email_address, config.email_password)
            smtp_server.sendmail(config.email_address, recipient, msg.as_string())

        return True
    except Exception as e:
        print(f"ERROR: Message not to {recipient} not sent. ERROR: {e}")
        return False

async def delete_team(team_id: int):
    # Get all channels from database
    guild = bot.get_guild(config.discord_guild_id)
    channels = records.get_team(team_id)['channels']

    #Delete all channels and role
    for channel in channels:
        if(channel == 'role'):
            await guild.get_role(channels[channel]).delete()
        else:
            await guild.get_channel(channels[channel]).delete()

    # Remove team from database
    records.remove_team(team_id)

async def remove_roles(user: discord.Member, roles:list):
    roles_set = set(roles)
    old_roles = user.roles
    new_roles = []

    # If role is not contained in the set of roles to remove
    for roles in old_roles:
        if not roles in roles_set:
            new_roles.append(roles)

    # Update user with new roles
    await user.edit(roles=new_roles)
# ---------------------Classes-------------------------

#Retrieves Member username (Can be used for adding members)
class userFlag(commands.FlagConverter):
    member: discord.Member = commands.flag(description='The User being selected')

#Retrieves Email
class emailFlag(commands.FlagConverter):
    email: str = commands.flag(description = 'Email Address used to Register')

#Retrieves Team Name
class teamNameFlag(commands.FlagConverter):
    teamname: str = commands.flag(description = "Name of your team")

#Details to register user to database (Expected to be called by Qualtrics Workflow)
class registerFlag(commands.FlagConverter):
    user: discord.Member = commands.flag(description="Discord User")
    email: str = commands.flag(description="User Email Address")
    role: discord.Role = commands.flag(description="User Role")

#-------------------"/" Command Methods-----------------------------

#Test Greet Command
@bot.tree.command(description="Recieve a random affirmation for encouragement")
async def affirm(ctxt):
    affirmations = {
        "You're doing amazing—every line of code is one step closer to something great!",
        "Remember, the best solutions often come from the toughest challenges. Keep going!",
        "You belong here. Your ideas matter and are worth sharing.",
        "It's not about having all the answers; it's about asking the right questions. You're doing great!",
        "Every bug you squash is a step closer to innovation. Keep debugging!",
        "Your creativity is your superpower. Let it shine!",
        "It's okay to take breaks. Rest fuels brilliance.",
        "You’re capable of more than you realize—trust the process.",
        "Collaboration is key, and you're an invaluable part of your team!",
        "Progress, not perfection, is the goal. You're moving forward, and that's what counts.",
        "Hackathons are marathons, not sprints. Pace yourself and enjoy the journey!",
        "Remember, even the greatest projects started with a single idea. Keep building!",
        "You’re not alone; your teammates and community are here to support you.",
        "Every keystroke is an act of creativity. You're a digital artist!",
        "Challenges are opportunities in disguise. Embrace them and thrive!",
        "Your dedication inspires others. Keep up the amazing work!",
        "Celebrate small victories—they lead to big successes!",
        "Think outside the box. Your unique perspective is your advantage!",
        "You're making something out of nothing—that's incredible!",
        "No matter the outcome, you're learning, growing, and creating. That's a win!"
    }
    random_affirm = random.choice(list(affirmations))
    await ctxt.response.send_message(ephemeral=True, content=f'{random_affirm}')

# ----------- Email/Account Verification ----------------------------------------------
'''
* @requires 
    - Email entered is in database
    - Discord Username matches the user whose email was entered
    - User is not already verified (check role)
* @ensures
    - User gains "verified" role
    - User in database is updated to verified
'''
@bot.hybrid_command(description="Verify your Discord account for this Event")
async def verify(ctxt, flags: emailFlag):
    user = ctxt.author
    email = flags.email

    #Confirm user is registered
    if not records.registered_user_exists(email):
        await ctxt.send(ephemeral=True,
                        content=f"There are no user's registered with the email: `<{email}>`. Please verify using the correct email, reregister at {config.contact_registration_link}, or contact administration.")
        return
    
    #Check if user is already verified
    if records.verified_user_exists(user.id):
        first_name = records.get_first_name(records.get_verified_email(user.id))
        await ctxt.send(ephemeral=True,
                        content=f"Welcome, {first_name}! You are already verified.")
        return

    # Check if email is in verified DB
    if records.verified_email_exists(email):
        await ctxt.send(ephemeral=True,
                        content=f"A User with that email address is already verified. Please reregister with a different email address at {config.contact_registration_link}")
        return
    
    # Store discord_id with registered user
    records.update_reg_discord_id(email, user.id)

    # Remove any codes from same user so only newest link will work
    records.remove_user_codes(user.id)

    # Send Verification Info to web for update
    CODE = generate_random_string(20)
    if(await send_verification_email(email, CODE, user.name)):
        # add code to verification codes and send message
        records.add_code(CODE, user.id)
        await ctxt.send(ephemeral=True,
                        content=f"Check your inbox for an email from `<{config.email_address}>` with a verification link. Please check your email and click the link to verify your account.")
    else:
        await ctxt.send(ephemeral=True,
                        content="Failed to send verification email. Please contact an organizer for assistance.")

    ## Wait for timeout then delete verification code
    await asyncio.sleep(config.email_code_expiration_time)
    records.remove_code(CODE)

#@app.route('/verify', ['GET'])
async def check_verification_code(request):
    code = request.query.get('code', None)
    
    # Check that a code is provided
    if code == None:
        return web.Response(text="No Verification Code Provided")
        
    # Check that code is valid
    if not records.code_exists(code):
        return web.Response(text="Your Verification Code is either not valid or has expired. Please request a new one.")
        
    # Retrieve Message ID or Verification message
    user_id = records.get_value_from_code(code)

    try: 
        # Complete Verification
        await complete_verification(user_id)

        # Remove Code from database
        records.remove_code(code)

        return web.Response(text="Verification Successful")
    except Exception as e:
        print(f"ERROR: Verification Failed - {e}")
        return web.Response(text="Verification Failed: An Internal Error has occured. Please contact an organizer for help")

async def complete_verification(user_id):
    guild = bot.get_guild(config.discord_guild_id)
    user = guild.get_member(user_id)
    email = records.get_email_from_reg(user_id)

    # Add user to verified database
    records.add_verified_user(user.id, email, user.name)

    # Assign user the verified role
    await assign_user_roles(user, ['verified'])

    # Assign user with all given roles
    roles = records.get_roles(email)
    await assign_user_roles(user, roles)
    
    ## Send the user a message that they have been verified and the next steps
    await user.send(content=f"Welcome {records.get_first_name(email)}! \nYou have been verified. Please check the {bot.get_guild(config.discord_guild_id).get_channel(config.discord_start_here_channel_id).mention} channel for next steps.")
    
# -------------------------------------------------------------------------------------
'''
* @requires
    - User sending command is admin (check role)
* @ensures
    - User gains assigned role
    - Database is updated accordingly 
        (if user doesn't exist, add them with role, if they do exist, update role)
'''
@bot.hybrid_command(description="Manually verify a Discord account for this event (Organizers only)")
async def overify(ctxt, flags: registerFlag):
    admin_user = ctxt.author

    username = flags.username
    email = flags.email
    role = flags.role
    user = discord.utils.get(ctxt.guild.members, name=username)


    # Check that user is an admin [check role]
    if not admin_user.guild_permissions.administrator:
        await ctxt.send(ephemeral=True,
                        content="You do not have permission to use this command.")
        return
    
    # Check if user is already verified
    if records.verified_user_exists(user.id):

        #Check if user has role specified, else add it
        if role in records.get_verified_user(user.id)['roles']:
            await ctxt.send(ephemeral=True,
                            content=f"`<{username}>` is verified and has the role `<{role}>` already.")
            return
        
        # Assign user the role
        await assign_user_roles(user, [role])
    
        # Update user in database
        roles = records.get_roles(email)
        roles.append(role) 
        records.reassign_roles(email, roles)

        await ctxt.send(ephemeral=True,
                        content=f"`<{username}>` is already verified but has been given the role `<{role}>`.")
        return

    # If User is not registered, add a registered user with no data
    if not records.registered_user_exists(email):
        records.add_registered_user(email, [role], {})
    
    # Add user to verified database
    records.add_verified_user(user.id, email, username)

    await assign_user_roles(user, [role, 'verified'])

    await ctxt.send(ephemeral=True,
                    content=f"`<{username}>` has been verified and given the role `<{role}>`.")

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
@bot.hybrid_command(description="Create a new team for this event")
async def createteam(ctxt, flags: teamNameFlag):
    # Retrieve Context
    user = ctxt.author
    team_name = flags.teamname

    # Check that user is verified
    if not records.verified_user_exists(user.id):
        await ctxt.send(ephemeral=True,
                        content=f"You are not verified! Please verify yourself with the /verify command")

    # Check that user is not in team
    if records.is_member_on_team(user.id):
        await ctxt.send(ephemeral=True,
                        content=f"You are already on a team. You can leave with the /leaveteam command")
        return

    # Check that team doesn't already exist
    if records.team_name_exists(team_name):
        await ctxt.send(ephemeral=True,
                        content=f"That team name is already in use. Please chose a different name")
        print(records.get_number_of_teams())
        return

    # Create Team Role create channel permissions
    team_role = await ctxt.guild.create_role(name=team_name)

    category_channel_perms = {
        ctxt.guild.get_role(config.discord_all_access_pass_role_id): discord.PermissionOverwrite(view_channel=True),
        ctxt.guild.default_role: discord.PermissionOverwrite(view_channel=False),  
        team_role: discord.PermissionOverwrite(view_channel=True),               
    } 
    voice_channel_perms={
        team_role: discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
        ctxt.guild.get_role(config.discord_all_access_pass_role_id): discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
        ctxt.guild.default_role:  discord.PermissionOverwrite(view_channel=False)
    }

    # Create Channels
    category_channel = await ctxt.guild.create_category_channel(f"Team ## - {team_name}", overwrites=category_channel_perms)
    text_channel = await category_channel.create_text_channel(f"{team_name.replace(' ','-')}-text") # Inherit perms from Category
    voice_channel = await category_channel.create_voice_channel(f"{team_name.replace(' ','-')}-voice", overwrites=voice_channel_perms)

    # Create Team in Database
    channels = {
        'category': category_channel.id,
        'text': text_channel.id,
        'voice': voice_channel.id,
        'role': team_role.id
    }

    team_id = records.create_team(team_name, channels)
    records.join_team(team_id, user.id) # Add user to team

    # Assign role to user and send message
    await category_channel.edit(name=f"Team {team_id} - {team_name}")
    await user.add_roles(team_role)
    await user.add_roles(ctxt.guild.get_role(config.discord_team_assigned_role_id))
    await ctxt.send(ephemeral=True,
                    content=f'Team creation succeeded. {team_role.mention} created. Make sure to add members to your team using the `/addmember` command. Teams with fewer than 2 members will be deleted after {round(TEAM_FORMATION_TIMEOUT/60, 2)} minutes.')

    # Wait for team timeout
    await asyncio.sleep(TEAM_FORMATION_TIMEOUT)
    await handle_team_formation_timeout(ctxt, team_id)

'''
* @requires
    - Member is in a team
* @ensures
    - Member is removed from team db
    - Member has team role removed
    - Send message to team channel
'''
@bot.hybrid_command(description="Leave your current team")
async def leaveteam(ctxt):
    # Check that member is on a team
    user = ctxt.author

    # Ensure user is on a team
    if not records.is_member_on_team(user.id):
        await ctxt.send(ephemeral=True,
                        content=f"You cannot leave a team since you are not assigned to one!")
        return

    team_id = records.get_user_team_id(user.id)
    role_id = records.get_team(team_id)['channels']['role']

    team_assigned_role = ctxt.guild.get_role(config.discord_team_assigned_role_id)
    team_role = ctxt.guild.get_role(role_id)

    # Remove user from team in Database
    records.drop_team(user.id)

    # Remove role from user
    await remove_roles(user, [team_role, team_assigned_role])
    
    # Send message back confirming removal
    await ctxt.send(ephemeral=True,
                    content=f"You have successfully been removed from the team {team_role.mention}")
    await ctxt.guild.get_channel(team_id).send(content=f'{user.mention} has left the team.')

    # Delete team if no one is left
    if records.get_team_size(team_id) == 0:
        await delete_team(team_id)

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
@bot.hybrid_command(description="Add a member to your team")
async def addmember(ctxt, flags: userFlag):
    team_user = ctxt.author
    added_user = flags.member

    # Check that team_user is in a team
    if not records.is_member_on_team(team_user.id):
        await ctxt.send(ephemeral=True,
                        content=f'Failed to add team member. You are not currently in a team. You must be in a team to add a team member.')
        return
    
    # Check that team is not full
    team_id = records.get_user_team_id(team_user.id)
    if records.get_team_size(team_id) >= MAX_TEAM_SIZE:
        await ctxt.send(ephemeral=True,
                        content=f'Failed to add team member. There is no space in your team. Teams can have a maximum of {MAX_TEAM_SIZE} members.')

    # Check that added_user is verified
    if not records.verified_user_exists(added_user.id):
        await ctxt.send(ephemeral=True,
                        content=f'Failed to add team member. `{added_user.mention}` is not a verified participant. All team members must be verified participants.')
        return
    
    # Check that added_user is not on a team
    if records.is_member_on_team(added_user.id):
        await ctxt.send(ephemeral=True,
                        content=f'Failed to add team member. {added_user.mention} is already in a team. To join your team, they must leave their current team.')
        return
    
    # Add the member to the team
    records.join_team(team_id, added_user.id)

    # Assign added user team and team_assigned role
    added_user.add_roles(ctxt.guild.get_role(records.get_team(team_id)['channels']['role']))
    added_user.add_roles(ctxt.guild.get_role(config.discord_team_assigned_role_id))
    await ctxt.send(ephemeral=True,
                    content=f'Team member added successfully. {added_user.mention} has been added to {team_role.mention}.')
    await ctxt.guild.get_channel(team_id).send(content=f'{added_user.mention} has been added to the team by {team_user.mention}.')

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
@bot.command() #TODO
async def renameTeam(ctxt):
    pass

'''
* @requires
    - User calling command is in the team or an admin
* @ensures
    - Team is removed from Databse
    - Discord Channels are removed
    - Roles are removed from Users
'''
@bot.command() #TODO
async def deleteTeam(ctxt):
    pass

@bot.command(name="sync", description="Sync bot commands with server (Organizer only)")
async def sync(ctxt):
    synced_commands = await bot.tree.sync(guild=ctxt.guild)
    print(f"Refreshed Channels: [{','.join(synced_commands)}]")

#When the bot is ready, this automatically runs
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

web_app = web.Application()
web_app.add_routes([web.get('/verify', check_verification_code)])

async def main():
    ## Prepare GET Request Listener
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", config.email_get_port)
    await site.start()
    print(f"GET Listener open on port {config.email_domain_name}:{config.email_get_port}/verify")

    ## Start Bot
    await bot.start(config.discord_token)
    
def start():
    asyncio.run(main())
# ------------------------------------------------------------------


