#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import time
import unittest

import httpretty
import tortilla
import six


def monkey_patch_httpretty():
    # HTTPretty decodes unicode strings before passing them to the
    # `quote` method of `urllib`. On Python 2, this can cause KeyErrors
    # when the string contains unicode. To prevent this, we encode the
    # string so urllib can safely quote it.
    from httpretty.core import url_fix
    def fixed_url_fix(s, charset='utf-8'):
        return url_fix(s.encode(charset), charset)
    httpretty.core.url_fix = fixed_url_fix


from tortilla.compat import is_py2
if is_py2:
    monkey_patch_httpretty()


API_URL = 'https://test.tortilla.locally'
api = tortilla.wrap(API_URL)


def register_urls(endpoints):
    for endpoint, options in six.iteritems(endpoints):
        if isinstance(options.get('body'), (dict, list, tuple)):
            body = json.dumps(options.get('body'))
        else:
            body = options.get('body')
        print(body, endpoint)
        httpretty.register_uri(method=options.get('method', 'GET'),
                               status=options.get('status', 200),
                               uri=API_URL + endpoint,
                               body=body)


with open('test_data.json') as resource:
    test_data = json.load(resource)
endpoints = test_data['endpoints']
register_urls(endpoints)


httpretty.register_uri(
    httpretty.GET, API_URL + '/cache',
    responses=[
       httpretty.Response(body='"cache this response"'),
       httpretty.Response(body='"this should not be returned"'),
    ]
)


class TestTortilla(unittest.TestCase):

    def test_json_response(self):
        assert api.user.get('jimmy') == endpoints['/user/jimmy']['body']
        assert api.user.get('имя') == endpoints['/user/имя']['body']

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

    def test_cached_response(self):
        api.cache.get(cache_lifetime=100)
        assert api.cache.get() == "cache this response"
        api.cache.get(cache_lifetime=0.25, ignore_cache=True)
        time.sleep(0.5)
        assert api.cache.get() == "this should not be returned"

    def test_request_methods(self):
        assert api.awesome.tweet.post().message == "Success!"
        assert api.cash.money.put().message == "Success!"
        assert api.windows.ssh.patch().message == "Success!"
        assert api.world.hunger.delete().message == "Success!"
        assert api.another.test.head() is None

    def test_wrap_config(self):
        api.stuff(debug=True, extension='json', cache_lifetime=5, silent=True)
        assert api.stuff.debug
        assert api.stuff.extension == 'json'
        assert api.stuff.cache_lifetime == 5
        assert api.stuff.silent
        api.stuff(debug=False, extension='xml', cache_lifetime=8, silent=False)
        assert not api.stuff.debug
        assert api.stuff.extension == 'xml'
        assert api.stuff.cache_lifetime == 8
        assert not api.stuff.silent

    def test_wrap_chain(self):
        assert api.chained.wrap.stuff is api('chained').wrap('stuff')
        assert api.more.chaining.stuff is api.more('chaining')('stuff')
        assert api.more is api.more.chaining.parent
        assert api('expert/chaining/stuff') is not api.expert.chaining.stuff

    def test_debugging(self):
        api.user.get('имя', debug=True)


if __name__ == '__main__':
    httpretty.enable()
    unittest.main()
    httpretty.disable()
