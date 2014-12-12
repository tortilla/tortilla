# -*- coding: utf-8 -*-

import os
import time

import bunch
import colorclass
import requests

from .compat import string_type
from .utils import run_from_ipython


debug_messages = {
    'request': (
        '{blue}Executing {method} request:{/blue}\n'
        '{hiblack}'
        '    URL:     {url}\n'
        '    headers: {headers}\n'
        '    query:   {params}\n'
        '    data:    {data}\n'
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
    'cached_response': (
        '{cyan}Cached response:{/cyan}\n'
        '{hiblack}'
        '    {text}\n'
        '{/hiblack}'
    ),
    'nojson_response': (
        '{red}Got {status_code} {reason} (NOT JSON):{/red}\n'
        '{hiblack}'
        '    {text}\n'
        '{/hiblack}'
    )
}


DEBUG_MAX_TEXT_LENGTH = 100


if os.name == 'nt':
    if run_from_ipython():
        # IPython stops working properly when it loses control of
        # `stdout` on Windows. In this case we won't enable Windows
        # color support and we'll strip out all colors from the debug
        # messages.
        colorclass.disable_all_colors()
    else:
        colorclass.Windows.enable()


class Client(object):
    """Wrapper around the most basic methods of the requests library."""

    def __init__(self, debug=False):
        self.headers = bunch.Bunch()
        self.debug = debug
        self.cache = {}
        self.session = requests.session()

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
            print((colored_message.format(**kwargs)))

    def request(self, method, url, path=(), extension=None, params=None,
                headers=None, data=None, debug=None, cache_lifetime=None,
                silent=False, ignore_cache=False, **kwargs):
        """Requests a URL and returns a *Bunched* response.

        This method basically wraps the request method of the requests
        module and adds a `path` and `debug` option.

        A `ValueError` will be thrown if the response is not JSON encoded.

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

        if not isinstance(path, string_type):
            path = '/'.join(path)

        request_headers = dict(self.headers.__dict__)
        if headers is not None:
            request_headers.update(headers)

        if debug is None:
            debug = self.debug

        if extension is None:
            extension = ''
        elif not extension.startswith('.'):
            extension = '.' + extension

        url = url + path + extension

        self._log(debug_messages['request'], debug,
                  method=method.upper(), url=url, headers=request_headers,
                  params=params, data=data)

        cache_key = (url, str(params), str(headers))
        if cache_key in self.cache and not ignore_cache:
            item = self.cache[cache_key]
            if item['expires'] > time.time():
                self._log(debug_messages['cached_response'], debug,
                          text=item['value'])
                return bunch.bunchify(item['value'])
            del self.cache[cache_key]

        r = self.session.request(method, url, params=params,
                                 headers=request_headers, data=data, **kwargs)

        try:
            has_body = len(r.text) > 0
            if not has_body:
                json_response = 'No response'
            else:
                json_response = r.json()
        except ValueError as e:
            if len(r.text) > DEBUG_MAX_TEXT_LENGTH:
                text = r.text[:DEBUG_MAX_TEXT_LENGTH] + '...'
            else:
                text = r.text
            self._log(debug_messages['nojson_response'], debug,
                      status_code=r.status_code, reason=r.reason, text=text)
            if silent:
                return None
            raise e

        if cache_lifetime and cache_lifetime > 0 and method.lower() == 'get':
            self.cache[cache_key] = {'expires': time.time() + cache_lifetime,
                                     'value': json_response}

        debug_message = 'success_response' if r.status_code == 200 else \
            'failure_response'
        self._log(debug_messages[debug_message], debug,
                  status_code=r.status_code, reason=r.reason,
                  text=json_response)

        if has_body:
            return bunch.bunchify(json_response)
        return None


class Wrap(object):
    """Represents a part of the wrapped URL.

    You can chain this object to other Wrap objects. This is done
    *automagically* when accessing non-existing attributes of the object.

    The root of the chain should be a :class:`Client` object. When a new
    :class:`Wrap` object is created without a parent, it will create a
    new :class:`Client` object which will act as the root.
    """

    def __init__(self, part, parent=None, headers=None, debug=None,
                 cache_lifetime=None, silent=False, extension=None):
        if isinstance(part, string_type):
            # trailing slashes are removed
            self.part = part[:-1] if part[-1:] == '/' else part
        else:
            self.part = str(part)
        self._url = None
        self.parent = parent or Client(debug=debug)
        self.headers = bunch.bunchify(headers) if headers else bunch.Bunch()
        self.debug = debug
        self.cache_lifetime = cache_lifetime
        self.silent = silent
        self.extension = extension

    def url(self):
        if self._url:
            return self._url
        try:
            self._url = '/'.join([self.parent.url(), self.part])
        except AttributeError:
            self._url = self.part
        return self._url

    def __call__(self, *parts, **options):
        """Creates and returns a new :class:`Wrap` object in the chain
        if `part` is provided. If not, the current object's options
        will be manipulated by the provided `options` ``dict`` and the
        current object will be returned.

        Usage::

            # creates a new Wrap, assuming `foo` is already wrapped
            foo('bar')

            # this is the same as:
            foo.bar()

            # which is the same as:
            foo.bar

            # enabling `debug` for a specific chain object
            foo.bar(debug=True)

        :param part: (optional) The URL part to append to the current chain
        :param options: (optional) Arguments accepted by the
            :class:`Wrap` initializer
        """
        self.__dict__.update(**options)

        if len(parts) == 0:
            return self

        parent = self
        for part in parts:
            # check if a wrap is already created for the part
            try:
                # the next part in this loop will have this wrap as
                # its parent
                parent = parent.__dict__[part]
            except KeyError:
                # create a wrap for the part
                parent.__dict__[part] = Wrap(part=part, parent=parent)
                parent = parent.__dict__[part]

        return parent

    def __getattr__(self, part):
        try:
            return self.__dict__[part]
        except KeyError:
            self.__dict__[part] = Wrap(part=part, parent=self,
                                       debug=self.debug)
            return self.__dict__[part]

    def request(self, method, pk=None, **options):
        """Requests a URL and returns a *Bunched* response.

        This method basically wraps the request method of the requests
        module and adds a `path` and `debug` option.

        :param method: The request method, e.g. 'get', 'post', etc.
        :param pk: (optional) A primary key to append to the path
        :param url: (optional) The URL to request
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

        if not options.get('url'):
            # if a primary key is given, it is joined with the requested URL
            if pk:
                options['url'] = '/'.join([self.url(), pk])
            else:
                options['url'] = self.url()

        if self.debug is not None:
            options.setdefault('debug', self.debug)
        if self.cache_lifetime is not None:
            options.setdefault('cache_lifetime', self.cache_lifetime)
        if self.silent is not None:
            options.setdefault('silent', self.silent)
        if self.extension is not None:
            options.setdefault('extension', self.extension)

        # headers are copied into a new object so temporary
        # custom headers aren't overriding future requests
        headers = self.headers.copy()
        if options.get('headers'):
            headers.update(options['headers'])
        options['headers'] = headers

        return self.parent.request(method=method, **options)

    def get(self, pk=None, **options):
        """Executes a `GET` request on the currently formed URL."""
        return self.request('get', pk, **options)

    def post(self, pk=None, **options):
        """Executes a `POST` request on the currently formed URL."""
        return self.request('post', pk, **options)

    def put(self, pk=None, **options):
        """Executes a `PUT` request on the currently formed URL."""
        return self.request('put', pk, **options)

    def patch(self, pk=None, **options):
        """Executes a `PATCH` request on the currently formed URL."""
        return self.request('patch', pk, **options)

    def delete(self, pk=None, **options):
        """Executes a `DELETE` request on the currently formed URL."""
        return self.request('delete', pk, **options)

    def head(self, pk=None, **options):
        """Executes a `HEAD` request on the currently formed URL."""
        return self.request('head', pk, **options)

    def __repr__(self):
        return "<{} for {}>".format(self.__class__.__name__, self.url())
