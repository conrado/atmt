
import os
import ConfigParser

from assembla.api import API
from assembla.error import AssemblaError

from actions import migrate_space_tickets

def init_client(client):
    print ("Follow this url: {0}".format(client.getAuthorizeUrl()))
    pin = raw_input("Enter your pin: ")
    client.initClient(pin)
    return client

filename = os.path.join(os.environ['HOME'], '.atmt')

config = ConfigParser.RawConfigParser({
            'client_id':None,
            'client_secret':None,
            'bearer_token':None,
            'refresh_token':None
})

config.add_section('ApplicationTokens')
config.add_section('ClientTokens')

config.read(filename)

client_id = config.get('ApplicationTokens', 'client_id')
if client_id == "None":
    client_id = raw_input("Please type enter your Client ID: ")
client_secret = config.get('ApplicationTokens', 'client_secret')
if client_secret == "None":
    client_secret = raw_input("Please type enter your Client Secret: ")

print "We require an Assembla account info to download documents"
username = raw_input("Please enter your Assembla.com username: ")
password = raw_input("and password: ")
auth = (username, password)

space1 = raw_input("Please enter the name of the space to copy tickets from: ")
space2 = raw_input("Please enter the name of the space to copy tickets to: ")

tickets = raw_input("Please enter full path to ticket list: ")

api = API(client_id, client_secret)

refresh_token = config.get('ClientTokens', 'refresh_token')
bearer_token = config.get('ClientTokens', 'bearer_token')
if bearer_token != "None":
    try:
        api.initTokens(bearer_token, refresh_token)
        api.me()
    except AssemblaError:
        print "Token has expired, please re-enter pincode..."
        api = init_client(api)
        bearer_token = api.client.access_token
        refresh_token = api.client.refresh_token
else:
    api = init_client(api)
    bearer_token = api.client.service.access_token

with open(filename, 'wb') as configfile:
    config.set('ApplicationTokens', 'client_id', client_id)
    config.set('ApplicationTokens', 'client_secret', client_secret)
    config.set('ClientTokens', 'bearer_token', bearer_token)
    config.set('ClientTokens', 'refresh_token', refresh_token)
    config.write(configfile)

ticketlist = []
with open(tickets, 'r') as ticketfile:
    lines = ticketfile.readlines()
    for l in lines:
        if l:
            ticketlist.append(int(l))


spaces=api.get_spaces()
sp1 = sp2 = None
for space in spaces:
    if space.name == space1:
        sp1 = space
    if space.name == space2:
        sp2 = space
if not sp1 or not sp2:
    print "Could not find spaces, exiting."
else:
    migrate_space_tickets(sp1, sp2, ticket_numbers=ticketlist, auth=auth)

print "Migration done!"
delete = raw_input("Okay to delete tickets? [y/N] ")
if delete == 'y':
    for t in ticketlist:
        t = sp1.get_ticket(number=t)
        t.destroy()
    print "Deleting done!"
