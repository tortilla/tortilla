# -*- coding: utf-8 -*-

from time import time

try:
    import simplejson as json
except ImportError:
    import json


class CacheWrapper(object):
    def __init__(self, cache):
        self.cache = cache

    def has(self, key):
        data = self.cache.get(key)
        return data and time() < data['expires_on']

    def get(self, key, default=None):
        if self.has(key):
            return self.cache.get(key)['value']
        return default

    def set(self, key, value, lifetime=60):
        return self.cache.set(key, {'value': value,
                                    'expires_on': time() + lifetime})

    def delete(self, key):
        return self.cache.delete(key)

    def clear(self):
        return self.cache.clear()


class BaseCache(object):
    def has(self, key):
        return False

    def get(self, key, default=None):
        return None

    def set(self, key, value):
        pass

    def delete(self, key):
        pass

    def clear(self):
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

    def set(self, key, value,):
        self._cache[key] = value

    def delete(self, key):
        del self._cache[key]

    def clear(self):
        self._cache.clear()


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

    def clear(self):
        self._redis.delete(self.namespace)
