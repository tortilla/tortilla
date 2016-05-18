#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
import json
import time
import unittest

import httpretty
import six
from requests.exceptions import HTTPError

import tortilla


def monkey_patch_httpretty():
    # HTTPretty decodes unicode strings before passing them to the
    # `quote` method of `urllib`. On Python 2, this can cause KeyErrors
    # when the string contains unicode. To prevent this, we encode the
    # string so urllib can safely quote it.
    from httpretty.core import url_fix

    def fixed_url_fix(s, charset='utf-8'):
        return url_fix(s.encode(charset), charset)

    httpretty.core.url_fix = fixed_url_fix


if sys.version[0] == 2:
    monkey_patch_httpretty()


API_URL = 'https://test.tortilla.locally'
api = tortilla.wrap(API_URL)


def register_urls(urls):
    for endpoint, options in six.iteritems(urls):
        if isinstance(options.get('body'), (dict, list, tuple)):
            body = json.dumps(options.get('body'))
        else:
            body = options.get('body')
        httpretty.register_uri(method=options.get('method', 'GET'),
                               status=options.get('status', 200),
                               uri=API_URL + endpoint,
                               body=body)


with open('test_data.json') as resource:
    test_data = json.load(resource)
endpoints = test_data['endpoints']
register_urls(endpoints)

# this is a special endpoint which loops through responses,
# very useful to test the cache
httpretty.register_uri(
    httpretty.GET, API_URL + '/cache',
    responses=[
        httpretty.Response(body='"cache this response"'),
        httpretty.Response(body='"this should not be returned"'),
    ]
)


def time_function(func, *args, **kwargs):
    """Returns the time it took for a function to execute."""
    start = time.time()
    func(*args, **kwargs)
    return time.time() - start


class TestTortilla(unittest.TestCase):
    def setUp(self):
        httpretty.enable()

    def tearDown(self):
        httpretty.disable()

    def test_json_response(self):
        assert api.user.get('jimmy') == endpoints['/user/jimmy']['body']
        assert api.user.get('имя') == endpoints['/user/имя']['body']
        assert api.has_self.get() == endpoints['/has_self']['body']

    def test_non_json_response(self):
        self.assertRaises(ValueError, api.nojson.get)
        assert api.nojson.get(silent=True) is None

    def test_formed_urls(self):
        assert api.this.url() == API_URL + '/this'
        assert api('this').url() == API_URL + '/this'
        assert api.this('that').url() == API_URL + '/this/that'
        assert api('this')('that').url() == API_URL + '/this/that'
        assert api.user('имя').url() == API_URL + '/user/имя'
        trailing_slash_api = tortilla.wrap(API_URL + '/')
        assert trailing_slash_api.endpoint.url() == API_URL + '/endpoint'
        assert api('hello', 'world').url() == API_URL + '/hello/world'
        assert api('products', 123).url() == API_URL + '/products/123'

    def test_cached_response(self):
        api.cache.get(cache_lifetime=100)
        assert api.cache.get() == "cache this response"
        api.cache.get(cache_lifetime=0.25, ignore_cache=True)
        time.sleep(0.5)
        assert api.cache.get() == "this should not be returned"

    def test_request_delay(self):
        api.config.delay = 0.5
        api.test.get()
        assert time_function(api.test.get) >= 0.5
        assert time_function(api.test.get, delay=0.1) >= 0.1
        assert time_function(api.test.get) >= 0.5
        # do not delay the rest of the tests
        api.config.delay = 0

    def test_request_methods(self):
        assert api.awesome.tweet.post().message == "Success!"
        assert api.cash.money.put().message == "Success!"
        assert api.windows.ssh.patch().message == "Success!"
        assert api.world.hunger.delete().message == "Success!"
        assert api.another.test.head() is None

    def test_extensions(self):
        assert api.extension.hello.get(extension='json').message == 'Success!'
        assert api.extension.hello.get(extension='.json').message == 'Success!'

    def test_wrap_config(self):
        api.stuff(debug=True, extension='json', cache_lifetime=5, silent=True)
        assert api.stuff.config.debug
        assert api.stuff.config.extension == 'json'
        assert api.stuff.config.cache_lifetime == 5
        assert api.stuff.config.silent
        api.stuff(debug=False, extension='xml', cache_lifetime=8, silent=False)
        assert not api.stuff.config.debug
        assert api.stuff.config.extension == 'xml'
        assert api.stuff.config.cache_lifetime == 8
        assert not api.stuff.config.silent
        api.stuff('more', 'stuff', debug=True)
        assert api.stuff.config.debug

    def test_wrap_chain(self):
        assert api.chained.wrap.stuff is api('chained').wrap('stuff')
        assert api.more.chaining.stuff is api.more('chaining')('stuff')
        assert api('expert/chaining/stuff') is not api.expert.chaining.stuff
        assert api('hello', 'world') is api.hello.world
        assert api('products', 123) is api.products(123)

    def test_debugging(self):
        api.user.get('имя', debug=True)

    def test_response_exceptions(self):
        self.assertRaises(HTTPError, api.status_404.get)
        self.assertRaises(HTTPError, api.status_500.get)
        try:
            api.status_404.get(silent=True)
            api.status_500.get(silent=True)
        except HTTPError:
            self.fail("Wrap.get() raised an unexpected HTTPError while being "
                      "told to be silent!")


if __name__ == '__main__':
    unittest.main()
