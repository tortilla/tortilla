# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import time

import colorclass
import requests
import six

from .cache import CacheWrapper, DictCache
from .utils import formats, run_from_ipython, Bunch, bunchify


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
    'incorrect_format_response': (
        '{red}Got {status_code} {reason} (not {format}):{/red}\n'
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

    def __init__(self, debug=False, cache=None):
        self.headers = Bunch()
        self.debug = debug
        self.cache = cache if cache else DictCache()
        self.cache = CacheWrapper(self.cache)
        self.session = requests.session()
        self._last_request_time = None

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

    def request(self, method, url, path=(), extension=None, params=None,
                headers=None, data=None, debug=None, cache_lifetime=None,
                silent=False, ignore_cache=False, format='json', delay=0.0,
                **kwargs):
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

        # extract req_format and resp_format from format arguments
        if type(format) in (list, tuple) and len(format) == 2:
            req_format = format[0]
            resp_format = format[1]
        else:
            req_format = resp_format = format

        # add Content-Type header & compose data, only when
        # 1. content is actually sent (whatever the HTTP verb is used)
        # 2. format is provided ('json' by default)
        if req_format and (data is not None):
            request_headers.setdefault(
                'Content-Type', formats.meta(req_format).get('content_type'))
            data = formats.compose(req_format, data)

        # form the URL
        if not hasattr(path, "encode"):
            path = '/'.join(path)
        if extension is None:
            extension = ''
        elif not extension.startswith('.'):
            extension = '.' + extension
        url = '%s%s%s' % (url, path, extension)

        # log a debug message about the request we're about to make
        self._log(debug_messages['request'], debug, method=method.upper(),
                  url=url, headers=request_headers, params=params, data=data)

        # actually, check if we have something in the cache that's valid
        cache_key = (url, str(params), str(headers))
        if self.cache.has(cache_key) and not ignore_cache:
            item = self.cache.get(cache_key)
            self._log(debug_messages['cached_response'], debug, text=item)
            return bunchify(item)

        # delay if needed
        if delay > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < delay:
                time.sleep(delay - elapsed)

        # execute the request
        r = self.session.request(method, url, params=params,
                                 headers=request_headers, data=data, **kwargs)
        self._last_request_time = time.time()

        # when not silent, raise an exception for any status code >= 400
        if not silent:
            r.raise_for_status()

        try:
            # parse the response into something nice
            has_body = len(r.text) > 0
            if not has_body:
                parsed_response = 'No response'
            else:
                parsed_response = formats.parse(resp_format, r.text)
        except ValueError as e:
            # we've failed, raise this stuff when not silent
            if len(r.text) > DEBUG_MAX_TEXT_LENGTH:
                text = r.text[:DEBUG_MAX_TEXT_LENGTH] + '...'
            else:
                text = r.text
            self._log(debug_messages['incorrect_format_response'], debug,
                      format=resp_format, status_code=r.status_code,
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
                 debug=None, cache_lifetime=None, silent=False,
                 extension=None, format=None, cache=None, delay=None):
        if not hasattr(part, "encode"):
            part = str(part)
        self._part = part[:-1] if part[-1:] == '/' else part
        self._url = None
        self._parent = parent or Client(debug=debug, cache=cache)
        self.config = Bunch({
            'headers': bunchify(headers) if headers else Bunch(),
            'params': bunchify(params) if params else Bunch(),
            'debug': debug,
            'cache_lifetime': cache_lifetime,
            'silent': silent,
            'extension': extension,
            'format': format,
            'delay': delay,
        })

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
                                       debug=self.config.get('debug'))
            return self.__dict__[part]

    def request(self, method, *parts, **options):
        """Requests a URL and returns a *Bunched* response.

        This method basically wraps the request method of the requests
        module and adds a `path` and `debug` option.

        :param method: The request method, e.g. 'get', 'post', etc.
        :param part: (optional) A primary key to append to the path
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
