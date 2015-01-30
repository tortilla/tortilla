# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json


class BaseCache(object):
    def has(self, key):
        return False

    def get(self, key, default=None):
        return None

    def set(self, key, value):
        pass

    def delete(self, key):
        pass


class DictCache(BaseCache):
    def __init__(self):
        self._cache = {}

    def has(self, key):
        return key in self._cache

    def get(self, key, default=None):
        if key in self._cache:
            return self._cache[key]
        return None

    def set(self, key, value):
        self._cache[key] = value

    def delete(self, key):
        del self._cache[key]


class RedisCache(BaseCache):
    def __init__(self, redis):
        self._redis = redis
        self.namespace = 'python.tortilla.cache'

    def has(self, key):
        return self._redis.hget(self.namespace, json.dumps(key)) is not None

    def get(self, key, default=None):
        value = self._redis.hget(self.namespace, json.dumps(key))
        if value is not None:
            return json.loads(value)
        return default

    def set(self, key, value):
        self._redis.hset(self.namespace, json.dumps(key), json.dumps(value))

    def delete(self, key):
        self._redis.hdel(self.namespace, json.dumps(key))
