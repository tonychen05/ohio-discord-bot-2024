import discord
from discord.ext import commands
from discord import app_commands
import core.records as records
import config
import random
import smtplib
from email.mime.text import MIMEText

class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.role_map = {
            'participant': config.discord_participant_role_id,
            'mentor': config.discord_mentor_role_id,
            'judge': config.discord_judge_role_id,
            'verified': config.discord_verified_role_id
        }
        self.logger.info(f'VerifyCog initialized with {bot.user}')

    async def generate_random_code(n: int) -> str:
        """
        Generates random string of specified length using uppercase letters, lowercase letters, and digits.

        Args:
            length (int): the length of random string to generate

        Requires:
            length (int) >= 0
            
        Returns:
            str: A random string of specified length, containing digits.
        """
        characters = '0123456789'
        return ''.join(random.choices(characters, k=n))    

    async def send_verification_email(self, recipient: str, CODE: str, username: str) -> bool:
        """
        Sends verification email to recipientwith one-time use link for verifying Discord account
        
        Args:
            recipient (str): Email address of the users to send the verificatio link to.
            CODE (str): A randomly generated verification code used in verification link.
            username (str): The Discord username of the person requesting verification.
        
        Returns:
            bool: True if email was sent successfully, False if there was error.
            
        Raises:
            Exception: If there is an error with sending email, prints error message.
        
        """
        body = f"""Dear {records.get_first_name(recipient)},<br>
            To verify that your email is associated with the discord account: {username}, please enter the code below:<br><br>
            <h3>{CODE}</h3><br>
            If you didn’t attempt to verify your account, you can safely ignore this email.<br><br>
            This code will expire in {round(config.email_code_expiration_time/60)} minutes. If it has expired, please request a new verification email.<br><br>
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
            self.logger.info(f"Verification email sent to {recipient}.")
            return True
        except Exception as e:
            self.logger.error(f"ERROR: Message not to {recipient} not sent. ERROR: {e}")
            return False

    async def verify_user(self, interaction: discord.Interaction, registrant_id: int):
        """
        Verifies a user by adding them to the verified users table and assigning roles.

        Args:
            registrant (dict): The registrant information containing 'registrant_id'.
            discord_id (int): The Discord ID of the user to be verified.
            username (str): The Discord username of the user to be verified.
        """
        discord_id = interaction.user.id
        username = interaction.user.name

        await records.update_reg_discord_id(registrant_id, discord_id)
        await records.add_verified_user(registrant_id, discord_id, username)

        # Assign roles to the user
        registrant_email = await records.get_email_by_registrant_id(registrant_id)
        roles: list = await records.get_roles(registrant_email)
        roles.append('verified')  # Ensure 'verified' role is always included
        discord_roles = [interaction.guild.get_role(role_id) for role_id in roles if interaction.guild.get_role(role_id)]
        await interaction.user.add_roles(*discord_roles)
        await interaction.response.send_message(content="You have been verified! Welcome to the event!", ephemeral=True)
        self.logger.info(f"User {username} (ID: {discord_id}) has been verified and assigned roles: {', '.join(roles)}.")
        
    @app_commands.command(name='verify', description="Verify yourself to participate in the event")
    @app_commands.describe(email_or_code="Your registered email or verification code")
    async def verify(self, interaction: discord.Interaction, email_or_code: str):
        self.logger.info(f"Verification attempt by {interaction.user.name} (ID: {interaction.user.id}) with input: {email_or_code}")
        # CASE 1: User enters an email address
        if '@' in email_or_code:
            email = email_or_code.strip().lower()

            # Check if user is already verified
            if await records.verified_user_exists(interaction.user.id):
                first_name = records.get_first_name(records.get_verified_email(interaction.user.id))
                await interaction.response.send_message(
                    content=f"Welcome, {first_name}! You are already verified.",
                    ephemeral=True
                )
                return
            
            # Check if email is already verified
            if await records.verified_email_exists(email):
                await interaction.response.send_message(
                    content=(
                        f"The email `<{email}>` is already associated with another Discord account. \n"
                        f"If you believe this is an error, please contact administration."
                    ),
                    ephemeral=True
                )
                return
            
            # Check if email is registered
            registrant = await records.get_registered_user_by_email 
            if not registrant:
                await interaction.response.send_message(
                    content=(
                        f"There are no user's registered with the email: `<{email}>`. \n" 
                        f"Please verify using the correct email, reregister at "
                        f"{config.contact_registration_link}, or contact administration."
                    ),
                    ephemeral=True
                )
                return
                
            # After all checks, send verification email
            CODE = self.generate_random_code(6)
            while await records.code_exists(CODE):
                CODE = self.generate_random_code(6)

            if (self.send_verification_email(email, CODE, interaction.name)):
                # add code to verification codes and send message
                records.add_code(CODE, registrant['registrant_id'], interaction.user.id)
                await interaction.response.send_message(
                    content=f"Check your inbox for an email from `<{config.email_address}>` with a verification link. Please check your email and enter the code in this format \n `/verify <code>`", 
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    content="Failed to send verification email. Please contact an organizer for assistance.", 
                    ephemeral=True)
    
        # CASE 2: User enters a verification code
        elif (email_or_code.isdigit()):
            code = email_or_code.strip()

            is_valid, registrant_id = await records.verify_code(code, interaction.user.id)
            if not is_valid:
                await interaction.response.send_message(
                    content="Your Verification Code is either not valid or has expired. Please request a new one.", 
                    ephemeral=True
                )
            else:
                await self.verify_user(interaction, registrant_id)
                
        else:
            await interaction.response.send_message(
                content="Please enter a valid email address or a verification code.",
                ephemeral=True
            )
            return

    @app_commands.command(name='overify', description="Manually verify a user and assign roles")
    @app_commands.describe(
        member="The Discord user to verify", 
        email="Email address of the user", 
        role="Role to assign")
    @app_commands.checks.has_role(config.discord_organizer_role_id)
    @app_commands.choices(role=[
        app_commands.Choice(name='Participant', value='participant'),
        app_commands.Choice(name='Mentor', value='mentor'),
        app_commands.Choice(name='Judge', value='judge'),
        app_commands.Choice(name='Mentor/Judge', value='mentor, judge')
    ])
    async def overify(self, interaction: discord.Interaction, member: discord.Member, email: str, role: app_commands.Choice[str]):
        self.logger.info(f"Overification attempt by {interaction.user.name} (ID: {interaction.user.id}) for {member.name} (ID: {member.id}) with email: {email} and role: {role.value}")
        roles = role.strip().split(', ')
        if not records.registered_user_exists(email):
            registrant_id = await records.add_registered_user(email, roles, {})
        else:
            registrant_id = await records.get_registrant_id(email)
        
        # Add user to verified database
        records.add_verified_user(registrant_id, member.id, member.name)

        try:
            await member.add_roles(roles)
            await interaction.response.send_message(
                content=f"Successfully assigned {', '.join(roles)} to {member.name}.",
                ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                content=f"Failed to verify user `<{member.name}>`. Error: {e}",
                ephemeral=True)
            return
        
async def setup(bot) -> None:
    await bot.add_cog(VerifyCog(bot))
