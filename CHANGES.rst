Tortilla Changelog
==================

Version 0.5.0
-------------

Unreleased.

- Hyphenated, mixedCased, and CamelCased endpoints can be more easily
  requested using the `hyphenate`, `mixedcase`, and `camelcase` option
  (`#44`_, `#10`_)
- Retry request when catching a connection reset error (`#40`_)
- It is now possible to request endpoints that collide with `Wrap`
  attributes such as `config` (See discussion in `#38`_)
- Extra kwargs in `tortilla.wrap()` are eventually passed to the
  requests package, enabling many new features such as HTTPBasicAuth
  (`#37`_)

.. _#44: https://github.com/tortilla/tortilla/issues/44
.. _#40: https://github.com/tortilla/tortilla/pull/40
.. _#38: https://github.com/tortilla/tortilla/pull/38
.. _#37: https://github.com/tortilla/tortilla/pull/37
.. _#10: https://github.com/tortilla/tortilla/issues/10

Version 0.4.3
-------------

Released on April 6th 2018.

- Correct default value for silent parameter (`#36`_)
- Add tox configuration (`#34`_)
- Update link to docs (`#33`_)
- Increases code coverage (`#31`_)
- Add support for URL "suffix" to access certain APIs that, eg, uses
  trailing-slashes at URLs (`#30`_)
- Replaces colorclass with colorama, fixed (`#28`_)

.. _#36: https://github.com/tortilla/tortilla/issues/36
.. _#34: https://github.com/tortilla/tortilla/pull/34
.. _#33: https://github.com/tortilla/tortilla/pull/33
.. _#31: https://github.com/tortilla/tortilla/pull/31
.. _#30: https://github.com/tortilla/tortilla/pull/30
.. _#28: https://github.com/tortilla/tortilla/issues/28

Version 0.4.2
-------------

Released on May 18th 2016. Changes by `@osantana`_ in `#29`_.

- Formatting code to make it more PEP-8 compliant
- Simplify py2/3 compatibility code (remove compat module)
- Enable/disable httpretty in setUp/tearDown methods in tests to make
  it works with all kind of test runners (like PyCharm test runner or
  nose)
- Refactor ``run_from_ipython()`` implementation to make it pass static
  code analysis test (warns for missing ``__IPYTHON__``)
- Fix an issue with ``delay`` code when it was called for the first
  time and ``self._last_request_time`` is ``None``

.. _@osantana: https://github.com/osantana
.. _#29: https://github.com/tortilla/tortilla/pull/29

Version 0.4.1
-------------

Released on April 29th 2015.

- Fixes `#25`_
- Adds the ability to define different formats for request and response
  data (`#24`_)

.. _#25: https://github.com/tortilla/tortilla/issues/25
.. _#24: https://github.com/tortilla/tortilla/pull/24

Version 0.4.0
-------------

Released on February 11th 2015.

- Added support for multiple response formats
- Persistent URL query params
- New delay option in Wrap class
- Exception can be raised on HTTP error

Version 0.3.0
-------------

Released on December 12th 2014.

- Added support for cookies by using requests sessions

Version 0.2.0
-------------

Released on December 7th 2014.

- Execute HTTP HEAD requests on endpoints (responses from endpoints are
  now optional, ``None`` will be returned if there's no response body)
- Multiple parts can be defined when calling an attribute (e.g.
  ``api.books(book_id, author_id)``)
