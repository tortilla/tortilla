#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
import json
import time
import unittest

import httpretty
from requests.exceptions import HTTPError

import tortilla
from tortilla.utils import bunchify, Bunch, run_from_ipython


API_URL = 'https://test.tortilla.locally'


def monkey_patch_httpretty():
    # HTTPretty decodes unicode strings before passing them to the
    # `quote` method of `urllib`. On Python 2, this can cause KeyErrors
    # when the string contains unicode. To prevent this, we encode the
    # string so urllib can safely quote it.
    from httpretty.core import url_fix

    def fixed_url_fix(s, charset='utf-8'):
        return url_fix(s.encode(charset), charset)

    httpretty.core.url_fix = fixed_url_fix


if sys.version_info[0] == 2:
    monkey_patch_httpretty()


class TestTortilla(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # this is a special endpoint which loops through responses,
        # very useful to test the cache
        httpretty.register_uri(
            httpretty.GET, API_URL + '/cache',
            responses=[
                httpretty.Response(body='"cache this response"'),
                httpretty.Response(body='"this should not be returned"'),
            ]
        )

        with open('test_data.json') as resource:
            test_data = json.load(resource)

        cls.endpoints = test_data['endpoints']

        for endpoint, options in cls.endpoints.items():
            if isinstance(options.get('body'), (dict, list, tuple)):
                body = json.dumps(options.get('body'))
            else:
                body = options.get('body')

            httpretty.register_uri(method=options.get('method', 'GET'),
                                   status=options.get('status', 200),
                                   uri=API_URL + endpoint,
                                   body=body)

    def setUp(self):
        httpretty.enable()
        self.api = tortilla.wrap(API_URL)

    def tearDown(self):
        httpretty.disable()

    def _time_function(self, func, *args, **kwargs):
        """Returns the time it took for a function to execute."""
        start = time.time()
        func(*args, **kwargs)
        return time.time() - start

    def test_json_response(self):
        self.assertEqual(self.api.user.get('jimmy'),
                         self.endpoints['/user/jimmy']['body'])
        self.assertEqual(self.api.user.get('имя'),
                         self.endpoints['/user/имя']['body'])
        self.assertEqual(self.api.has_self.get(),
                         self.endpoints['/has_self']['body'])

    def test_non_json_response(self):
        with self.assertRaises(ValueError):
            self.api.nojson.get()
        self.assertIsNone(self.api.nojson.get(silent=True))

    def test_formed_urls(self):
        self.assertEquals(self.api.this.url(), API_URL + '/this')
        self.assertEquals(self.api('this').url(), API_URL + '/this')
        self.assertEquals(self.api.this('that').url(), API_URL + '/this/that')
        self.assertEquals(self.api('this')('that').url(), API_URL + '/this/that')
        self.assertEquals(self.api.user('имя').url(), API_URL + '/user/имя')
        self.assertEquals(self.api('hello', 'world').url(), API_URL + '/hello/world')
        self.assertEquals(self.api('products', 123).url(), API_URL + '/products/123')

        trailing_slash_api = tortilla.wrap(API_URL + '/')
        self.assertEquals(trailing_slash_api.endpoint.url(), API_URL + '/endpoint')

    def test_cached_response(self):
        self.api.cache.get(cache_lifetime=100)
        self.assertEquals(self.api.cache.get(), "cache this response")

        self.api.cache.get(cache_lifetime=0.25, ignore_cache=True)
        time.sleep(0.5)
        self.assertEquals(self.api.cache.get(), "this should not be returned")

    def test_request_delay(self):
        self.api.config.delay = 0.5
        self.api.test.get()
        self.assertGreaterEqual(self._time_function(self.api.test.get), 0.5)
        self.assertGreaterEqual(self._time_function(self.api.test.get, delay=0.1), 0.1)
        self.assertGreaterEqual(self._time_function(self.api.test.get), 0.5)

        # do not delay the rest of the tests
        self.api.config.delay = 0

    def test_request_methods(self):
        self.assertEquals(self.api.awesome.tweet.post().message, "Success!")
        self.assertEquals(self.api.cash.money.put().message, "Success!")
        self.assertEquals(self.api.windows.ssh.patch().message, "Success!")
        self.assertEquals(self.api.world.hunger.delete().message, "Success!")
        self.assertIsNone(self.api.another.test.head())

    def test_extensions(self):
        self.assertEquals(self.api.extension.hello.get(extension='json').message, 'Success!')
        self.assertEquals(self.api.extension.hello.get(extension='.json').message, 'Success!')

    def test_wrap_config(self):
        self.api.stuff(debug=True, extension='json', cache_lifetime=5, silent=True)
        self.assertTrue(self.api.stuff.config.debug)
        self.assertEquals(self.api.stuff.config.extension, 'json')
        self.assertEquals(self.api.stuff.config.cache_lifetime, 5)
        self.assertTrue(self.api.stuff.config.silent)

        self.api.stuff(debug=False, extension='xml', cache_lifetime=8, silent=False)
        self.assertFalse(self.api.stuff.config.debug)
        self.assertEquals(self.api.stuff.config.extension, 'xml')
        self.assertEquals(self.api.stuff.config.cache_lifetime, 8)
        self.assertFalse(self.api.stuff.config.silent)

        self.api.stuff('more', 'stuff', debug=True)
        self.assertTrue(self.api.stuff.config.debug)

    def test_wrap_chain(self):
        self.assertIs(self.api.chained.wrap.stuff, self.api('chained').wrap('stuff'))
        self.assertIs(self.api.more.chaining.stuff, self.api.more('chaining')('stuff'))
        self.assertIsNot(self.api('expert/chaining/stuff'), self.api.expert.chaining.stuff)
        self.assertIs(self.api('hello', 'world'), self.api.hello.world)
        self.assertIs(self.api('products', 123), self.api.products(123))

    def test_debugging(self):
        self.api.user.get('имя', debug=True)

    def test_response_exceptions(self):
        with self.assertRaises(HTTPError):
            self.api.status_404.get()

        with self.assertRaises(HTTPError):
            self.api.status_500.get()

        try:
            self.api.status_404.get(silent=True)
            self.api.status_500.get(silent=True)
        except HTTPError:
            self.fail("Wrap.get() raised an unexpected HTTPError while being "
                      "told to be silent!")

    def test_bunchify_sequence_objects(self):
        bunch = bunchify([{"a": 1}, {"b": 2}])
        self.assertIsInstance(bunch[0], Bunch)

    def test_run_from_ipython(self):
        self.assertEqual(getattr(__builtins__, "__IPYTHON__", False),
                         run_from_ipython())


if __name__ == '__main__':
    unittest.main()
