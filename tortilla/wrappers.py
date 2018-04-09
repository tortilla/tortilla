# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import time

import requests
import six
from colorama import Fore, Style, init as init_colorama

from . import formatters
from .cache import CacheWrapper, DictCache
from .utils import formats, run_from_ipython, Bunch, bunchify

try:
    import OpenSSL
    ConnectionError = OpenSSL.SSL.SysCallError
except ImportError:
    ConnectionError = requests.exceptions.ConnectionError


#: Dictionary of colored debug messages used in the `~Client._log` method
debug_messages = {
    'request': ''.join([
        Fore.BLUE, 'Executing {method} request:\n',
        Fore.BLACK, Style.BRIGHT,
        '    URL:     {url}\n',
        '    headers: {headers}\n',
        '    query:   {params}\n',
        '    data:    {data}\n',
        Style.RESET_ALL
    ]),
    'success_response': ''.join([
        Fore.GREEN, 'Got {status_code} {reason}:\n',
        Fore.BLACK, Style.BRIGHT,
        '    {text}\n',
        Style.RESET_ALL
    ]),
    'failure_response': ''.join([
        Fore.RED, 'Got {status_code} {reason}:\n',
        Fore.BLACK, Style.BRIGHT,
        '    {text}\n',
        Style.RESET_ALL
    ]),
    'cached_response': ''.join([
        Fore.CYAN, 'Cached response:\n',
        Fore.BLACK, Style.BRIGHT,
        '    {text}\n',
        Style.RESET_ALL
    ]),
    'incorrect_format_response': ''.join([
        Fore.RED, 'Got {status_code} {reason} (not {format}):\n',
        Fore.BLACK, Style.BRIGHT,
        '    {text}\n',
        Style.RESET_ALL
    ])
}


#: The maximum length of a response displayed in a debug message
DEBUG_MAX_TEXT_LENGTH = 100


if os.name == 'nt' and run_from_ipython():
    # IPython stops working properly when it loses control of
    # `stdout` on Windows. In this case we won't enable Windows
    # color support and we'll strip out all colors from the debug
    # messages.
    init_colorama(wrap=False)
else:
    init_colorama()


class Client(object):
    """Wrapper around the most basic methods of the requests library."""

    def __init__(self, debug=False, cache=None, **kwargs):
        self.headers = Bunch()
        self.debug = debug
        self.cache = cache if cache else DictCache()
        self.cache = CacheWrapper(self.cache)
        self.session = requests.session()
        self._last_request_time = None
        self.defaults = kwargs

    def _log(self, message, debug=None, **kwargs):
        """Outputs a formatted message in the console if the
        debug mode is activated.

        :param message: The message that will be printed
        :param debug: (optional) Overwrite of `Client.debug`
        :param kwargs: (optional) Arguments that will be passed
            to the `str.format()` method
        """
        display_log = self.debug
        if debug is not None:
            display_log = debug
        if display_log:
            print(message.format(**kwargs))

    def send_request(self, *args, **kwargs):
        """Wrapper for session.request
        Handle connection reset error even from pyopenssl
        """
        try:
            return self.session.request(*args, **kwargs)
        except ConnectionError:
            self.session.close()
            return self.session.request(*args, **kwargs)

    def request(self, method, url, path=(), extension=None, suffix=None,
                params=None, headers=None, data=None, debug=None,
                cache_lifetime=None, silent=None, ignore_cache=False,
                format='json', delay=0.0, formatter=None, **kwargs):
        """Requests a URL and returns a *Bunched* response.

        This method basically wraps the request method of the requests
        module and adds a `path` and `debug` option.

        A `ValueError` will be thrown if the response is not JSON encoded.

        :param method: The request method, e.g. 'get', 'post', etc.
        :param url: The URL to request
        :param path: (optional) Appended to the request URL. This can be
            either a string or a list which will be joined
            by forward slashes.
        :param extension: (optional) The extension to append to the URL.
        :param suffix: (optional) Append stuff like trailing slashes the URL.
        :param params: (optional) The URL query parameters
        :param headers: (optional) Extra headers to sent with the request.
            Existing header keys can be overwritten.
        :param data: (optional) Dictionary
        :param debug: (optional) Overwrite of `Client.debug`
        :param cache_lifetime: (optional) The amount of seconds that the
            response has to be cached for.
        :param silent: (optional) When ``True`, any exception resulted
            from HTTP status codes or parsing will be ignored.
        :param ignore_cache: (optional) When ``True``, a previously
            cached response of the same request will be ignored.
        :param format: (optional) The type of request data to parse.
            May take the following values:
              - 'json', 'xml', ... both request data load and response are
                converted to the specified format
              - (None, 'json') a tuple, with the request data format in pos 0
                and the response format in pos 1
            defaults to 'json'
        :param delay: (option) Ensures a minimum delay of seconds between
            requests.
        :param kwargs: (optional) Arguments that will be passed to
            the `requests.request` method
        :return: :class:`Bunch` object from JSON-parsed response
        """
        if debug is None:
            debug = self.debug

        # build the request headers
        request_headers = dict(self.headers.__dict__)
        if headers is not None:
            request_headers.update(headers)

        # extract request_format and response_format from format arguments
        if type(format) in (list, tuple) and len(format) == 2:
            request_format, response_format = format
        else:
            request_format = response_format = format

        # add the 'Content-Type' header and compose data, only when:
        #   1. the content is actually sent (whatever the HTTP verb is used)
        #   2. the format is provided ('json' by default)
        if request_format and (data is not None):
            request_headers.setdefault(
                'Content-Type', formats.meta(request_format).get('content_type'))
            data = formats.compose(request_format, data)

        # form the URL
        if not hasattr(path, "encode"):
            path = '/'.join(path)
        if extension is None:
            extension = ''
        elif not extension.startswith('.'):
            extension = '.' + extension
        if suffix is None:
            suffix = ''
        url = '%s%s%s%s' % (url, path, extension, suffix)

        # log a debug message about the request
        self._log(debug_messages['request'], debug, method=method.upper(),
                  url=url, headers=request_headers, params=params, data=data)

        # check if the response for this request is cached
        cache_key = (url, str(params), str(headers))
        if self.cache.has(cache_key) and not ignore_cache:
            item = self.cache.get(cache_key)
            self._log(debug_messages['cached_response'], debug, text=item)
            return bunchify(item)

        # delay the request if needed
        if delay > 0:
            t = time.time()
            if self._last_request_time is None:
                self._last_request_time = t

            elapsed = t - self._last_request_time
            if elapsed < delay:
                time.sleep(delay - elapsed)

        # use default request parameters
        for name, value in self.defaults.items():
            kwargs.setdefault(name, value)

        # execute the request
        r = self.send_request(method, url, params=params,
                              headers=request_headers, data=data, **kwargs)
        self._last_request_time = time.time()

        # when not silent, raise an exception for any HTTP status code >= 400
        if not silent:
            r.raise_for_status()

        try:
            # parse the response into something nice
            has_body = len(r.text) > 0
            if not has_body:
                # TODO: This is set 'No response' for the debug message.
                #       Extract this into a different variable so that
                #       `parsed_response` is not ambiguous.
                parsed_response = 'No response'
            else:
                parsed_response = formats.parse(response_format, r.text)
        except ValueError as e:
            # we've failed, raise this stuff when not silent
            if len(r.text) > DEBUG_MAX_TEXT_LENGTH:
                text = r.text[:DEBUG_MAX_TEXT_LENGTH] + '...'
            else:
                text = r.text
            self._log(debug_messages['incorrect_format_response'], debug,
                      format=response_format, status_code=r.status_code,
                      reason=r.reason, text=text)
            if silent:
                return None
            raise e

        # cache the response if required
        # only GET requests are cached
        if cache_lifetime and cache_lifetime > 0 and method.lower() == 'get':
            self.cache.set(cache_key, parsed_response, cache_lifetime)

        # print out a final debug message about the response of the request
        debug_message = 'success_response' if r.status_code == 200 else \
            'failure_response'
        self._log(debug_messages[debug_message], debug,
                  status_code=r.status_code, reason=r.reason,
                  text=parsed_response)

        # return our findings and try to make it a bit nicer
        if has_body:
            return bunchify(parsed_response)
        return None


class Wrap(object):
    """Represents a part of the wrapped URL.

    You can chain this object to other Wrap objects. This is done
    *automagically* when accessing non-existing attributes of the object.

    The root of the chain should be a :class:`Client` object. When a new
    :class:`Wrap` object is created without a parent, it will create a
    new :class:`Client` object which will act as the root.
    """

    def __init__(self, part, parent=None, headers=None, params=None,
                 debug=None, cache_lifetime=None, silent=None,
                 extension=None, suffix=None, format=None, cache=None,
                 delay=None, hyphenate=False, mixedcase=False, camelcase=False,
                 formatter=None, **kwargs):
        if not hasattr(part, "encode"):
            part = str(part)
        self._part = part[:-1] if part[-1:] == '/' else part
        self._url = None
        self._parent = parent or Client(debug=debug, cache=cache, **kwargs)

        if formatter is None:
            if hyphenate:
                formatter = formatters.hyphenate
            elif mixedcase:
                formatter = formatters.mixedcase
            elif camelcase:
                formatter = formatters.camelcase

        self.config = Bunch({
            'headers': bunchify(headers) if headers else Bunch(),
            'params': bunchify(params) if params else Bunch(),
            'debug': debug,
            'cache_lifetime': cache_lifetime,
            'silent': silent,
            'extension': extension,
            'suffix': suffix,
            'format': format,
            'delay': delay,
            'formatter': formatter,
        })
        self._children = {}

    def url(self):
        if self._url:
            return self._url
        try:
            self._url = '/'.join([self._parent.url(), self._part])
        except AttributeError:
            self._url = self._part
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
        self.config.update(**options)

        if len(parts) == 0:
            return self

        parent = self
        for part in parts:
            parent = parent._get_or_create_child_wrap(part)

        return parent

    def __getattr__(self, part):
        if part in self.__dict__:
            return self.__dict__[part]

        if self.config.formatter:
            part = self.config.formatter(part)

        return self._get_or_create_child_wrap(part)

    def _get_or_create_child_wrap(self, name):
        if name not in self._children:
            self._children[name] = Wrap(
                part=name,
                parent=self,
                debug=self.config.get('debug'),
            )
        return self._children[name]

    def request(self, method, *parts, **options):
        """Requests a URL and returns a *Bunched* response.

        This method basically wraps the request method of the requests
        module and adds a `path` and `debug` option.

        :param method: The request method, e.g. 'get', 'post', etc.
        :param parts: (optional) Additional path parts to append to the URL
        :param options: (optional) Arguments that will be passed to
            the `requests.request` method
        :return: :class:`Bunch` object from JSON-parsed response
        """
        if len(parts) != 0:
            # the chain will be extended with the parts and finally a
            # request will be triggered
            return self.__call__(*parts).request(method=method, **options)

        else:
            if 'url' not in options:
                # the last part constructs the URL
                options['url'] = self.url()

            for key, value in six.iteritems(self.config):
                # set the defaults in the options
                if value is not None:
                    if isinstance(value, dict):
                        # prevents overwriting default values in dicts
                        copy = value.copy()
                        if options.get(key):
                            copy.update(options[key])
                        options[key] = copy
                    else:
                        options.setdefault(key, value)

            # at this point, we're ready to completely go down the chain
            return self._parent.request(method=method, **options)

    def get(self, *parts, **options):
        """Executes a `GET` request on the currently formed URL."""
        return self.request('get', *parts, **options)

    def post(self, *parts, **options):
        """Executes a `POST` request on the currently formed URL."""
        return self.request('post', *parts, **options)

    def put(self, *parts, **options):
        """Executes a `PUT` request on the currently formed URL."""
        return self.request('put', *parts, **options)

    def patch(self, *parts, **options):
        """Executes a `PATCH` request on the currently formed URL."""
        return self.request('patch', *parts, **options)

    def delete(self, *parts, **options):
        """Executes a `DELETE` request on the currently formed URL."""
        return self.request('delete', *parts, **options)

    def head(self, *parts, **options):
        """Executes a `HEAD` request on the currently formed URL."""
        return self.request('head', *parts, **options)

    def __repr__(self):
        return "<{} for {}>".format(self.__class__.__name__, self.url())
