import bot

TEAM_DATABASE = 'team.sqlite'
USER_DATABASE = 'user.sqlite'

userDB = bot.connect_to_team_db(USER_DATABASE)

'''
The purpose of this file is to stay active and listen for any incoming post requests from 
the Qualtrics Workflow that should send the bot a request to update the userDB anytime someone 
registers for the event. This will keep the db up-to-date
'''

def registerUser():
    userDB.execute('INSERT INTO users (name) VALUES (?)', )
    userDB.commit()

