import httplib
import urllib
import time
import re

from assembla.error import AssemblaError
from assembla.utils import convert_to_utf8_str
from assembla.models import Model

re_path_template = re.compile('{\w+}')


def bind_api(**config):

    class APIMethod(object):

        path = config['path']
        payload_type = config.get('payload_type', None)
        payload_list = config.get('payload_list', False)
        allowed_param = config.get('allowed_param', [])
        method = config.get('method', 'GET')
        require_auth = config.get('require_auth', True)
        search_api = config.get('search_api', False)
        use_cache = config.get('use_cache', True)

        def __init__(self, api, args, kargs):
            # If authentication is required and no credentials
            # are provided, throw an error.
            if self.require_auth and not api.client.service.access_token:
                raise AssemblaError('Authentication required!')

            self.api = api
            self.post_data = kargs.pop('post_data', None)
            self.retry_count = kargs.pop('retry_count', api.retry_count)
            self.retry_delay = kargs.pop('retry_delay', api.retry_delay)
            self.retry_errors = kargs.pop('retry_errors', api.retry_errors)
            self.okay_status = kargs.pop('okay_status', api.okay_status)
            self.headers = kargs.pop('headers', {})
            self.build_parameters(args, kargs)

            # Assembla accepts multiple formats, we work with json.
            if 'Content-Type' not in self.headers:
                self.headers['Content-Type'] = 'application/json'

            # Pick correct URL root to use
            if self.search_api:
                self.api_root = api.search_root
            else:
                self.api_root = api.api_root

            # Perform any path variable substitution
            self.build_path()

            if api.secure:
                self.scheme = 'https://'
            else:
                self.scheme = 'http://'

            if self.search_api:
                self.host = api.search_host
            else:
                self.host = api.host

        def build_parameters(self, args, kargs):
            self.parameters = {}
            for idx, arg in enumerate(args):
                if arg is None:
                    continue

                try:
                    self.parameters[self.allowed_param[idx]] = convert_to_utf8_str(arg)
                except IndexError:
                    raise AssemblaError('Too many parameters supplied!')

            for k, arg in kargs.items():
                if arg is None:
                    continue
                if k in self.parameters:
                    raise AssemblaError('Multiple values for parameter %s supplied!' % k)

                self.parameters[k] = convert_to_utf8_str(arg)

        def build_path(self):
            for variable in re_path_template.findall(self.path):
                name = variable.strip('{}')

                try:
                    value = urllib.quote(self.parameters[name])
                except KeyError:
                    raise AssemblaError('No parameter value found for path variable: %s' % name)
                del self.parameters[name]

                self.path = self.path.replace(variable, value)

        def execute(self):
            # Build the request URL
            schema = 'https://' if self.api.secure else 'http://'
            url = schema + self.host + self.api_root + self.path
            if len(self.parameters):
                url = '%s?%s' % (url, urllib.urlencode(self.parameters))

            m = getattr(self.api.client, self.method)
            resp = m(url, headers=self.headers, data=self.post_data)

            # If an error was returned, throw an exception
            self.api.last_response = resp
            if resp.status_code == 204:
                return []
            elif resp.status_code not in self.okay_status:
                try:
                    error_msg = self.api.parser.parse_error(resp.content)
                except Exception:
                    error_msg = "Assembla error response: status code = %s" % resp.status_code
                raise AssemblaError(error_msg, resp)

            # Parse the response payload
            result = self.api.parser.parse(self, resp.content)
            return result


    def _call(api, *args, **kargs):

        method = APIMethod(api, args, kargs)
        return method.execute()


    # Set pagination mode
    if 'cursor' in APIMethod.allowed_param:
        _call.pagination_mode = 'cursor'
    elif 'page' in APIMethod.allowed_param:
        _call.pagination_mode = 'page'

    return _call

