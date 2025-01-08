import records
import config
import bot

from flask import Flask, abort, request, jsonify
from eventlet import wsgi
import eventlet



'''
The purpose of this file is to stay active and listen for any incoming post requests from 
the Qualtrics Workflow that should send the bot a request to update the userDB anytime someone 
registers for the event. This will keep the db up-to-date with new registrations

Format for Post Requests JSON
{
    header: {
        'API_KEY': str
    }
    body: {
        'email': str,
        'roles': (role,role), (comma-separated)
        
        'data-header':'data-contents' (Every other pair is considered data)
        ...
    }
}
"""
'''

#Define the server as app
app = Flask(__name__)

#Setup a method to listen at "/post/user" for a post request
@app.route("/post/user", methods=['POST'])
def push_user():
    #Check that API key is correct
    if (request.headers.get('API_KEY') == config.web_api_key):
        
        #Retrieve Data from Request
        data = request.get_json()

        email = data['email']
        roles = data['roles']
        data = data['data']


        #Append Data to Database 
        try:
            #Add User to registrant list
            records.add_registered_user(str(data['email']).lower(), data['discord_username'], data['roles'])

            #Send back "Good" Message
            return jsonify({'email': str(data['email']).lower(), 'discord_username': data['discord_username'], 'role': data['role']})
        except:
            #Send Error that user being added has failed
            print("ERROR: Not all data in the request was included or error with DB file")
            abort(400)
    else:
        #Send Error that API_KEY is not correct
        print("ERROR: API_KEY is not correct.")
        abort(403)

#Method to start a server and wait for a request
def start():
    wsgi.server(eventlet.listen(('0.0.0.0', config.web_port)), app)


