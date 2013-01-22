import os
import mimetypes

from assembla.binder import bind_api
from assembla.error import AssemblaError
from assembla.parsers import ModelParser
from assembla.utils import list_to_csv

from assembla.HttpClient import HttpClient


class API(object):
    """Assembla API"""

    def __init__(self, consumer_key, consumer_secret, pin=None,
            host='api.assembla.com', search_host=None,
            cache=None, secure=False, api_root='/v1/', search_root='',
            retry_count=0, retry_delay=0, retry_errors=None,
            parser=None):
        self.client = HttpClient(consumer_key, consumer_secret, pin)
        self.host = host
        self.search_host = search_host
        self.api_root = api_root
        self.search_root = search_root
        self.cache = cache
        self.secure = secure
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.retry_errors = retry_errors
        self.okay_status = [200, 201]
        self.parser = parser or ModelParser()

    def getAuthorizeUrl(self):
        return self.client.getAuthorizeUrl()

    def initClient(self, pin):
        self.client.initClient(pin)

    def initTokens(self, access_token, refresh_token):
        self.client.initTokens(access_token, refresh_token)

    """ Get the authenticated user """
    me = bind_api(
        path="user.json",
        payload_type="user"
    )

    """ Get the spaces current user has """
    get_spaces = bind_api(
        path="spaces.json",
        payload_type="space", payload_list = True
    )

    """ Get users belonging to a space """
    get_space_users = bind_api(
        path="users/{space}.json",
        payload_type="user", payload_list = True,
        allowed_param = ['space']
    )

    """ Get tickets belonging to a space """
    get_space_tickets = bind_api(
        path='spaces/{space}/tickets.json',
        payload_type="ticket", payload_list = True,
        allowed_params = ['space']
    )

    """ Get possible ticket statuses for a space """
    get_ticket_statuses = bind_api(
        path='spaces/{space}/tickets/statuses.json',
        method='GET',
        payload_type='ticketstatus', payload_list = True,
        allowed_params = ['space',]
    )

    """ Create ticket status in a space """
    def create_ticket_status(self, status, *args, **kargs):
        post_data=status.toJSON()
        kargs['post_data'] = post_data
        return bind_api(
            path='spaces/{space}/tickets/statuses.json',
            method='POST',
            payload_type='ticketstatus',
            allowed_params = ['space']
        )(self, *args, **kargs)

    """ Get possible ticket custom fields"""
    get_custom_fields = bind_api(
        path='spaces/{space}/tickets/custom_fields.json',
        method='GET',
        payload_type='ticketcustomfield', payload_list=True,
        allowed_params = ['space',]
    )

    """ Create ticket custom field """
    def create_custom_field(self, field, *args, **kargs):
        post_data=field.toJSON()
        kargs['post_data'] = post_data
        return bind_api(
            path='spaces/{space}/tickets/custom_fields.json',
            method='POST',
            payload_type='ticketcustomfield',
            allowed_params = ['space']
        )(self, *args, **kargs)

    """ Get ticket components """
    get_ticket_components = bind_api(
        path='spaces/{space}/ticket_components.json',
        method='GET',
        payload_type='ticketcomponent', payload_list=True,
        allowed_params = ['space',]
    )

    """ Create ticket component """
    def create_ticket_component(self, component, *args, **kargs):
        post_data=component.toJSON()
        kargs['post_data'] = post_data
        return bind_api(
            path='spaces/{space}/ticket_components.json',
            method='POST',
            payload_type='ticketcomponent',
            allowed_params = ['space']
        )(self, *args, **kargs)

    """ Get space milestones """
    get_milestones = bind_api(
        path='spaces/{space}/milestones.json',
        method='GET',
        payload_type='milestone', payload_list=True,
        allowed_params = ['space',]
    )

    """ Create milestone """
    def create_milestone(self, milestone, *args, **kargs):
        post_data=milestone.toJSON()
        kargs['post_data'] = post_data
        return bind_api(
            path='spaces/{space}/milestones.json',
            method='POST',
            payload_type='milestone',
            allowed_params = ['space']
        )(self, *args, **kargs)

    """ Get ticket associations """
    get_associations = bind_api(
        path='spaces/{space}/tickets/{ticket}/ticket_associations.json',
        method='GET',
        payload_type='ticketassociation', payload_list=True,
        allowed_params = ['space', 'ticket']
    )

    """ Create milestone """
    def create_association(self, association, *args, **kargs):
        post_data=association.toJSON()
        kargs['post_data'] = post_data
        return bind_api(
            path='spaces/{space}/tickets/{ticket}/ticket_associations.json',
            method='POST',
            payload_type='ticketassociation',
            allowed_params = ['space', 'ticket']
        )(self, *args, **kargs)

    """ Get tickets """
    get_tickets = bind_api(
        path='spaces/{space}/tickets.json',
        method='GET',
        payload_type='ticket', payload_list=True,
        allowed_params = ['space']
    )

    """ Get ticket """
    get_ticket = bind_api(
        path='spaces/{space}/tickets/{ticket}.json',
        method='GET',
        payload_type='ticket',
        allowed_params = ['space', 'ticket']
    )

    """ Get ticket by id """
    get_ticket_by_id = bind_api(
        path='spaces/{space}/tickets/id/{ticket}.json',
        method='GET',
        payload_type='ticket',
        allowed_params = ['space', 'ticket']
    )

    """ Create ticket in a space """
    def create_ticket(self, ticket, *args, **kargs):
        post_data=ticket.toJSON()
        kargs['post_data'] = post_data
        return bind_api(
            path='spaces/{space}/tickets.json',
            method='POST',
            payload_type='ticket',
            allowed_params = ['space',]
        )(self, *args, **kargs)

    """ Delete ticket """
    delete_ticket = bind_api(
        path='spaces/{space}/tickets/{ticket}.json',
        method='DELETE',
        allowed_params = ['space', 'ticket']
    )

    """ Get ticket comment """
    get_ticket_comment = bind_api(
        path='spaces/{space}/tickets/{ticket}/ticket_comments/{comment}.json',
        method='GET',
        payload_type='ticketcomment',
        allowed_params = ['space', 'ticket', 'comment']
    )

    """ Get ticket comments """
    get_ticket_comments = bind_api(
        path='spaces/{space}/tickets/{ticket}/ticket_comments.json',
        method='GET',
        payload_type='ticketcomment', payload_list=True,
        allowed_params = ['space', 'ticket']
    )

    """ Create ticket comment """
    def create_ticket_comment(self, comment, *args, **kargs):
        post_data=comment.toJSON()
        kargs['post_data'] = post_data
        return bind_api(
            path='spaces/{space}/tickets/{ticket}/ticket_comments.json',
            method='POST',
            payload_type='ticketcomment',
            allowed_params = ['space', 'ticket']
        )(self, *args, **kargs)

    """ Update ticket comment """
    def update_ticket_comment(self, comment, *args, **kargs):
        post_data = comment.toJSON()
        kargs['post_data'] = post_data
        return bind_api(
            path='spaces/{space}/tickets/{ticket}/ticket_comments.json',
            method='POST',
            payload_type='ticketcomment'
        )(self, *args, **kargs)

    """ Get all document for space """
    get_documents = bind_api(
        path='spaces/{space}/documents.json',
        method='GET',
        allowed_params = ['space'],
        payload_type='document', payload_list=True
    )

    """ Get a document by id """
    get_document = bind_api(
        path='spaces/{space}/documents/{document}.json',
        method='GET',
        allowed_params = ['space', 'document'],
        payload_type='document'
    )

    """ Create document """
    def create_document(self, filecontent, docmeta, *args, **kargs):
        headers, post_data = API._pack_file(filecontent, docmeta)
        kargs['post_data'] = post_data
        kargs['headers'] = headers
        return bind_api(
            path = 'spaces/{space}/documents.json',
            method = 'POST',
            payload_type = 'document'
        )(self, *args, **kargs)


    """ Internal use only """
    @staticmethod
    def _pack_file(fileresponse, docmeta):

        fields = ['name', 'attachable_id', 'description', 'attachable_type']

        # build the mulitpart-formdata body
        BOUNDARY = '4079f119cf48'
        body = []
        body.append('--'+BOUNDARY)
        body.append('Content-Disposition: form-data; name="document[file]"; filename="%s"' % docmeta.name)
        body.append('Content-Type: application/octet-stream')
        body.append('')
        body.append(fileresponse.content)
        for field in fields:
            body.append('--'+BOUNDARY)
            body.append('Content-Disposition: form-data; name="document[%s]"' % field)
            body.append('')
            body.append(str(getattr(docmeta, field, '')))
        body.append('--'+BOUNDARY + '--')
        body.append('')
        body = '\r\n'.join(body)

        # build headers
        headers = {
            'Content-Type': 'multipart/form-data; boundary=%s' %BOUNDARY,
        }

        return headers, body

