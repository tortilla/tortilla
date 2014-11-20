# -*- coding: utf-8 -*-

import sys
import os

import bunch
import colorclass
import requests


_version = sys.version_info
is_py2 = (_version[0] == 2)
is_py3 = (_version[0] == 3)

if is_py2:
    str = basestring
# We've made an assumption that `str` will still exist in future Python versions


debug_messages = {
    'request': (
        '{blue}Executing {method} request:{/blue}\n'
        '{hiblack}'
        '    URL:   {url}\n'
        '    headers: {headers}\n'
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
        self.headers = bunch.Bunch()
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

    def request(self, method, url, path=(), params=None, headers=None,
                 data=None, debug=None, **kwargs):
        """Requests a URL and returns a *Bunched* response.

        :param method: The request method, e.g. 'get', 'post', etc.
        :param url: The URL to request
        :param path: (optional) Appended to the request URL. This can be
                     either a string or a list which will be joined
                     by forward slashes.
        :param params: (optional) The URL query parameters
        :param headers: (optional) Extra headers to sent with the request.
                        Existing header keys can be overwritten.
        :param data: (optional) Dictionary
        :param debug: (optional) Overwrite of `Client.debug`
        :param kwargs: (optional) Arguments that will be passed to
                       the `requests.request` method
        :return: :class:`Bunch` object from JSON-parsed response
        """
        if not isinstance(path, str):
            path = '/'.join(item for item in path)

        request_headers = dict(self.headers.__dict__)
        if headers is not None:
            request_headers.update(headers)

        if debug is None:
            debug = self.debug

        url = url + path

        self._log(debug_messages['request'], debug,
                  method=method.upper(), url=url, headers=request_headers,
                  params=params, data=data)

        r = requests.request(method, url, params=params,
                             headers=request_headers, data=data, **kwargs)

        json_response = r.json()

        debug_message = 'success_response' if r.status_code == 200 else \
            'failure_response'
        self._log(debug_messages[debug_message], debug,
                  status_code=r.status_code, reason=r.reason,
                  text=json_response)

        return bunch.bunchify(json_response)


class Wrap(object):
    def __init__(self, part, parent=None, headers=None, debug=None):
        self.part = part
        self.__parts = None
        self.parent = parent or Client(debug=debug)
        self.headers = bunch.bunchify(headers) if headers else bunch.Bunch()
        self.debug = debug

    def parts(self):
        if self.__parts:
            return self.__parts
        try:
            self.__parts = '/'.join([self.parent.parts(), self.part])
        except AttributeError:
            self.__parts = self.part
        return self.__parts

    def __call__(self, part=None, **options):
        if not part:
            self.__dict__.update(**options)
            return self
        try:
            return self.__dict__[part]
        except KeyError:
            self.__dict__[part] = Wrap(part=part, parent=self,
                                       debug=self.debug, **options)
            return self.__dict__[part]

    def __getattr__(self, part):
        try:
            return self.__dict__[part]
        except KeyError:
            self.__dict__[part] = Wrap(part=part, parent=self,
                                       debug=self.debug)
            return self.__dict__[part]

    def request(self, method, pk=None, **options):
        if not options.get('url'):
            options['url'] = '/'.join([self.parts(), unicode(pk)]) \
                if pk else self.parts()
        options.setdefault('debug', self.debug)
        headers = self.headers.copy()
        if options.get('headers'):
            headers.update(options['headers'])
        options['headers'] = headers
        return self.parent.request(method=method, **options)

    def get(self, pk=None, **options):
        return self.request('get', pk, **options)

    def post(self, pk=None, **options):
        return self.request('post', pk, **options)

    def put(self, pk=None, **options):
        return self.request('put', pk, **options)

    def patch(self, pk=None, **options):
        return self.request('patch', pk, **options)

    def delete(self, pk=None, **options):
        return self.request('delete', pk, **options)

    def __repr__(self):
        return "<{} for {}>".format(self.__class__.__name__, self.parts())
