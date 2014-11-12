# -*- coding: utf-8 -*-

import sys
import os

import colorclass
import requests

from .utils import Bunch


_version = sys.version_info
is_py2 = (_version[0] == 2)
is_py3 = (_version[0] == 3)

if is_py2:
    str = basestring
# We've made an assumption that `str` will still exist in Py3+


debug_messages = {
    'request': (
        '{blue}Executing {method} request:{/blue}\n'
        '{hiblack}'
        '    URL:   {url}\n'
        '    query: {params}\n'
        '    data:  {data}\n'
        '{/hiblack}'
    ),
    'success_response': (
        '{green}Got {status_code} {reason}:{/green}\n'
        '{hiblack}'
        '    {text}\n'
        '{/hiblack}'
    ),
    'failure_response': (
        '{red}Got {status_code} {reason}:{/red}\n'
        '{hiblack}'
        '    {text}\n'
        '{/hiblack}'
    ),
}


if os.name == 'nt':
    # Enable console colors for Windows
    colorclass.Windows.enable()


class Client(object):
    """Wrapper around the most basic methods of the requests library."""

    def __init__(self, debug=False):
        # TODO: Implement default headers functionality
        self.debug = debug

    def _log(self, message, debug=None, **kwargs):
        """Outputs a colored and formatted message in the console
        if the debug mode is activated.

        :param message: the message that will be printed
        :param debug: (optional) Overwrite of `Client.debug`
        :param kwargs: (optional) Arguments that will be passed
                       to the `str.format()` method
        """
        display_log = self.debug
        if debug is not None:
            display_log = debug
        if display_log:
            colored_message = colorclass.Color(message)
            print(colored_message.format(**kwargs))

    def _request(self, method, url, path=(), params=None, headers=None,
                 data=None, debug=None, **kwargs):
        """Requests a URL and returns a *Bunched* response.

        :param method: The request method, e.g. 'get', 'post', etc.
        :param url: The URL to request
        :param path: (optional) Appended to the request URL. This can be
                     either a string or a list which will be joined
                     by forward slashes.
        :param params: (optional) The URL parameters, also known as 'query'
        :param headers:
        :param data: (optional) Dictionary
        :param debug: (optional) Overwrite of `Client.debug`
        :param kwargs: (optional) Arguments that will be passed to
                       the `requests.request` method
        :return:
        """
        if not isinstance(path, str):
            path = '/'.join(unicode(item) for item in path)

        url = url + path

        self._log(debug_messages['request'], debug,
                  method=method.upper(), url=url, kwargs=params,
                  data=data)

        r = requests.request(method, url, params=params, headers=headers,
                             data=data, **kwargs)

        json_response = r.json()

        debug_message = 'success_response' if r.status_code == 200 else \
            'failure_response'
        self._log(debug_messages[debug_message], debug,
                  status_code=r.status_code, reason=r.reason,
                  text=json_response)

        return Bunch(**json_response)

    def get(self, **options):
        return self._request('get', **options)

    def post(self, **options):
        return self._request('post', **options)

    def put(self, **options):
        return self._request('put', **options)

    def delete(self, **options):
        return self._request('delete', **options)


class Service(object):
    def __init__(self, url, debug=False):
        self.url = url
        self.client = Client(debug=debug)

    def __call__(self, path, debug=None):
        return Endpoint(self, path, debug)

    def endpoint(self, path, debug=None):
        return Endpoint(self, path, debug)

    def get(self, **options):
        return self.client.get(url=self.url, **options)

    def post(self, **options):
        return self.client.post(url=self.url, **options)

    def put(self, **options):
        return self.client.put(url=self.url, **options)

    def delete(self, **options):
        return self.client.delete(url=self.url, **options)


class Endpoint(object):
    def __init__(self, service, path, debug=None):
        self.service = service
        self.path = path
        self.debug = debug

    def get(self, pk, **options):
        options.setdefault('debug', self.debug)
        return self.service.get(path=[self.path, pk], **options)

    def post(self, data, **options):
        options.setdefault('debug', self.debug)
        return self.service.post(path=self.path, data=data, **options)

    def put(self, pk, data, **options):
        options.setdefault('debug', self.debug)
        return self.service.put(path=[self.path, pk], data=data, **options)

    def delete(self, pk, **options):
        options.setdefault('debug', self.debug)
        return self.service.delete(path=[self.path, pk], **options)
