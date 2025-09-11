"""
Unit tests for the database functions in core/records.py.
"""
import unittest
import asyncio
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import records

class TestRecords(unittest.TestCase):
    """
    Test suite for the records module.
    """

    def setUp(self):
        """
        Set up a clean database for each test.
        """
        self.db_file = 'test_records.db'
        records._DATABASE_FILE = self.db_file
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        
        async def init_db():
            async with records.asqlite.connect(self.db_file) as db:
                await records._create_tables(db)
        
        asyncio.run(init_db())

    def tearDown(self):
        """
        Clean up the database file after each test.
        """
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_add_and_get_registered_user(self):
        """
        Test adding and retrieving a registered user.
        """
        email = "test@example.com"
        roles = ["participant"]
        data = {
            "first_name": "Test",
            "last_name": "User"
        }

        # Add a user
        user_id = asyncio.run(records.add_registered_user(email, roles, data))
        self.assertIsNotNone(user_id)

        # Get the user and assert it's correct
        user = asyncio.run(records.get_registered_user_by_email(email))
        self.assertIsNotNone(user)
        self.assertEqual(user['registrant_id'], user_id)
        self.assertEqual(user['email'], email)
        self.assertEqual(user['first_name'], "Test")

    def test_create_and_get_team(self):
        """
        Test creating and retrieving a team.
        """
        team_name = "Test Team"
        channels = {
            "category_id": 123,
            "text_id": 456,
            "voice_id": 789,
            "role_id": 101
        }

        # Create a team
        team_id = asyncio.run(records.create_team(team_name, channels))
        self.assertIsNotNone(team_id)

        # Get the team and assert it's correct
        team = asyncio.run(records.get_team(team_id))
        self.assertIsNotNone(team)
        self.assertEqual(team['name'], team_name)
        self.assertEqual(team['category_id'], 123)

    def test_user_verification_flow(self):
        """
        Test the full user verification flow.
        """
        email = "verify@example.com"
        roles = ["participant"]
        data = {"first_name": "Verify", "last_name": "User"}
        discord_id = 1234567890
        username = "verify_user"
        verification_code = "123456"

        # 1. Add a registered user
        registrant_id = asyncio.run(records.add_registered_user(email, roles, data))
        self.assertIsNotNone(registrant_id)

        # 2. Add a verification code for that user
        add_code_success = asyncio.run(records.add_code(verification_code, registrant_id, discord_id))
        self.assertTrue(add_code_success)

        # 3. Verify the code
        verify_success = asyncio.run(records.verify_code(verification_code, discord_id))
        self.assertTrue(verify_success)

        # 4. Add the user to the VERIFIED table
        asyncio.run(records.add_verified_user(registrant_id, discord_id, username))

        # 5. Check if the user is now verified
        is_verified = asyncio.run(records.verified_user_exists(discord_id))
        self.assertTrue(is_verified)

    def test_verify_with_incorrect_code(self):
        """
        Test that verification fails with an incorrect code.
        """
        email = "incorrect@example.com"
        roles = ["participant"]
        data = {"first_name": "Incorrect", "last_name": "Code"}
        discord_id = 9876543210
        correct_code = "123456"
        incorrect_code = "654321"

        # 1. Add a registered user
        registrant_id = asyncio.run(records.add_registered_user(email, roles, data))
        self.assertIsNotNone(registrant_id)

        # 2. Add a verification code for that user
        add_code_success = asyncio.run(records.add_code(correct_code, registrant_id, discord_id))
        self.assertTrue(add_code_success)

        # 3. Attempt to verify with the incorrect code
        verify_success = asyncio.run(records.verify_code(incorrect_code, discord_id))
        self.assertFalse(verify_success)

    def test_registrant_id_auto_increment(self):
        """
        Test that the registrant_id auto-increments correctly.
        """
        # Add first user
        email1 = "test1@example.com"
        roles1 = ["participant"]
        data1 = {"first_name": "Test", "last_name": "User1"}
        user_id1 = asyncio.run(records.add_registered_user(email1, roles1, data1))
        self.assertEqual(user_id1, 1)

        # Add second user
        email2 = "test2@example.com"
        roles2 = ["participant"]
        data2 = {"first_name": "Test", "last_name": "User2"}
        user_id2 = asyncio.run(records.add_registered_user(email2, roles2, data2))
        self.assertEqual(user_id2, 2)

        # Add third user
        email3 = "test3@example.com"
        roles3 = ["participant"]
        data3 = {"first_name": "Test", "last_name": "User3"}
        user_id3 = asyncio.run(records.add_registered_user(email3, roles3, data3))
        self.assertEqual(user_id3, 3)

    def test_team_id_auto_increment_and_deletion(self):
        """
        Test that the team_id auto-increments correctly and is not reused after deletion.
        """
        channels = {"category_id": 123, "text_id": 456, "voice_id": 789, "role_id": 101}

        # Create three teams
        team_id1 = asyncio.run(records.create_team("Team 1", channels))
        self.assertEqual(team_id1, 1)

        team_id2 = asyncio.run(records.create_team("Team 2", channels))
        self.assertEqual(team_id2, 2)

        team_id3 = asyncio.run(records.create_team("Team 3", channels))
        self.assertEqual(team_id3, 3)

        team_id = asyncio.run(records.get_team_id("Team 3"))
        self.assertEqual(team_id, team_id3)

        # Delete team 2
        asyncio.run(records.remove_team(team_id2))
        self.assertIsNone(asyncio.run(records.get_team(team_id2)))

        # Create a new team
        team_id4 = asyncio.run(records.create_team("Team 4", channels))
        self.assertEqual(team_id4, 4)

        # Check that team_id2 is not reused
        team_id5 = asyncio.run(records.create_team("Team 5", channels))
        self.assertEqual(team_id5, 5)

    def test_team_member_addition_and_removal(self):
        """
        Test adding and removing team members.
        """
        channels = {"category_id": 123, "text_id": 456, "voice_id": 789, "role_id": 101}
        team_id = asyncio.run(records.create_team("Member Test Team", channels))
        self.assertIsNotNone(team_id)

        discord_id1 = 111111
        discord_id2 = 222222

        # Define user data
        email1 = "member1@example.com"
        roles1 = ["participant"]
        data1 = {"first_name": "Member", "last_name": "One"}
        email2 = "member2@example.com"
        roles2 = ["participant"]
        data2 = {"first_name": "Member", "last_name": "Two"}

        # Add registered users
        reg1 = asyncio.run(records.add_registered_user(email1, roles1, data1))
        reg2 = asyncio.run(records.add_registered_user(email2, roles2, data2))

        # Add verified users
        asyncio.run(records.update_reg_discord_id(reg1, discord_id1))
        asyncio.run(records.update_reg_discord_id(reg2, discord_id2))
        asyncio.run(records.add_verified_user(reg1, discord_id1, "User1"))
        asyncio.run(records.add_verified_user(reg2, discord_id2, "User2"))

        # Add members to the team
        asyncio.run(records.add_to_team(team_id, discord_id1))
        asyncio.run(records.add_to_team(team_id, discord_id2))

        members = asyncio.run(records.get_team_members(team_id))
        self.assertIn(discord_id1, members)
        self.assertIn(discord_id2, members)

        # Remove one member
        asyncio.run(records.remove_from_team(discord_id1))
        members = asyncio.run(records.get_team_members(team_id))
        self.assertNotIn(discord_id1, members)
        self.assertIn(discord_id2, members)

if __name__ == '__main__':
    unittest.main()