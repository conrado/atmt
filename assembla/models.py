from assembla.error import AssemblaError
from assembla.utils import parse_datetime, parse_date, parse_html_value, \
        parse_a_href, parse_search_datetime, unescape_html, parse_file

from utils import import_simplejson, DateTimeJSONEncoder

json = import_simplejson()

class ResultSet(list):
    """A list like object that holds results from a Twitter API query."""


class Model(object):

    def __init__(self, api=None):
        self._api = api

    def __getstate__(self):
        # pickle
        pickle = dict(self.__dict__)
        try:
            del pickle['_api']  # do not pickle the API reference
        except KeyError:
            pass
        return pickle

    def toJSON(self):
        return json.dumps(self)

    @classmethod
    def parse(cls, api, json):
        """Parse a JSON object into a model instance."""
        raise NotImplementedError

    @classmethod
    def parse_list(cls, api, json_list):
        """Parse a list of JSON objects into a result set of model instances."""
        results = ResultSet()
        for obj in json_list:
            if obj:
                results.append(cls.parse(api, obj))
        return results

    def __str__(self):
        """Return object id for easier serialization"""
        return str(self.id)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__str__())


class Space(Model):

    @classmethod
    def parse(cls, api, json):
        space = cls(api)
        for k, v in json.items():
            if (k == 'created_at' or k == 'updated_at' or k == 'commercial_from') and v:
                setattr(space, k, parse_datetime(v))
            elif (k == 'restricted_date' or k == 'last_payer_changed_at') and v:
                setattr(space, k, parse_date(v))
            elif k == 'tabs_order':
                pass # for now
            #elif k == 'place':
                #if v is not None:
                    #setattr(space, k, Place.parse(api, v))
                #else:
                    #setattr(space, k, None)
            else:
                setattr(space, k, v)
        return space

    """
            if k == 'user':
                user_model = getattr(api.parser.model_factory, 'user')
                user = user_model.parse(api, v)
                setattr(space, 'author', user)
                setattr(space, 'user', user)  # DEPRECIATED
    """

    def destroy(self):
        return self._api.delete_space(space=self.id)

    def get_milestones(self):
        return self._api.get_milestones(space=self.id)

    def create_milestone(self, milestone):
        return self._api.create_milestone(milestone, space=self.id)

    def get_components(self):
        return self._api.get_ticket_components(space=self.id)

    def create_component(self, component):
        return self._api.create_ticket_component(component, space=self.id)

    def get_custom_fields(self):
        return self._api.get_custom_fields(space=self.id)

    def create_custom_field(self, field):
        return self._api.create_custom_field(field, space=self.id)

    def get_ticket_statuses(self):
        return self._api.get_ticket_statuses(space=self.id)

    def create_ticket_status(self, status):
        return self._api.create_ticket_status(status, space=self.id)

    def get_tickets(self):
        return self._api.get_tickets(space=self.id)

    def get_ticket(self, number):
        return self._api.get_ticket(space=self.id, ticket=number)

    def create_ticket(self, ticket):
        return self._api.create_ticket(ticket, space=self.id)

class InstantMessenger(Model):

    @classmethod
    def parse(cls, api, json):
        im = cls(api)
        for k, v in json.items():
            setattr(im, k, v)
        return im


class User(Model):

    @classmethod
    def parse(cls, api, json):
        user = cls(api)
        for k, v in json.items():
            if k == 'im' or k == 'im2':
                setattr(user, k, InstantMessenger.parse(api, v))
            else:
                setattr(user, k, v)
        return user

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['users']

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

class Ticket(Model):

    @classmethod
    def parse(cls, api, json):
        ticket = cls(api)
        for k, v in json.items():
            if (k == 'created_on' or k == 'updated_at' or k == 'completed_date') and v:
                setattr(ticket, k, parse_datetime(v))
            else:
                setattr(ticket, k, v)
        return ticket

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['tickets'] # XXX check

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

    def toJSON(self):
        pickle = self.__getstate__()
        pickle = {'ticket': pickle}
        return json.dumps(pickle, cls=DateTimeJSONEncoder)

    def __str__(self):
        """Return ticket number for easier serialization"""
        return str(self.number)

    def get_associations(self):
        return self._api.get_associations(space=self.space_id, ticket=self.number)

    def create_association(self, association):
        return self._api.create_association(association, space=self.space_id, ticket=self.number)

    def get_comments(self):
        return self._api.get_ticket_comments(space=self.space_id, ticket=self.number)

    def create_comment(self, comment):
        return self._api.create_ticket_comment(comment, space=self.space_id, ticket=self.number)

    def attach_file(self, filecontent, docmeta):
        docmeta.attachable_id = self.id
        return self._api.create_document(filecontent, docmeta, space=self.space_id)

    def destroy(self):
        return self._api.delete_ticket(space=self.space_id, ticket=self.number)

    def get_document(self, fileid):
        return self._api.get_document(space=self.space_id, document=fileid)

class TicketComment(Model):

    @classmethod
    def parse(cls, api, json):
        comment = cls(api)
        comment.file = None
        comment.comment = None
        for k, v in json.items():
            if (k == 'created_on' or k == 'updated_at') and v:
                v = parse_datetime(v)
            elif (k == 'comment') and v:
                if '[[file' in v or '[[image' in v:
                    comment.file = parse_file(v)
            setattr(comment, k, v)
        return comment

    def toJSON(self):
        pickle = self.__getstate__()
        pickle = {'ticket_comment': pickle}
        return json.dumps(pickle, cls=DateTimeJSONEncoder)


class TicketCustomField(Model):

    @classmethod
    def parse(cls, api, json):
        customfield = cls(api)
        for k, v in json.items():
            if (k == 'created_on' or k == 'updated_at') and v:
                setattr(customfield, k, parse_datetime(v))
            else:
                setattr(customfield, k, v)
        return customfield

    def toJSON(self):
        pickle = self.__getstate__()
        pickle = {'custom_field': pickle}
        return json.dumps(pickle, cls=DateTimeJSONEncoder)


class TicketComponent(Model):

    @classmethod
    def parse(cls, api, json):
        component = cls(api)
        for k, v in json.items():
            setattr(component, k, v)
        return component

    def toJSON(self):
        pickle = {'component': self.name}
        return json.dumps(pickle)


class TicketAssociation(Model):

    @classmethod
    def parse(cls, api, json):
        association = cls(api)
        for k, v in json.items():
            if (k == 'created_at' or k == 'updated_at') and v:
                setattr(association, k, parse_datetime(v))
            else:
                setattr(association, k, v)
        return association

    def toJSON(self):
        pickle = self.__getstate__()
        pickle = {'ticket_association': pickle}
        return json.dumps(pickle, cls=DateTimeJSONEncoder)

    def invert(self):
        tmp = self.ticket1_id
        self.ticket2_id = self.ticket1_id
        self.ticket1_id = tmp
        if self.relationship == 0:
            self.relationship = 1
        elif self.relationship == 1:
            self.relationship = 0
        elif self.relationship == 7:
            self.relationship = 8
        elif self.relationship == 8:
            self.relationship = 7



class TicketStatus(Model):

    @classmethod
    def parse(cls, api, json):
        status = cls(api)
        for k, v in json.items():
            if (k == 'created_at' or k == 'updated_at') and v:
                setattr(status, k, parse_datetime(v))
            else:
                setattr(status, k, v)
        return status

    def toJSON(self):
        pickle = self.__getstate__()
        pickle = {'status': pickle}
        return json.dumps(pickle, cls=DateTimeJSONEncoder)

class Milestone(Model):

    @classmethod
    def parse(cls, api, json):
        milestone = cls(api)
        for k, v in json.items():
            if (k == 'created_at' or k == 'updated_at') and v:
                setattr(milestone, k, parse_datetime(v))
            if (k == 'completed_date' or k == 'due_date') and v:
                setattr(milestone, k, parse_date(v))
            else:
                setattr(milestone, k, v)
        return milestone

    def toJSON(self):
        pickle = self.__getstate__()
        pickle = {'milestone': pickle}
        return json.dumps(pickle, cls=DateTimeJSONEncoder)


class Document(Model):

    @classmethod
    def parse(cls, api, json):
        document = cls(api)
        for k, v in json.items():
            if (k == 'created_at' or k == 'updated_at') and v:
                setattr(document, k, parse_datetime(v))
            else:
                setattr(document, k, v)
        return document

    def toJSON(self):
        pickle = self.__getstate__()
        pickle = {'document': pickle}
        return json.dumps(pickle, cls=DateTimeJSONEncoder)


class MergeRequest(Model):

    @classmethod
    def parse(cls, api, json):
        mergerequest = cls(api)
        for k, v in json.items():
            if k in ['applied_at', 'created_at', 'updated_at'] and v:
                setattr(mergerequest, k, parse_datetime(v))
            else:
                setattr(mergerequest, k, v)
        return mergerequest

    def toJSON(self):
        pickle = self.__getstate__()
        pickle = {'merge_request': pickle}
        return json.dumps(pickle, cls=DateTimeJSONEncoder)


class JSONModel(Model):

    @classmethod
    def parse(cls, api, json):
        return json


class IDModel(Model):

    @classmethod
    def parse(cls, api, json):
        if isinstance(json, list):
            return json
        else:
            return json['ids']


class ModelFactory(object):
    """
    Used by parsers for creating instances
    of models. You may subclass this factory
    to add your own extended models.
    """

    space = Space
    user = User

    ticket = Ticket
    ticketcomment = TicketComment
    ticketcustomfield = TicketCustomField
    ticketcomponent = TicketComponent
    ticketassociation = TicketAssociation
    ticketstatus = TicketStatus

    document = Document
    milestone = Milestone
    mergerequest = MergeRequest

    json = JSONModel
    ids = IDModel
