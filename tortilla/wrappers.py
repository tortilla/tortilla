# -*- coding: utf-8 -*-

import os

import colorclass
import requests

from .utils import Bunch


try:
    # This should raise a `NameError` on Python 2
    str
except NameError:
    # Replace the Python 3 `str` type with Python 2's `basestring` type
    str = basestring


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


# Enable console colors for Windows if we're actually on Windows
if os.name == 'nt':
    colorclass.Windows.enable()


class Client(object):

    def __init__(self, debug=False):
        self.debug = debug

    def _log(self, message, debug=None, **params):
        display_log = self.debug
        if debug is not None:
            display_log = debug
        if display_log:
            colored_message = colorclass.Color(message)
            print(colored_message.format(**params))

    def _request(self, method, url, path=(), params=None, headers=None,
                 data=None, debug=None):
        if not isinstance(path, str):
            path = '/'.join(path)

        url = url + path

        self._log(debug_messages['request'], debug,
                  method=method.upper(), url=url, params=params,
                  data=data)

        r = requests.request(method, url, params=params, headers=headers, data=data)

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
