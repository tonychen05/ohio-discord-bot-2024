Instructions on setting up on your machine:
1. create virtual environment using: 
  python -m venv venv
  source venv/bin/activate 
2. update .env file
  - The .env file is a sensitive document; Slack DM Dylan Jian for access
3. inside your virtual environment (should say (venv) at the beginning of your terminal line), run:
  pip install python-dotenv
  pip install discord.py
4. Finally, to log into the discord bot, run:
  python bot.py
  - After running that, it should say "discord.client logging in using static token", and then after a few seconds, "discord.gateway Shard ID None has connected to Gateway (Session ID: ..."
