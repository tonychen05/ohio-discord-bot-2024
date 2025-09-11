from typing import Optional, Dict, Any
import asqlite
import sqlite3
import datetime
from datetime import timedelta

import os
import json
import logging
from utils.logger import setup_logging

_DATABASE_FILE = os.getenv('DATABASE_FILE', 'records.db')

# Initialize logger
db_logger = logging.getLogger('records')

_REG_TABLE_NAME = 'REGISTRANT'
_VERIFIED_TABLE_NAME = 'VERIFIED'
_TEAM_TABLE_NAME = 'TEAMS'

async def _initialize_db():
    async with asqlite.connect(_DATABASE_FILE) as db:
        # Create tables if they do not exist
        await _create_tables(db)
        # Commit the changes
        await db.commit()

async def _create_tables(db) -> None:
    try:
        # Enable foreign key constraints
        await db.execute("PRAGMA foreign_keys = ON")

        # Table for registration responses
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS {_REG_TABLE_NAME} (
                registrant_id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                is_participant INTEGER NOT NULL, -- Boolean (0 or 1)
                is_judge INTEGER NOT NULL,       -- Boolean (0 or 1)
                is_mentor INTEGER NOT NULL,      -- Boolean (0 or 1)
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                verification_code TEXT UNIQUE,
                discord_id BIGINT,              -- Discord ID for verification
                code_expires_at TEXT,            -- Storing TIMESTAMP as TEXT (ISO8601 format)
                verified_at TEXT                 -- Storing TIMESTAMP as TEXT (ISO8601 format)
            );
        """)
        db_logger.info("REGISTRANT table created successfully.")

        # Teams
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS {_TEAM_TABLE_NAME} (
                team_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                category_id BIGINT,
                text_id BIGINT,
                voice_id BIGINT,
                role_id BIGINT,
                created_at TEXT NOT NULL

            );
        """)
        db_logger.info("TEAM table created successfully.")

        # Table for verified users' data
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS {_VERIFIED_TABLE_NAME} (
                verified_id INTEGER PRIMARY KEY,
                discord_id BIGINT NOT NULL,
                registrant_id INTEGER NOT NULL,
                team_id INTEGER,
                username TEXT NOT NULL,
                FOREIGN KEY (registrant_id) REFERENCES {_REG_TABLE_NAME} (registrant_id) ON DELETE CASCADE,
                FOREIGN KEY (team_id) REFERENCES {_TEAM_TABLE_NAME} (team_id) ON DELETE SET NULL
            );
        """)
        db_logger.info("VERIFIED table created successfully.")
    except sqlite3.Error as e:
        db_logger.error(f"An error occurred while creating tables: {e}")
        raise

async def get_registrant_id(email: str) -> int:
    async with asqlite.connect(_DATABASE_FILE) as db:
        async with db.execute(
            f"SELECT registrant_id FROM {_REG_TABLE_NAME} WHERE email = ?", (email,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

# ---------- Register Data into Database ------------------------------------------------------------ DONE

async def add_registered_user(email: str, roles: list, data: dict) -> Optional[int]:
    try:
        #Check if user is not verified
        if await verified_email_exists(email):
            db_logger.warning(f"The email ({email}) is already verified. Registered user is not added")
            return

        #Check if user with that email already registerd and remove it
        if await registered_user_exists(email):
            await remove_registered_user(email)
        
        #Extract data
        is_participant = 'participant' in roles
        is_judge = 'judge' in roles 
        is_mentor = 'mentor' in roles 

        data_columns = [
        'first_name', 'last_name'
        ]

        user_data = {col: data.get(col, '') for col in data_columns}

        # Build the SQL query to insert data into the REG_RESPONSES table
        all_columns = ['email', 'is_participant', 'is_judge', 'is_mentor'] + data_columns
        column_names_str = ', '.join(all_columns);
        placeholders_str = ', '.join(['?'] * len(all_columns))
        
        values_to_insert = [email, is_participant, is_judge, is_mentor] + \
                        [user_data.get(col, '') for col in data_columns]

        query = f"INSERT INTO {_REG_TABLE_NAME} ({column_names_str}) VALUES ({placeholders_str})"

        #Insert into the database
        async with asqlite.connect(_DATABASE_FILE) as db:
            async with db.cursor() as cursor:
                await cursor.execute(query, tuple(values_to_insert))
                await cursor.execute("SELECT last_insert_rowid()")
                result = await cursor.fetchone()
                await db.commit()
                db_logger.info(f"User with email {email} added to {_REG_TABLE_NAME} with roles {roles}")
                return result[0]
    except sqlite3.Error as e:
        db_logger.error(f"Database error while adding registered user with email {email}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while adding registered user with email {email}: {e}")
        return None


async def add_verified_user(registrant_id: int, discord_id: int, username: str):
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            await db.execute(
                f'INSERT INTO {_VERIFIED_TABLE_NAME} (discord_id, registrant_id, team_id, username) VALUES (?, ?, ?, ?)',
                (discord_id, registrant_id, None, username)
            )
            await db.commit()
            db_logger.info(f"User with discord_id {discord_id} added to {_VERIFIED_TABLE_NAME}")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while adding verified user with discord_id {discord_id}: {e}")
    except Exception as e:
        db_logger.error(f"Unexpected error while adding verified user with discord_id {discord_id}: {e}")


async def create_team(team_name: str, channels: dict) -> int:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            async with db.cursor() as cursor:
                created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                await cursor.execute(
                    f'INSERT INTO {_TEAM_TABLE_NAME} (name, category_id, text_id, voice_id, role_id, created_at) VALUES (?, ?, ?, ?, ?, ?)', 
                    (team_name, channels.get('category_id'), channels.get('text_id'), channels.get('voice_id'), channels.get('role_id'), created_at)
                )
                await cursor.execute("SELECT last_insert_rowid()")
                result = await cursor.fetchone()
                await db.commit()
                db_logger.info(f"Team {team_name} created successfully with channels {channels}")
                return result[0]
    except sqlite3.Error as e:
        db_logger.error(f"Database error while creating team {team_name}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while creating team {team_name}: {e}")
        return None
    

# ------------ Remove Entries from Tables -------------------------------------------------------------------------- DONE

async def remove_registered_user(email: str) -> None:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            await db.execute(f'DELETE FROM {_REG_TABLE_NAME} WHERE email = ?',
                             (email,))
            await db.commit()
            db_logger.info(f"User with email {email} removed from {_REG_TABLE_NAME}")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while removing user with email {email}: {e}")
    except Exception as e:
        db_logger.error(f"Unexpected error: {e}")

async def remove_verified_user(discord_id: int) -> None:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            await db.execute(
                f'DELETE FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
                (discord_id,))
            await db.commit()
            db_logger.info(f"User with discord_id {discord_id} removed from {_VERIFIED_TABLE_NAME}")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while removing user with discord_id {discord_id}: {e}")
    except Exception as e:
        db_logger.error(f"Unexpected error: {e}")

async def remove_team(team_id: int) -> None:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            await db.execute(
                f'DELETE FROM {_TEAM_TABLE_NAME} WHERE team_id = ?',
                (team_id,))
            await db.commit()
            db_logger.info(f"Team with team_id {team_id} removed from {_TEAM_TABLE_NAME}")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while removing team with team_id {team_id}: {e}")
    except Exception as e:
        db_logger.error(f"Unexpected error: {e}")

# ------------ Retrieve Individual Entry ------------------------------------------------------------------------ DONE
async def get_registered_user_by_id(registrant_id: int) -> Optional[Dict[str, Any]]:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT * FROM {_REG_TABLE_NAME} WHERE registrant_id = ?',
                (registrant_id,)
            )
            return dict(row) if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error in {_DATABASE_FILE} while fetching registered user with registrant_id {registrant_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error in {_DATABASE_FILE} while fetching registered user with registrant_id {registrant_id}: {e}")
        return None

async def get_registered_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT * FROM {_REG_TABLE_NAME} WHERE email = ?',
                (email,)
            )
            return dict(row) if row else None
    except sqlite3.Error as e:
            db_logger.error(f"Database error while fetching registered user with email {email}: {e}")
            return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching registered user with email {email}: {e}")
        return None

async def get_email_by_registrant_id(registrant_id: int) -> Optional[str]:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT email FROM {_REG_TABLE_NAME} WHERE registrant_id = ?',
                (registrant_id,)
            )
            return row['email'] if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching email by registrant_id {registrant_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching email by registrant_id {registrant_id}: {e}")
        return None

async def get_verified_user(discord_id: int) -> Optional[Dict[str, Any]]:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT * FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
                (discord_id,)
            )
            return dict(row) if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching registered user with discord_id {discord_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching registered user with discord_id {discord_id}: {e}")
        return None


async def get_team(team_id: int) -> Optional[Dict[str, Any]]:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT * FROM {_TEAM_TABLE_NAME} WHERE team_id = ?',
                (team_id,)
            )
            return dict(row) if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching team with team_id {team_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching team with team_id {team_id}: {e}")
        return None


# -------------- Check if entry exists ----------------------------------------------------------------------- DONE

async def registered_user_exists(email: str) -> bool:
    """ Check if a user is registered by email."""
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT 1 FROM {_REG_TABLE_NAME} WHERE email = ?',
                (email,)
            )
            return row is not None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while checking if registered user exists with email {email}: {e}")
        return False
    except Exception as e:
        db_logger.error(f"Unexpected error while checking if registered user exists with email {email}: {e}")
        return False

async def verified_user_exists(discord_id: int) -> bool:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT 1 FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
                (discord_id,)
            )
            return row is not None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while checking if verified user exists with discord_id {discord_id}: {e}")
        return False
    except Exception as e:
        db_logger.error(f"Unexpected error while checking if verified user exists with discord_id {discord_id}: {e}")
        return False

async def team_exists(team_id: int) -> bool:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT 1 FROM {_TEAM_TABLE_NAME} WHERE team_id = ?',
                (team_id,)
            )
            return row is not None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while checking if team exists with team_id {team_id}: {e}")
        return False
    except Exception as e:
        db_logger.error(f"Unexpected error while checking if team exists with team_id {team_id}: {e}")
        return False

# ------- Registered User Methods ----------------------------------------------------------------------------

async def get_roles(email: str) -> list:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            async with db.execute(
                f'select is_participant, is_judge, is_mentor FROM {_REG_TABLE_NAME} WHERE email = ?',
                (email,)
            ) as cursor:
                row = await cursor.fetchone()
                roles = []
                if row[0]: roles.append('participant')
                if row[1]: roles.append('judge')
                if row[2]: roles.append('mentor')
                return roles
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching roles for user with email {email}: {e}")
        return []
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching roles for user with email {email}: {e}")
        return []
    
async def reassign_roles(email: str, roles: list) -> None:
    try:
        is_participant = 'participant' in roles
        is_judge = 'judge' in roles
        is_mentor = 'mentor' in roles

        async with asqlite.connect(_DATABASE_FILE) as db:
            await db.execute(
                f'UPDATE {_REG_TABLE_NAME} SET is_participant = ?, is_judge = ?, is_mentor = ? WHERE email = ?',
                (is_participant, is_judge, is_mentor, email)
            )
            await db.commit()
            db_logger.info(f"Roles for user with email {email} updated to {roles}")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while updating roles for user with email {email}: {e}")
    except Exception as e:
        db_logger.error(f"Unexpected error while updating roles for user with email {email}: {e}")
        
async def get_first_name(email: str) -> str:
    first_name = await get_registered_user_by_email(email)['first_name']
    if not first_name:
        # Empty strings and None have a truth value of False.
        return "Hackathon Registrant"
    else:
        return first_name

async def update_reg_discord_id(registrant_id:int, discord_id:int) -> None:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            await db.execute(
                f'UPDATE {_REG_TABLE_NAME} SET discord_id = ? WHERE registrant_id = ?',
                (discord_id, registrant_id)
            )
            await db.commit()
            db_logger.info(f"Discord ID for user with registrant_id {registrant_id} updated to {discord_id}")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while updating discord_id for user with registrant_id {registrant_id}: {e}")
    except Exception as e:
        db_logger.error(f"Unexpected error while updating discord_id for user with registrant_id {registrant_id}: {e}")

async def get_user_email(discord_id: int) -> str:
    try:
        query = """
        SELECT r.email
        FROM REGISTRANT r
        JOIN VERIFIED v ON r.registrant_id = v.registrant_id
        WHERE v.discord_id = ?;
        """
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(query, (discord_id,))
        if row:
            return row[0]
        else:
            db_logger.warning(f"No email found for registrant with discord_id {discord_id}")
            return None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching email for registrant with discord_id {discord_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching email for registrant with discord_id {discord_id}: {e}")
        return None

# ------- Verified User Methods ----------------------------------------------------------------------------


async def get_verified_discord_id(email: str) -> int:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f"SELECT discord_id FROM {_VERIFIED_TABLE_NAME} WHERE email = ?",
                (email,)
            )
        if row:
            return row[0]
        else:
            db_logger.warning(f"No discord_id found for registrant with email {email}")
            return None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching discord_id for email {email}: {e}")
        return None
    except Exception as e:  
        db_logger.error(f"Unexpected error while fetching discord_id for email {email}: {e}")
        return None

async def get_verified_email(discord_id: int) -> str:
    try:
        query = f"""
        SELECT r.email
        FROM {_REG_TABLE_NAME} r
        JOIN {_VERIFIED_TABLE_NAME} v ON r.registrant_id = v.registrant_id
        WHERE v.discord_id = ?;
    """
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(query, (discord_id,))
        if row:
            return row[0]
        else:
            db_logger.warning(f"No email found for verified user with discord_id {discord_id}")
            return None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching email for verified user with discord_id {discord_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching email for verified user with discord_id {discord_id}: {e}")
        return None

async def verified_email_exists(email: str) -> bool:
    try:
        query = f"""
        SELECT 1
        FROM {_REG_TABLE_NAME} r
        JOIN {_VERIFIED_TABLE_NAME} v ON r.registrant_id = v.registrant_id
        WHERE r.email = ?;
        """
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(query, (email,))
        return row is not None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while checking if email {email} exists in verified users: {e}")
        return False
    except Exception as e:
        db_logger.error(f"Unexpected error while checking if email {email} exists in verified users: {e}")
        return False    

async def user_is_participant(user_id: int) -> bool:
    email = await get_verified_email(user_id)
    if not email:
        return False
    roles = await get_roles(email)
    return 'participant' in roles


# ----------- Team Methods ---------------------------------------------------------------------------- 

async def remove_from_team(discord_id: int):
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            # Set the team_id to NULL for the user
            await db.execute(
                f'UPDATE {_VERIFIED_TABLE_NAME} SET team_id = NULL WHERE discord_id = ?',
                (discord_id,)
            )
            await db.commit()
            db_logger.info(f"User with discord_id {discord_id} has been removed from their team.")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while dropping team for user with discord_id {discord_id}: {e}")
    except Exception as e:  
        db_logger.error(f"Unexpected error while dropping team for user with discord_id {discord_id}: {e}")

async def add_to_team(team_id: int, discord_id: int):
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            # Check if the team exists
            if not await team_exists(team_id):
                db_logger.error(f"Team with team_id {team_id} does not exist.")
                return
            
            # Update the user's team_id in the VERIFIED table
            await db.execute(
                f'UPDATE {_VERIFIED_TABLE_NAME} SET team_id = ? WHERE discord_id = ?',
                (team_id, discord_id)
            )
            await db.commit()
            db_logger.info(f"User with discord_id {discord_id} has joined team {team_id}.")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while joining team {team_id} for user with discord_id {discord_id}: {e}")
    except Exception as e:
        db_logger.error(f"Unexpected error while joining team {team_id} for user with discord_id {discord_id}: {e}")

async def get_team_size(team_id: int) -> int:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            count = await db.fetchone(
                f'SELECT COUNT(*) FROM {_VERIFIED_TABLE_NAME} WHERE team_id = ?',
                (team_id,)
            )
            return count[0] if count else 0
    except sqlite3.Error as e:
        db_logger.error(f"Database error while getting team size for team_id {team_id}: {e}")
        return 0
    except Exception as e:
        db_logger.error(f"Unexpected error while getting team size for team_id {team_id}: {e}")
        return 0

async def get_number_of_teams() -> int:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            count = await db.fetchone(
                f'SELECT COUNT(*) FROM {_TEAM_TABLE_NAME}'
            )
            return count[0] if count else 0
    except sqlite3.Error as e:
        db_logger.error(f"Database error while getting number of teams: {e}")
        return 0
    except Exception as e:
        db_logger.error(f"Unexpected error while getting number of teams: {e}")
        return 0

async def get_max_team_id() -> int:
    async with asqlite.connect(_DATABASE_FILE) as db:
        # Get the maximum team_id from the TEAMS table
        row = await db.fetchone(f'SELECT MAX(team_id) FROM {_TEAM_TABLE_NAME}')
        # Fetch the result and return it, defaulting to 0 if no teams exist
        max_id = row[0]
        return max_id if max_id is not None else 0

async def is_member_on_team(discord_id: int) -> bool:
    """ Check if a user is on a team by looking for their discord_id in the VERIFIED table."""
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            # Check if the user is on a team by looking for their discord_id in the VERIFIED table
            user_team_id = await db.fetchone(f"SELECT team_id FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?", (discord_id,))
            return user_team_id is not None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while checking if user with discord_id {discord_id} is on a team: {e}")
        return False
    except Exception as e:
        db_logger.error(f"Unexpected error while checking if user with discord_id {discord_id} is on a team: {e}")
        return False

async def get_user_team_id(discord_id: int) -> int:
    """ Get the team_id for a user by looking for their discord_id in the VERIFIED table."""
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT team_id FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
                (discord_id,)
            )
            return row[0] if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching team_id for user with discord_id {discord_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching team_id for user with discord_id {discord_id}: {e}")
        return None

async def get_team_id(team_name: str) -> Optional[int]:
    """ Get the team_id for a given team_name."""
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT team_id FROM {_TEAM_TABLE_NAME} WHERE name = ?',
                (team_name,)
            )
            return row[0] if row else -1  # Return -1 if the team does not exist
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching team_id for team_name {team_name}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching team_id for team_name {team_name}: {e}")
        return None

async def get_team_members(team_id: int) -> list[int]:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            members = await db.fetchall(f'SELECT discord_id FROM {_VERIFIED_TABLE_NAME} WHERE team_id = ?', (team_id,))
            return [member['discord_id'] for member in members]  # Return a list of discord_ids
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching members for team_id {team_id}: {e}")
        return []
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching members for team_id {team_id}: {e}")
        return []
    
async def team_name_exists(team_name: int) -> bool:
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT 1 FROM {_TEAM_TABLE_NAME} WHERE name = ?',
                (team_name,)
            )
            return row is not None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while checking if team name {team_name} exists: {e}")
        return False
    except Exception as e:
        db_logger.error(f"Unexpected error while checking if team name {team_name} exists: {e}")
        return False

async def update_channels(team_id: int, channels: dict):
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            await db.execute(f"UPDATE {_TEAM_TABLE_NAME} SET category_id = ?, text_id = ?, voice_id = ?, role_id = ? WHERE team_id = ?",
                             (channels.get('category_id'), channels.get('text_id'), channels.get('voice_id'), channels.get('role_id'), team_id))
            await db.commit()
            db_logger.info(f"Channels for team_id {team_id} updated to {channels}")
    except sqlite3.Error as e:
        db_logger.error(f"Database error while updating channels for team_id {team_id}: {e}")
    except Exception as e:
        db_logger.error(f"Unexpected error while updating channels for team_id {team_id}: {e}")

async def get_team_role_id(team_id: int) -> Optional[int]:
    """ Get the role_id for a given team_id."""
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT role_id FROM {_TEAM_TABLE_NAME} WHERE team_id = ?',
                (team_id,)
            )
            return row[0] if row else -1  # Return -1 if the team does not exist
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching role_id for team_id {team_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching role_id for team_id {team_id}: {e}")
        return None

async def get_team_text_id(team_id:int) -> Optional[int]:
    """ Get the text channel ID for a given team_id."""
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT text_id FROM {_TEAM_TABLE_NAME} WHERE team_id = ?',
                (team_id,)
            )
            return row[0] if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching text_id for team_id {team_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching text_id for team_id {team_id}: {e}")
        return None

async def get_team_voice_id(team_id: int) -> Optional[int]:
    """ Get the voice channel ID for a given team_id."""
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT voice_id FROM {_TEAM_TABLE_NAME} WHERE team_id = ?',
                (team_id,)
            )
            return row[0] if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching voice_id for team_id {team_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching voice_id for team_id {team_id}: {e}")
        return None

async def get_team_category_id(team_id: int) -> Optional[int]:
    """ Get the category channel ID for a given team_id."""
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f'SELECT category_id FROM {_TEAM_TABLE_NAME} WHERE team_id = ?',
                (team_id,)
            )
            return row[0] if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while fetching category_id for team_id {team_id}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error while fetching category_id for team_id {team_id}: {e}")
        return None

# ----------- Verification Code Methods ----------------------------------------------------------------------
async def code_exists(code: str) -> bool:
    """ Check if a verification code exists in the database."""
    if not code:
        return False
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(f"SELECT 1 FROM {_REG_TABLE_NAME} WHERE verification_code = ?", (code,))
            return row is not None
    except sqlite3.Error as e:
        db_logger.error(f"Database error while checking if code {code} exists: {e}")
        return False
    except Exception as e:
        db_logger.error(f"Unexpected error while checking if code {code} exists: {e}")
        return False
    
async def add_code(code: str, registrant_id: int, discord_id: int) -> bool:
    """
    Adds a verification code and its expiration time to a registrant's record.

    Args:
        registrant_id: The ID of the user to whom the code is being assigned.
        code: The unique verification code.

    Requires:
        - code must be UNIQUE.
        - registrant_id must exist in the REGISTRANT table.
        
    Returns:
        True if the code was added successfully, False otherwise.
    """
    try:
        expires_at = datetime.datetime.now(datetime.timezone.utc) + timedelta(minutes = 15)
        expires_at_str = expires_at.isoformat()  # Convert to ISO 8601 format

        async with asqlite.connect(_DATABASE_FILE) as db:
            await db.execute(
                f"""
                    UPDATE {_REG_TABLE_NAME}
                    SET verification_code = ?, code_expires_at = ?, discord_id = ?
                    WHERE registrant_id = ?
                """, 
                (code, expires_at_str, discord_id, registrant_id))
            await db.commit()
            db_logger.info(f"Code {code} added for registrant_id {registrant_id}, expiring at {expires_at_str}.")
            return True
    except sqlite3.Error as e:
        db_logger.error(f"Database error while adding code {code}: {e}")
        return False
    except Exception as e:
        db_logger.error(f"Unexpected error while adding code {code}: {e}")
        return False

async def get_registrant_from_code(code: str) -> Optional[int]:
    """ Retrieves the registrant_id associated with a given verification code."""
    if not code:
        return None
    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f"SELECT registrant_id FROM {_REG_TABLE_NAME} WHERE verification_code = ?", 
                (code,)
                )
            db_logger.info(f"Fetched registrant_id {row['registrant_id']} for code {code}.")
            return row['registrant_id'] if row else None
    except sqlite3.Error as e:
        db_logger.error(f"Database error in {_DATABASE_FILE} while fetching registrant_id for code {code}: {e}")
        return None
    except Exception as e:
        db_logger.error(f"Unexpected error in {_DATABASE_FILE} while fetching registrant_id for code {code}: {e}")
        return None

async def verify_code(code: str, discord_id: int) -> (bool, Optional[int]):
    """ Verifies a given code for a registrant using discord ID. """
    if not code:
        return (False, None)

    try:
        async with asqlite.connect(_DATABASE_FILE) as db:
            row = await db.fetchone(
                f"""
                SELECT 1
                FROM {_REG_TABLE_NAME}
                WHERE verification_code = ? AND discord_id = ? AND code_expires_at > datetime('now')
                """, 
                (code, discord_id)
            )
            if row:
                registrant_id = await get_registrant_from_code(code)
                # Code is valid, update the registrant's verified status
                await db.execute(
                    f"""
                    UPDATE {_REG_TABLE_NAME}
                    SET verified_at = ?, verification_code = NULL, code_expires_at = NULL
                    WHERE discord_id = ?
                    """, 
                    (datetime.datetime.now(datetime.timezone.utc).isoformat(), discord_id)
                )
                await db.commit()
                db_logger.info(f"Code {code} verified for discord_id {discord_id}.")
                return (True, registrant_id)
            else:
                db_logger.warning(f"Code {code} is invalid or expired for discord_id {discord_id}.")
                return (False, None)
    except sqlite3.Error as e:
        db_logger.error(f"Database error in {_DATABASE_FILE} while verifying code {code} for discord_id {discord_id}: {e}")
        return (False, None)
    except Exception as e:
        db_logger.error(f"Unexpected error in {_DATABASE_FILE} while verifying code {code} for discord_id {discord_id}: {e}")
        return (False, None)

# ----------- Connect to Database ----------------------------------------------------------------------------

async def main():
    # Check if the database file exists
    _db_file_exists = os.path.isfile(_DATABASE_FILE)

    # Connect to the database, creating it if it does not exist
    async with asqlite.connect(_DATABASE_FILE, isolation_level=None) as db:
        # Initialize tables if the database is new
        if not _db_file_exists:
            await _initialize_db()


