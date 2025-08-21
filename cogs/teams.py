import core.records as records
import config

import asqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio

MAX_TEAM_SIZE = 4
TEAM_FORMATION_TIMEOUT = 120


class TeamsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.check_expired_teams.start()
        self.logger.info(f'TeamsCog initialized with {bot.user}')

    def cog_unload(self):
        self.check_expired_teams.cancel()

    async def delete_team_channels(self, guild, team_id: int):
        """
        Deletes all channels and role associateed with a team, and removes the team from database

        Args:
            team_id (int): The unique ID of the team to delete.
            
        Requires:
            team_id exists and associated with a team
        """
        team = await records.get_team(team_id)
        if not team:
            return

        category_id = team.get('category_id')
        if not category_id:
            self.logger.error(f'No category_id found for team {team_id}. Cannot delete channels.')
            return

        category = guild.get_channel(category_id)
        if not category:
            self.logger.error(f'No category found for team {team_id}. Cannot delete channels.')
            return

        # Delete all channels in the category
        for channel in category.channels:
            try:
                await channel.delete()
                self.logger.info(f'Deleted channel {channel.name} in category {category.name}')
            except discord.Forbidden:
                self.logger.error(f'Forbidden error while deleting channel {channel.name}. Check bot permissions.')
            except discord.HTTPException as e:
                self.logger.error(f'HTTPException while deleting channel {channel.name}: {e}')
            await asyncio.sleep(0.5)  # Small delay to avoid rate limits
        await category.delete()  # Delete the category itself
        self.logger.info(f'Deleted category and channels {category.name} for team {team_id}')

        # Remove team from database
        await records.remove_team(team_id)

    async def handle_team_formation_timeout(self, guild, team_id: int): 
        """
        Handles the timeout of team formation when team doesn't meet minimum size requirement
        
        If team has fewer than two members when timeout, this function will:
            1. remove team assigned role from all current members of team.
            2. remove team association from members in database
            3. delete team associated channels
            4. sends message explaining timeout and team re-creation process

        Args:
            guild (discord.Guild): The guild where the team exists.
            team_id (int): The unique ID of the team
        """
        if await records.team_exists(team_id) and await records.get_team_size(team_id) <= 1:
            # Remove Role and team_id from each user on team
            team_members = await records.get_team_members(team_id)
            team = await records.get_team(team_id)
            if not team:
                return

            for member_id in team_members:
                member = guild.get_member(member_id)
                if not member:
                    continue
                await member.remove_roles(
                    guild.get_role(team['role_id']),
                    guild.get_role(config.discord_team_assigned_role_id)
                )
                await records.remove_from_team(member_id)
                try:
                    await member.send(
                        content = (
                            f'Team formation timed out.'
                            f'Teams must have at least two members in {round(TEAM_FORMATION_TIMEOUT/60)} minutes'
                            f'after creation to be saved. '
                            f'You may re-create your team and use the `/addmember` command to add'
                            f'members to your team within {round(TEAM_FORMATION_TIMEOUT/60)} minutes of using the `/createteam` command.'
                    ))
                except discord.Forbidden:
                    self.logger.warning(f'Could not send timeout message to {member}. User may have DMs disabled.')

            await self.delete_team_channels(guild, team_id)

    @tasks.loop(seconds=60)
    async def check_expired_teams(self):
        expired_teams = await records.get_expired_teams(TEAM_FORMATION_TIMEOUT)
        for team_id in expired_teams:
            guild = self.bot.get_guild(config.discord_guild_id)
            if not guild:
                self.logger.error(f"Could not find guild with id {config.discord_guild_id}")
                continue
            await self.handle_team_formation_timeout(guild, team_id)

    @check_expired_teams.before_loop
    async def before_check_expired_teams(self):
        await self.bot.wait_until_ready()

    @app_commands.checks.has_any_role(config.discord_verified_role_id, 'Verified')
    @app_commands.command(name='createteam', description="Create a new team for this event")
    async def create_team(self, interaction: discord.Interaction, team_name: str):
        self.logger.info(f'Attempting to create team: {team_name} by {interaction.user}')
        
        # Check that user is verified
        if not await records.verified_user_exists(interaction.user.id):
            await interaction.response.send_message(
                content="You are not verified! Please verify yourself with the /verify command",
                ephemeral=True)
            return

        # Check that user is not in another team
        if await records.is_member_on_team(interaction.user.id):
            await interaction.response.send_message(
                content="You are already on a team. You can leave with the /leaveteam command",
                ephemeral=True)
            return

        # Check that team doesn't already exist
        if await records.team_name_exists(team_name):
            await interaction.response.send_message(
                content="That team name is already in use. Please chose a different name",
                ephemeral=True)
            return

        # Create Team Role create channel permissions
        everyone_role = interaction.guild.default_role
        team_role = await interaction.guild.create_role(name=team_name)

        # Sets up permissions:
        #   - @everyone -> cannot view channel
        #   - team_role -> can view channel
        category_channel_perms = {
            everyone_role: discord.PermissionOverwrite(view_channel=False),  
            team_role: discord.PermissionOverwrite(view_channel=True),               
        } 
        voice_channel_perms={
            everyone_role: discord.PermissionOverwrite(view_channel=False, connect=False, speak=False),
            team_role: discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
        }

        try:
            # Create Channels
            category_channel = await interaction.guild.create_category_channel(
                f"Team ## - {team_name}", 
                overwrites=category_channel_perms)
            text_channel = await category_channel.create_text_channel(
                f"{team_name.replace(' ','-')}-text") # Inherit perms from Category
            voice_channel = await category_channel.create_voice_channel(
                f"{team_name.replace(' ','-')}-voice", 
                overwrites=voice_channel_perms)
            self.logger.info(f'Created team channels: {text_channel.name}, {voice_channel.name} in category {category_channel.name}')
        except discord.Forbidden:
            await interaction.response.send_message(
                content="An error occurred while creating the team channels. Please contact a server admin.",
                ephemeral=True)
            self.logger.error("Forbidden error while creating team channels. Check bot permissions.")
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                content=f"An error occurred while creating the team channels. Please contact a server admin.",
                ephemeral=True)
            self.logger.error(f"HTTPException while creating team channels: {e}")
            return

        # Create Team in Database
        channels = {
            'category_id': category_channel.id,
            'text_id': text_channel.id,
            'voice_id': voice_channel.id,
            'role_id': team_role.id
        }

        try:
            async with asqlite.connect(records._DATABASE_FILE) as db:
                async with db.transaction():
                    team_id = await records.create_team(team_name, channels)
                    await records.add_to_team(team_id, interaction.user.id) # Add user to team
        except Exception as e:
            self.logger.error(f"Error creating team in database: {e}")
            await interaction.response.send_message(
                content="An error occurred while creating the team. Please contact a server admin.",
                ephemeral=True)
            return

        # Assign role to user and send confirmation message
        await category_channel.edit(name=f"Team {team_id} - {team_name}")
        await interaction.user.add_roles(team_role)
        await interaction.user.add_roles(interaction.guild.get_role(config.discord_team_assigned_role_id))
        await interaction.response.send_message(
            content = (
                f'Team creation succeeded. {team_role.mention} created. '
                f'Make sure to add members to your team using the `/addmember` command. '
                f'Teams with fewer than 2 members will be deleted after '
                f'{round(TEAM_FORMATION_TIMEOUT/60)} minutes.'
            ))
        self.logger.info(f'Team {team_name} created with ID {team_id} by {interaction.user}')

    @app_commands.command(name='leaveteam', description="Leave your current team")
    @app_commands.checks.has_any_role(config.discord_team_assigned_role_id, 'Team Assigned')
    async def leave_team(self, interaction: discord.Interaction):
        # Ensure user is on a team
        if not await records.is_member_on_team(interaction.user.id):
            await interaction.response.send_message(
                content="You cannot leave a team since you are not assigned to one!",
                ephemeral=True)
            return

        team_id = await records.get_user_team_id(interaction.user.id)
        role_id = await records.get_team(team_id)['team_role_id']

        team_assigned_role = interaction.guild.get_role(config.discord_team_assigned_role_id)
        team_role = interaction.guild.get_role(role_id)
        team_text_channel = interaction.guild.get_channel(await records.get_team(team_id)['text_channel_id'])

        try:
            async with asqlite.connect(records._DATABASE_FILE) as db:
                async with db.transaction():
                    # Remove user from team in Database
                    await records.remove_from_team(interaction.user.id)
        except Exception as e:
            self.logger.error(f"Error leaving team in database: {e}")
            await interaction.response.send_message(
                content="An error occurred while leaving the team. Please contact a server admin.",
                ephemeral=True)
            return

        # Remove role from user
        await interaction.user.remove_roles(team_role, team_assigned_role)
        
        # Send message back confirming removal
        await interaction.response.send_message(
            content=f"You have successfully been removed from the team {team_role.mention}",
            ephemeral=True
        )

        await team_text_channel.send(content=f'{interaction.user.mention} has left the team.')
        self.logger.info(f'{interaction.user} has left team {team_id} ({team_role.name})')
        
        # Delete team if no one is left
        if await records.get_team_size(team_id) == 0:
            await self.delete_team_channels(interaction.guild, team_id)
            self.logger.info(f'Team {team_id} ({team_role.name}) deleted due to no members left.')


    @app_commands.command(name='addmember', description="Add a member to your team")
    @app_commands.checks.has_any_role(config.discord_team_assigned_role_id, 'Team Assigned')
    @app_commands.describe(member="The member to add to your team")
    async def add_member(self, interaction: discord.Interaction, member: discord.Member):
        team_user = interaction.user # User who invoked the command
        user_to_add = member

        # Check that team_user is in a team
        if not await records.is_member_on_team(team_user.id):
            await interaction.response.send_message(
                content='Failed to add team member. You are not currently in a team. You must be in a team to add a team member. Please use `/createteam` to create a team or have another participant use `/addmember` to add you to their team',
                ephemeral=True
                )
            return
        
        # Check that team is not full
        team_id = await records.get_user_team_id(team_user.id)
        if await records.get_team_size(team_id) >= MAX_TEAM_SIZE:
            await interaction.response.send_message(
                content=f'Failed to add team member. There is no space in your team. Teams can have a maximum of {MAX_TEAM_SIZE} members.',
                ephemeral=True
                )
            return
        
        # Check that added_user is verified and a participant
        if not (await records.verified_user_exists(user_to_add.id) and await records.user_is_participant(user_to_add.id)):
            await interaction.response.send_message(
                content=f'Failed to add team member. `@{user_to_add.name}` is not a verified participant. All team members must be verified participants.',
                ephemeral=True
                )
            return
        
        # Check that added_user is not on a team
        if await records.is_member_on_team(user_to_add.id):
            await interaction.response.send_message(
                content=f'Failed to add team member. {user_to_add.mention} is already in a team. To join your team, they must leave their current team.',
                ephemeral=True
                )
            return
        
        # Add the member to the team
        try:
            async with asqlite.connect(records._DATABASE_FILE) as db:
                async with db.transaction():
                    await records.add_to_team(team_id, user_to_add.id)
        except Exception as e:
            self.logger.error(f"Error adding member to team in database: {e}")
            await interaction.response.send_message(
                content="An error occurred while adding the member to the team. Please contact a server admin.",
                ephemeral=True)
            return

        # Retrieve the team text channel and role
        team = await records.get_team(team_id)
        text_channel = interaction.guild.get_channel(team['text_id'])
        team_role = interaction.guild.get_role(team['role_id'])

        # Assign added user team and team_assigned role
        await user_to_add.add_roles(team_role)
        await user_to_add.add_roles(interaction.guild.get_role(config.discord_team_assigned_role_id))
        
        # Send confirmation message to team_user
        await interaction.response.send_message(
            content=f'Team member added successfully. {user_to_add.mention} has been added to {team_role.mention}.',
            ephemeral=True
            )
        
        # Notify team in team text channel of new member
        await text_channel.send(content=f'{user_to_add.mention} has been added to the team by {team_user.mention}.')
        self.logger.info(f'{user_to_add} has been added to team {team_id} ({team_role.name}) by {team_user}')

async def setup(bot) -> None:
    await bot.add_cog(TeamsCog(bot))
