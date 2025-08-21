
import unittest
import asyncio
import os
from unittest.mock import MagicMock, patch

# Set the database to a test database before importing records
os.environ['DATABASE_FILE'] = 'test_records.db'

from core.bot import OHIOBot
from core.records import (
    _initialize_db,
    add_registered_user,
    get_registered_user_by_email,
    remove_registered_user,
)

class TestBotRecords(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        # Initialize a clean database for each test
        self.loop.run_until_complete(_initialize_db())

    def tearDown(self):
        # Clean up the test database file after each test
        if os.path.exists('test_records.db'):
            os.remove('test_records.db')

    def test_add_and_get_registered_user(self):
        email = "test@example.com"
        roles = ["participant"]
        data = {
            "first_name": "Test",
            "last_name": "User",
            "university": "Test University",
            "class_team": 1,
            "major": "Computer Science",
            "grad_year": 2025,
        }

        # Add a user
        self.loop.run_until_complete(add_registered_user(email, roles, data))

        # Retrieve the user
        user = self.loop.run_until_complete(get_registered_user_by_email(email))

        self.assertIsNotNone(user)
        self.assertEqual(user['email'], email)
        self.assertEqual(user['first_name'], "Test")

        # Clean up
        self.loop.run_until_complete(remove_registered_user(email))

    @patch('discord.ext.commands.Bot.run')
    @patch('core.bot.OHIOBot.load_extension')
    def test_bot_initialization(self, mock_load_extension, mock_run):
        # This test checks if the bot can be initialized without errors.
        # We patch the run and load_extension methods to avoid actually running the bot
        # or loading cogs, which might have other dependencies.
        bot = OHIOBot(command_prefix='!', intents=MagicMock())
        self.assertIsInstance(bot, OHIOBot)

if __name__ == '__main__':
    unittest.main()
