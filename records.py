import sqlite3
import os
import json
"""
Goals

Make a class that connects to the DB and has an interface for methods like
add_registered_user
create_team
remove_team
leave_team
getUser

"""
_DATABASE_FILE = 'records.db'

"""
Participant Scheme {
    EMAIL: TEXT*,
    DATA: TEXT (JSON parsed){
        FIRST_NAME: TEXT,
        LAST_NAME: TEXT,
        UNIVERSITY: TEXT,
        MAJOR: TEXT,
        GRAD_YEAR: INTEGER,
        ... (other fields)
        header_name: contents
    }
    ROLES: TEXT (Array parsed)
}

Verified Scheme {
    DISCORD_ID: INTEGER* PRIMARY KEY,
    EMAIL: TEXT*,
    TEAM_ID: INTEGER REFERENCES {_TEAM_TABLE_NAME}(id)
}

- Channels is a JSON object that can have a variable number of channels, 
  Channel Keys are (TEXT, VOICE, CATEGORY*)

Team Scheme {
    ID: INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME: TEXT UNIQUE,
    CHANNELS: TEXT* (JSON parsed) {
        CATEGORY: INTEGER*,
        TEXT: INTEGER,
        VOICE: INTEGER
    }
}
"""

_REG_RESPONSES_TABLE_NAME = 'registration'
_VERIFIED_TABLE_NAME = 'verified'
_TEAM_TABLE_NAME = 'teams'


def _initialize_db(cursor: sqlite3.Cursor):

    # Registration form responses
    cursor.execute(
        f"""CREATE TABLE {_REG_RESPONSES_TABLE_NAME} ( 
            email TEXT NOT NULL, 
            roles TEXT NOT NULL, 
            data TEXT 
            )
        """)

    # Verified users
    cursor.execute(
        f"""CREATE TABLE {_VERIFIED_TABLE_NAME} ( 
            discord_id INTEGER PRIMARY KEY, 
            team_id REFERENCES {_TEAM_TABLE_NAME}(id), 
            email TEXT NOT NULL, 
            username TEXT NOT NULL
            )
        """)

    # Teams
    cursor.execute(
        f"""CREATE TABLE {_TEAM_TABLE_NAME} ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT UNIQUE NOT NULL, 
            channels TEXT
            )
        """)
    

# ---------- Register Data into Database ------------------------------------------------------------ DONE


def add_registered_user(email: str, roles: list, data: dict):
    roles = json.dumps(roles)
    data = json.dumps(data)
    cursor.execute(
        f'INSERT INTO {_REG_RESPONSES_TABLE_NAME} (email, roles, data) VALUES (?, ?, ?)',
        (email, roles, data)
    )

def add_verified_user(discord_id: int, email: str, username: str):
    cursor.execute(
        f'INSERT INTO {_VERIFIED_TABLE_NAME} (discord_id, email, username) VALUES (?, ?, ?)',
        (discord_id, email, username)
    )

def create_team(team_name: str):
    cursor.execute(
        f'INSERT INTO {_TEAM_TABLE_NAME} (name) VALUES (?)',
        (team_name,)
    )

# ------------ Remove Entries from Tables -------------------------------------------------------------------------- DONE

def remove_registered_user(email: str):
    cursor.execute(
        f'DELETE FROM {_REG_RESPONSES_TABLE_NAME} WHERE email = ?',
        (email,)
    )

def remove_verified_user(discord_id: int):
    cursor.execute(
        f'DELETE FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
        (discord_id,)
    )

def remove_team(team_id: int):
    cursor.execute(
        f'DELETE FROM {_TEAM_TABLE_NAME} WHERE id = ?',
        (team_id,)
    )

# ------------ Retrieve Individual Entry ------------------------------------------------------------------------ DONE

def get_registered_user(email: str) -> dict:
    cursor.execute(
        f'SELECT * FROM {_REG_RESPONSES_TABLE_NAME} WHERE email = ?',
        (email,)
    )
    data_tuple = cursor.fetchone()
    if data_tuple is None:
        return None

    # Convert data string to dictionary
    data = {
        'email': data_tuple[0],
        'roles': json.loads(data_tuple[1]),
        'data': json.loads(data_tuple[2])
    }

    return data

def get_verified_user(discord_id: int) -> dict:
    cursor.execute(
        f'SELECT * FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
        (discord_id,)
    )
    data_tuple = cursor.fetchone()
    if data_tuple is None:
        return None

    # Convert data string to dictionary
    data = {
        'discord_id': data_tuple[0],
        'team_id': data_tuple[1],
        'email': data_tuple[2],
        'username': data_tuple[3],
    }

    return data

def get_team(team_id: int) -> dict:
    cursor.execute(
        f'SELECT * FROM {_TEAM_TABLE_NAME} WHERE id = ?',
        (team_id,)
    )
    data_tuple = cursor.fetchone()
    if data_tuple is None:
        return None

    # Convert data string to dictionary
    data = {
        'id': data_tuple[0],
        'name': data_tuple[1],
        'channels': json.loads(data_tuple[2])
    }


    return data


# -------------- Check if entry exists ----------------------------------------------------------------------- DONE

def registered_user_exists(email: str) -> bool:
    cursor.execute(
        f'SELECT * FROM {_REG_RESPONSES_TABLE_NAME} WHERE email = ?',
        (email,)
    )
    return cursor.fetchone() is not None

def verified_user_exists(discord_id: int) -> bool:
    cursor.execute(
        f'SELECT * FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
        (discord_id,)
    )
    return cursor.fetchone() is not None

def team_exists(team_name: str) -> bool:
    cursor.execute(
        f'SELECT * FROM {_TEAM_TABLE_NAME} WHERE name = ?',
        (team_name,)
    )
    return cursor.fetchone() is not None

# ------- Registered User Methods ----------------------------------------------------------------------------

def get_first_name(email: str) -> str:
    userData = get_registered_user(email)
    return userData['data']['first_name']

# ------- Verified User Methods ----------------------------------------------------------------------------

def get_discord_id(email: str) -> int:
    return cursor.execute(
        f"SELECT discord_id FROM {_VERIFIED_TABLE_NAME} WHERE email=:email", {'email': email}).fetchone()[0]

def get_email(discord_id: int) -> str:
    return cursor.execute(
        f"SELECT email FROM {_VERIFIED_TABLE_NAME} WHERE discord_id=:discord_id", {'discord_id': discord_id}).fetchone()[0]
# ----------- Team Methods ---------------------------------------------------------------------------- 

def drop_team(discord_id: int):
    cursor.execute(
        f'UPDATE {_VERIFIED_TABLE_NAME} SET team_id=NULL WHERE discord_id=:discord_id', {
            'discord_id': discord_id})

def join_team(team_id: int, discord_id: int):
    cursor.execute(
        f'UPDATE {_VERIFIED_TABLE_NAME} SET team_id=:team_id WHERE discord_id=:discord_id', {
            'discord_id': discord_id, 'team_id': team_id})

def get_team_size(team_id: int) -> int:
    return cursor.execute(
        f'SELECT COUNT(*) FROM {_VERIFIED_TABLE_NAME} WHERE team_id=:team_id', {
            'team_id': team_id}).fetchone()[0]

def get_number_of_teams() -> int:
    return cursor.execute(f"SELECT COUNT(*) FROM {_TEAM_TABLE_NAME}").fetchone()[0]

def get_max_team_id() -> int:
    return cursor.execute(f'SELECT MAX(id) FROM {_TEAM_TABLE_NAME}').fetchone()[0]

def is_member_on_team(discord_id: int) -> bool:
    cursor.execute(f"SELECT team_id FROM {_VERIFIED_TABLE_NAME} WHERE discord_id=:discord_id", {'discord_id': discord_id})
    user_team_id = cursor.fetchone()[0]
    return user_team_id is not None

def get_user_team_id(discord_id: int) -> int:
    return cursor.execute(f"SELECT team_id FROM {_VERIFIED_TABLE_NAME} WHERE discord_id=:discord_id", 
                          {'discord_id': discord_id}).fetchone()[0]

def get_team_id(team_name: str) -> int:
    return cursor.execute(f"SELECT id FROM {_TEAM_TABLE_NAME} WHERE name=:team_name", {'team_name': team_name}).fetchone()[0]

# ----------- Connect to Database ----------------------------------------------------------------------------

# Check if db file exists
_db_file_exists = os.path.isfile(_DATABASE_FILE)

# Connecting creates the file if not there
_connection = sqlite3.connect(_DATABASE_FILE, isolation_level=None)
cursor = _connection.cursor()

# Initialize tables if database is new
if not _db_file_exists:
    _initialize_db(cursor)




