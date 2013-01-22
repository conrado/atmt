import time
import requests

from rauth.service import OAuth2Service
from assembla.error import AssemblaError


class HttpClient(object):

    RETRY_CODES = [502, 503, 504]
    UNAUTHED_CODES = [401]
    OKAY_STATUS = [200, 201]

    def __init__(self, consumer_key, consumer_secret, pin=None,
            retry_count=3, retry_delay=3, retry_errors=None):
        self.service = OAuth2Service(
            name='assembla',
            authorize_url='https://api.assembla.com/authorization',
            access_token_url='https://api.assembla.com/token',
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
        )
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.retry_errors = retry_errors or self.RETRY_CODES
        if pin:
            self.initClient(pin)

    def getAuthorizeUrl(self):
        return self.service.get_authorize_url(response_type='pin_code')

    def initClient(self, pin):
        data = dict(pin_code=pin,
            grant_type="pin_code",
            redirect_uri="")
        response = self.service.get_access_token("POST", data=data)
        self.initTokens(response.content["access_token"],
                        response.content["refresh_token"])

    def initTokens(self, access_token, refresh_token):
        self.service.access_token = access_token
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client = requests.Session()
        self.client.stream = False
        self.client.headers.update({"Authorization": 'Bearer %s'%access_token})

    def refreshTokens(self):
        data = dict(
            grant_type="refresh_token",
            refresh_token=self.refresh_token)
        response = self.service.get_access_token("POST", data=data)
        self.initTokens(response.content["access_token"],
                        self.refresh_token)

    def GET(self, url, **kargs):
        r=self.retry('get', url, **kargs)
        return r

    def POST(self, url, **kargs):
        r=self.retry('post', url, **kargs)
        return r

    def DELETE(self, url, **kargs):
        r=self.retry('delete', url, **kargs)
        return r

    def PUT(self, url, **kargs):
        r=self.retry('put', url, **kargs)
        return r

    def retry(self, method, url, **kargs):
        # Continue attempting request until successful
        # or maximum number of retries is reached.
        retries_performed = 0
        while retries_performed <= self.retry_count:
            m=getattr(self.client, method)

            # Execute request
            try:
                resp = m(url, **kargs)
            except Exception, e:
                raise AssemblaError('Failed to send request: %s' % e)

            # If unauthenticated try to refresh Access Token
            if resp.status_code in self.UNAUTHED_CODES:
                self.refreshTokens()
            # Exit request loop if non-retry error code
            elif self.retry_errors:
                if resp.status_code not in self.retry_errors: break
            else:
                if resp.status_code in self.OKAY_STATUS: break

            # Sleep before retrying request again
            time.sleep(self.retry_delay)
            retries_performed += 1
        return resp
