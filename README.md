Tortilla
========

[<img src="https://img.shields.io/travis/redodo/tortilla.svg?style=flat">](https://travis-ci.org/redodo/tortilla)
[<img src="https://img.shields.io/coveralls/redodo/tortilla.svg?style=flat">](https://coveralls.io/r/redodo/tortilla)
[<img src="https://readthedocs.org/projects/tortilla/badge/?version=latest&style=flat">](https://tortilla.readthedocs.org/latest/)
[<img src="https://img.shields.io/pypi/v/tortilla.svg?style=flat">](https://pypi.python.org/pypi/tortilla)
[<img src="https://pypip.in/py_versions/tortilla/badge.svg?style=flat">](https://pypi.python.org/pypi/tortilla)
[<img src="https://img.shields.io/pypi/l/tortilla.svg?style=flat">](https://github.com/redodo/tortilla/blob/master/LICENSE)

*Wrapping web APIs made easy.*

Tortilla has all the required features built in to interface with a web
API. It's aimed to be as pythonic and intuitive as possible.

Installation via PIP:

```bash
pip install tortilla
```

Quick usage overview:

```python
>>> import tortilla
>>> github = tortilla.wrap('https://api.github.com')
>>> u = github.users.get('octocat')
>>> u.location
u'San Francisco'
```

Wrapping APIs
-------------

Let's say we want to wrap the following API url:

```python
https://api.example.org
```

Wrapping it with Tortilla is easy:

```python
import tortilla
api = tortilla.wrap('https://api.example.org')
```

In the background this created a `Wrap` object which can be chained to
other `Wrap` objects. Each Wrap represents a part of a URL. This means
that we could do the following thing with our created wrapper:

```python
latest_news = api.news.latest.get()
# GET https://api.example.org/news/latest
#     |---------Wrap---------|Wrap|-Wrap-|
```

In this example, we've chained three Wraps together to form a URL. At
the end of the chain we invoked the `get` method. This could be one of
these HTTP methods: `get`, `post`, `put`, `patch` or `delete`. Tortilla
will then execute the request and parse the response. At the moment only
JSON responses will be parsed.

When the response was parsed successfully, Tortilla will *bunchify* the
data so it's accessible via attributes and keys. For example:
`news['meta']['views']` can be: `news.meta.views`, but both will work.

Headers
-------

You can optionally pass different headers to each request:

```python
latest_news = api.news.latest.get(headers={'token': 'not so secret'})
```

If a header is recurring at every request (like authentication tokens)
you can set them in one of the Wrap objects:

```python
api.headers.token = 'not so secret'
latest_news = api.news.latest.get()
```

Sub-wraps will overload settings from parent-wraps. So every Wrap under
`api` will have the `'token': 'not so secret'` header by default.

Caching
-------

Sometimes you can have request limits on an API. In these cases, caching
can be very helpful. You can activate this with the `cache_lifetime`
parameter:

```python
api = tortilla.wrap('https://api.example.org', cache_lifetime=100)  # seconds
```

All the requests made on this Wrap will now be cached for 100 seconds.
If you want to ignore the cache in a specific instance, you can use the
`ignore_cache` parameter:

```python
api.special.request.get(ignore_cache=True)
```

The response will now be reloaded.

URL Extensions
--------------

APIs like Twitter's require an extension in the URL that specifies the
formatting type. This can be defined in the `extension` parameter:

```python
api = tortilla.wrap('https://api.twitter.com/1.1', extension='json')
```

Again, this can be overridden for every sub-wrap or request.

*Enjoy your data.*
