import sys
import os
import csv
import logging
import ConfigParser

from assembla.api import API
from assembla.error import AssemblaError

from actions import migrate_tickets

logger = logging.getLogger('ATMT')
logger.setLevel(logging.DEBUG)

FORMAT = "%(asctime)-15s %(message)s"
formatter = logging.Formatter(FORMAT)
file_handler = logging.FileHandler('ATMT.log')
stream_handler = logging.StreamHandler()
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

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
if client_id in ["None", None]:
    print "Create a client here: https://www.assembla.com/user/edit/manage_clients"
    client_id = raw_input("Please type enter your Client ID: ")
client_secret = config.get('ApplicationTokens', 'client_secret')
if client_secret in ["None", None]:
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

renumber=False
assign_new_numbers = raw_input('Re-number copied tickets (if destination is not empty)? [y/N] ')
if assign_new_numbers == "y":
    renumber=True

print "************************************************************"
print "*              About to start ticket migration             *"
print "*                                                          *"
print "*    if you'd like to delete instead, skip this step.      *"
print "*                                                          *"
print "*                type 'copy' to copy                       *"
print "************************************************************"
copy = raw_input("Okay to start copy process? [copy/N] ")

spaces=api.get_spaces()
sp1 = sp2 = None
for space in spaces:
    if space.name == space1:
        sp1 = space
    if space.name == space2:
        sp2 = space
if not sp1 or not sp2:
    logger.debug('[Application] Could not find spaces, exiting.')
    sys.exit()

if copy == 'copy':
    logger.debug('[Application] Starting Copy Process')
    nmap = migrate_tickets(sp1, sp2, ticket_numbers=ticketlist, auth=auth,
            renumber=renumber)
    with open('ticket_map.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for n in nmap:
            writer.writerow([n, nmap[n]])
    print "************************************************************"
    print "* For your convenience a file mapping new ticket numbers   *"
    print "* has been placed in the current directory called:         *"
    print "*                                                          *"
    print "*                ticket_map.csv                            *"
    print "************************************************************"
    logger.debug('[Application] Finished Copy Process')

print "************************************************************"
print "*   WARNING!! It is not possible to recover from deletion  *"
print "*             Re-run tool after checking migration         *"
print "*             type 'delete' to delete tickets              *"
print "************************************************************"
delete = raw_input("Okay to delete tickets RIGHT NOW? [delete/N] ")

if delete == 'delete':
    logger.debug('[Application] Starting Ticket Deletion')
    for t in ticketlist:
        t = sp1.get_ticket(number=t)
        t.destroy()
        logger.debug('[Application] Deleted ticket %s from %s', t.number, sp1.name)
    logger.debug('[Application] Finished Ticket Deletion') 
