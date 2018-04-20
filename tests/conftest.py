# -*- coding: utf-8 -*-

import json
import os
import sys

import httpretty
import pytest

import tortilla


API_URL = 'http://test.tortilla.locally'
TESTS_DIR = os.path.dirname(__file__)


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


# this is a special endpoint which loops through responses,
# very useful to test the cache
httpretty.register_uri(
    httpretty.GET, API_URL + '/cache',
    responses=[
        httpretty.Response(body='"the first response"'),
        httpretty.Response(body='"the second response"'),
    ]
)


@pytest.fixture(scope='session')
def endpoints():
    httpretty.enable()
    with open(os.path.join(TESTS_DIR, 'endpoints.json')) as resource:
        test_data = json.load(resource)

    endpoints = test_data['endpoints']

    for endpoint, options in endpoints.items():
        if isinstance(options.get('body'), (dict, list, tuple)):
            body = json.dumps(options.get('body'))
        else:
            body = options.get('body')

        httpretty.register_uri(method=options.get('method', 'GET'),
                               status=options.get('status', 200),
                               uri=API_URL + endpoint,
                               body=body)
    yield endpoints
    httpretty.disable()


@pytest.fixture
def api():
    return tortilla.wrap(API_URL)
