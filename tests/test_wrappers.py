# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import time 

import pytest
from requests.exceptions import HTTPError

from tortilla.utils import Bunch, bunchify, run_from_ipython


def time_function(fn, *args, **kwargs):
    t1 = time.time()
    fn(*args, **kwargs)
    t2 = time.time()
    return t2 - t1


def test_json_response(api, endpoints):
    assert api.user.get('jimmy') == endpoints['/user/jimmy']['body']
    assert api.user.get('имя') == endpoints['/user/имя']['body']
    assert api.has_self.get() == endpoints['/has_self']['body']


def test_non_json_response(api):
    with pytest.raises(ValueError):
        api.nojson.get()
    assert api.nojson.get(silent=True) is None


def test_cached_response(api):
    api.cache.get(cache_lifetime=100)
    assert api.cache.get() == "the first response"
    assert api.cache.get() == "the first response"

    api.cache.get(cache_lifetime=0.25, ignore_cache=True)
    assert api.cache.get() == "the second response"
    assert api.cache.get() == "the second response"


def test_request_delay(api):
    api.config.delay = 0.2
    assert time_function(api.test.get) >= 0.2
    assert time_function(api.test.get, delay=0.1) >= 0.1
    assert time_function(api.test.get) >= 0.2


def test_request_methods(api):
    assert api.put_endpoint.put().message == "Success!"
    assert api.post_endpoint.post().message == "Success!"
    assert api.patch_endpoint.patch().message == "Success!"
    assert api.delete_endpoint.delete().message == "Success!"
    assert api.head_endpoint.head() is None


def test_extensions(api):
    assert api.extension.hello.get(extension='json').message == "Success!"
    assert api.extension.hello.get(extension='.json').message == "Success!"


def test_wrap_config(api):
    api.endpoint(debug=True, silent=True, extension='json', cache_lifetime=5)
    assert api.endpoint.config.debug
    assert api.endpoint.config.silent
    assert api.endpoint.config.extension == 'json'
    assert api.endpoint.config.cache_lifetime == 5

    api.endpoint(debug=False, silent=False, extension='xml', cache_lifetime=8)
    assert not api.endpoint.config.debug
    assert not api.endpoint.config.silent
    assert api.endpoint.config.extension == 'xml'
    assert api.endpoint.config.cache_lifetime == 8


def test_wrap_chaining(api):
    assert api.one.two.three is api('one').two('three')
    assert api.one.two.three is api.one('two')('three')
    assert api.one.two.three is api('one', 'two').three
    assert api.one.two.three is api('one', 'two', 'three')

    assert api.one(2) is api('one', 2)

    assert api.one.two.three is not api('one/two/three')


def test_response_exceptions(api):
    with pytest.raises(HTTPError):
        api.status_404.get()
    with pytest.raises(HTTPError):
        api.status_500.get()

    api.status_404.get(silent=True)
    api.status_500.get(silent=True)


def test_bunchify():
    bunch = bunchify([{'a': 1}, {'b': 2}])
    assert isinstance(bunch[0], Bunch)


def test_run_from_ipython():
    assert getattr(__builtins__, '__IPYTHON__', False) == run_from_ipython()


def test_config_endpoint(api, endpoints):
    assert api.get('config') == endpoints['/config']['body']
    assert api('config').get() == endpoints['/config']['body']
