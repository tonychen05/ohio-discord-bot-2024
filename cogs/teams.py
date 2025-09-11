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
        self.logger.info(f'TeamsCog initialized with {bot.user}')

    async def delete_team(self, guild, team_id: int):
        """
        Deletes all channels and role associated with a team, and removes the team from database

        Args:
            guild (discord.Guild): The Discord guild where the team exists.
            team_id (int): The unique ID of the team to delete.

        Requires:
            team_id exists and associated with a team
        """
        team = await records.get_team(team_id)

        if not team:
            self.logger.error(f'Team {team_id} not found in database.')
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
        
        # Delete the category itself
        await category.delete()  
        self.logger.info(f'Deleted category and channels {category.name} for team {team_id}')

        # Remove team from database
        await records.remove_team(team_id)

    @app_commands.command(name='createteam', description="Create a new team for this event")
    @app_commands.checks.has_any_role(config.discord_verified_role_id, 'Verified')
    @app_commands.describe(team_name="The name of your team", member_to_add="A member to add to your team (not yourself)")
    async def create_team(self, interaction: discord.Interaction, team_name: str, member_to_add: discord.Member):
        self.logger.info(f'Attempting to create team: {team_name} by {interaction.user}')

        # Check that user is verified (shouldn't happen due to @app_commands.checks.has_any_role)
        if not await records.verified_user_exists(interaction.user.id):
            await interaction.response.send_message(
                content="You are not verified! Please verify yourself with the /verify command",
                ephemeral=True)
            return
        
        # Ensure team member 1 is not the user
        if member_to_add.id == interaction.user.id:
            await interaction.response.send_message(
                content="You cannot add yourself to the team. Teams must have at least 2 members.",
                ephemeral=True)
            return

        # Check that user is not in another team
        if await records.is_member_on_team(interaction.user.id):
            await interaction.response.send_message(
                content="You are already on a team. You can leave with the /leaveteam command",
                ephemeral=True)
            return

        # Check that member to add is not in another team
        if await records.is_member_on_team(member_to_add.id):
            await interaction.response.send_message(
                content="That user is already on a team.",
                ephemeral=True)
            return
        
        # Check that member to add is verified
        if not await records.verified_user_exists(member_to_add.id):
            await interaction.response.send_message(
                content="That user is not verified.",
                ephemeral=True)
            return

        # Check that team name used doesn't already exist
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
                    await records.add_to_team(team_id, member_to_add.id) # Add member to team
        except Exception as e:
            self.logger.error(f"Error creating team in database: {e}")
            await interaction.response.send_message(
                content="An error occurred while creating the team. Please contact a server admin.",
                ephemeral=True)
            return

        # Assign role to user and send confirmation message
        team_assigned_role = interaction.guild.get_role(config.discord_team_assigned_role_id)
        if not team_assigned_role:
            # Fallback to searching by name
            team_assigned_role = interaction.guild.get_role(discord.utils.get(interaction.guild.roles, name='Team Assigned').id)

        await category_channel.edit(name=f"Team {team_id} - {team_name}")
        await interaction.user.add_roles(team_role, team_assigned_role) # Add role to user
        await member_to_add.add_roles(team_role, team_assigned_role)    # Add role to member

        await interaction.response.send_message(
            content = (
                f'Team creation succeeded. {team_role.mention} created. '
                f'Add more members to your team using the `/addmember` command. '
            ))
        self.logger.info(f'Team {team_name} created with ID {team_id} by {interaction.user}')

    @app_commands.command(name='leaveteam', description="Leave your current team")
    @app_commands.checks.has_any_role(config.discord_team_assigned_role_id, 'Team Assigned')
    async def leave_team(self, interaction: discord.Interaction):

        # Ensure user is on a team (shouldn't happen due to @app_commands.checks.has_any_role)
        if not await records.is_member_on_team(interaction.user.id):
            await interaction.response.send_message(
                content="You cannot leave a team since you are not assigned to one!",
                ephemeral=True)
            return

        team_id = await records.get_user_team_id(interaction.user.id)
        role_id = await records.get_team_role_id(team_id)

        team_assigned_role = interaction.guild.get_role(config.discord_team_assigned_role_id)
        if not team_assigned_role:
            # Fallback to searching by name
            team_assigned_role = interaction.guild.get_role(discord.utils.get(interaction.guild.roles, name='Team Assigned').id)

        team_role = interaction.guild.get_role(role_id)
        team_text_channel = interaction.guild.get_channel(await records.get_team_text_id(team_id))

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
        await interaction.user.remove_roles(*[team_role, team_assigned_role])

        # Send message back confirming removal
        await interaction.response.send_message(
            content=f"You have successfully been removed from the team {team_role.mention}",
            ephemeral=True
        )

        await team_text_channel.send(content=f'{interaction.user.mention} has left the team.')
        self.logger.info(f'{interaction.user} has left team {team_id} ({team_role.name})')
        
        # Delete team if no one is left
        if await records.get_team_size(team_id) == 0:
            await self.delete_team(interaction.guild, team_id)
            self.logger.info(f'Team {team_id} ({team_role.name}) deleted due to no members left.')


    @app_commands.command(name='addmember', description="Add a member to your team")
    @app_commands.checks.has_any_role(config.discord_team_assigned_role_id, 'Team Assigned')
    @app_commands.describe(member="The member to add to your team")
    async def add_member(self, interaction: discord.Interaction, member: discord.Member):
        team_user = interaction.user # User who invoked the command
        user_to_add = member

        # Check that team_user is in a team (shouldn't happen due to @app_commands.checks.has_any_role)
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
        
        # Check that user_to_add is verified and a participant
        if not (await records.verified_user_exists(user_to_add.id) and await records.user_is_participant(user_to_add.id)):
            await interaction.response.send_message(
                content=f'Failed to add team member. `@{user_to_add.name}` is not a verified participant. All team members must be verified participants.',
                ephemeral=True
                )
            return
        
        # Check that user_to_add is not on a team
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
        text_channel = interaction.guild.get_channel(team.get('text_id'))
        team_role = interaction.guild.get_role(team.get('role_id'))

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
