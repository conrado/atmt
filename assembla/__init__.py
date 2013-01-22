"""
Assembla API library
"""
__version__ = '0.1'
__author__ = 'Conrado Buhrer'
__license__ = 'Apache v2'

from assembla.models import Space, User, Ticket, ModelFactory
from assembla.error import AssemblaError
from assembla.api import API
from assembla.cursor import Cursor

def debug(enable=True, level=1):

    import httplib
    httplib.HTTPConnection.debuglevel = level

