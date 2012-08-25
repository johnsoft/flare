import json
import pprint
from urllib import parse, request as requestlib


SECURITY_LEVELS = {
    'eoff': 'Essentially Off',
    'low':  'Low',
    'med':  'Medium',
    'high': 'High',
    'help': '',
}


class QuitApp(BaseException):
    def __init__(self, message):
        self.message = message


def nice_dump(obj, prefix):
    ret = pprint.PrettyPrinter().pformat(obj)
    if prefix:
        ret = prefix + ('\n' + prefix).join(ret.splitlines())
    return ret


class APIError(Exception):
    def __init__(self, message):
        self.message = message


class APIRequest:
    url = 'https://www.cloudflare.com/api_json.html'

    def __init__(self, params):
        self.params = params
        self.dump = False

    def send(self):
        response = None
        try:
            if self.dump:
                print(nice_dump(self.params, '> '))
            data = parse.urlencode(self.params).encode('utf-8')
            response = requestlib.urlopen(self.url, data)
        except requestlib.URLError:
            raise QuitApp("Error connecting to CloudFlare API endpoint.")
        else:
            try:
                ret = json.loads(response.read().decode('utf-8'))
            except Exception:
                raise QuitApp('Malformed response from CloudFlare API endpoint.')
            if self.dump:
                print(nice_dump(ret, '< '))
            return ret
        finally:
            if response is not None:
                response.close()
