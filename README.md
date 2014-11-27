Tortilla
========

[<img src="https://travis-ci.org/redodo/tortilla.svg">](https://travis-ci.org/redodo/tortilla)

Wrapping web APIs made easy.

Installation:

```bash
pip install --pre tortilla
```


Quick usage:

```python
>>> import tortilla
>>> github = tortilla.wrap('https://api.github.com')
>>> redodo = github.users.get('redodo')
>>> redodo.id
2227416
```


Intro
-----

In the following examples we can assume that the following code is already
executed:

```python
import tortilla
api = tortilla.wrap('https://api.example.org')
```


Tortilla 101
------------

A quick overview of Tortilla's flow:

1. You form a chain of URL parts
2. You invoke a `get`, `post`, `patch`, `put` or `delete` method at the end of the chain
3. Tortilla requests the URL
4. Tortilla tries to JSON decode to response and puts it in a `Bunch` object (dictionary accessible via dots)
5. Tortilla returns the *bunched* object


Headers
-------

Most APIs require a authentication token before you can access its endpoints.

Those can be set in the headers of a wrapped object:

```python
api.headers.token = 'super secret token'
```

Or if you first need to login before getting a token:

```python
auth = api.auth.post(data={'username': 'foo', 'password': 'bar'})
api.headers.token = auth.token
```

If the header key contains a dot or is a reserved keyword you can use the
key instead of the attribute:

```python
api.headers['from'] = 'stuff'
api.headers['secret.key'] = 'more stuff'
```


Caching
-------

Caching stuff is easy:

```python
api.cache_lifetime = 3600  # seconds
# OR
api = tortilla.wrap('https://api.example.org', cache_lifetime=3600)
```

If you want to ignore the cache and force a reload:

```python
api.some.endpoint.get(ignore_cache=True)
```


URL Extensions
--------------

If the endpoints of your target API require an extension for the response
formatting you can set the `extension` parameter:

```python
api.extension = 'json'
# OR
api = tortilla.wrap('https://api.example.org', extension='json')
```

This can be overwritten per request or URL part:

```python
api.special.case(extension='json')
api.special.case.stuff.get()
# requests: https://api.example.org/special/case/stuff.json
```
