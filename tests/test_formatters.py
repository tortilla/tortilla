# -*- coding: utf-8 -*-

from tortilla.formatters import hyphenate, mixedcase, camelcase


def test_hyphenate(api, endpoints):
    assert 'hyphenated-endpoint' == hyphenate('hyphenated_endpoint')

    api.config.formatter = hyphenate
    assert api.hyphenated_endpoint.get() == \
        endpoints['/hyphenated-endpoint']['body']


def test_mixedcase(api, endpoints):
    assert 'mixedCasedEndpoint' == mixedcase('mixed_cased_endpoint')

    api.config.formatter = mixedcase
    assert api.mixed_cased_endpoint.get() == \
        endpoints['/mixedCasedEndpoint']['body']


def test_camelcase(api, endpoints):
    assert 'CamelCasedEndpoint' == camelcase('camel_cased_endpoint')

    api.config.formatter = camelcase
    assert api.camel_cased_endpoint.get() == \
        endpoints['/CamelCasedEndpoint']['body']
