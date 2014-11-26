#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import unittest

import httpretty
import tortilla
import six


API_URL = 'https://test.tortilla.locally'


class TestTortilla(unittest.TestCase):
    def setUp(self):
        self.api = tortilla.wrap(API_URL)

        httpretty.enable()

        with open('test_data.json') as resource:
            test_data = json.load(resource)

        self.endpoints = test_data['endpoints']

        for endpoint, options in six.iteritems(self.endpoints):
            if isinstance(options['body'], (dict, list, tuple)):
                body = json.dumps(options['body'])
            else:
                body = options['body']
            httpretty.register_uri(method=options.get('method', 'GET'),
                                   status=options.get('status', 200),
                                   uri=API_URL + endpoint,
                                   body=body)

    def tearDown(self):
        httpretty.disable()

    def test_json_response(self):
        jimmy = self.api.user.get('jimmy')
        jimmy_source = self.endpoints['/user/jimmy']['body']

        russian = self.api.user.get('имя')
        russian_source = self.endpoints['/user/имя']['body']

        assert jimmy == jimmy_source
        assert russian == russian_source

    def test_non_json_response(self):
        self.assertRaises(ValueError, self.api.nojson.get)
        assert self.api.nojson.get(silent=True) is None


if __name__ == '__main__':
    unittest.main()
