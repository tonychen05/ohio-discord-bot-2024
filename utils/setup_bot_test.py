import os
import asyncio
import sys
from datetime import datetime, timedelta
from core import records

def main():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    # Set up a clean database for each test.
    db_file = 'test_records.db'
    records._DATABASE_FILE = db_file
    if os.path.exists(db_file):
        os.remove(db_file)

    async def init_db():
        async with records.asqlite.connect(db_file) as db:
            await records._create_tables(db)

    asyncio.run(init_db())

    # Add mock data in all tables
    async def add_mock_data():
        async with records.asqlite.connect(db_file) as db:
            # Insert multiple mock registered users
            user1_id = await records.add_registered_user(
                email='me@example.com',
                roles=['participant'],
                data={'first_name': 'Test', 'last_name': 'User'}
            )
            user2_id = await records.add_registered_user(
                email='alice@example.com',
                roles=['judge'],
                data={'first_name': 'Alice', 'last_name': 'Smith'}
            )
            user3_id = await records.add_registered_user(
                email='bob@example.com',
                roles=['mentor'],
                data={'first_name': 'Bob', 'last_name': 'Brown'}
            )

            await records.update_reg_discord_id(user1_id, 282547899508850689)
            await records.update_reg_discord_id(user2_id, 987654321)
            await records.update_reg_discord_id(user3_id, 456789123 )
            # Insert mock verified users
            # await records.add_verified_user(user1_id, 282547899508850689, "me")
            await records.add_verified_user(user2_id, 987654321, "alice")
            await records.add_verified_user(user3_id, 456789123, "bob")

    asyncio.run(add_mock_data())

    # Add verification code and print verification code with expiration date in one year
    import secrets

    verification_code = 123456
    expiration_date = datetime.now() + timedelta(days=365)

    async def add_verification_code():
        async with records.asqlite.connect(db_file) as db:
            await records.add_code(verification_code, 1, discord_id=282547899508850689)
            await db.commit()

    asyncio.run(add_verification_code())

    print(f"Verification code: {verification_code}")
    print(f"Expires at: {expiration_date.isoformat()}")

if __name__ == "__main__":
    main()