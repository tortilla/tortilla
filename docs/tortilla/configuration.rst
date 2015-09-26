.. _configuration:

Configuration
=============

Design
------

There are several important aspects of Tortilla's handling of configuration,
which are meant to make it easy to use, but also very dynamic and powerful.

For one, configuration is cascading. Settings of subordinate
:class:`wrappers.Wrap` objects are automatically overloaded with their
parents' configuration.

Secondly, the various options accepted by the :meth:`wrappers.Client.request`
method are available in the configuration of :class:`wrappers.Wrap` objects
and passed to this method when a request is made.

Options
-------

The following options can be set in the configuration of each
:data:`wrappers.Wrap.config` object:

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

======================= ======================================================
``debug``               Enable or disable verbose requests and responses.
``delay``               Add a delay between the execution of requests. The
                        time between the second request and the first request
                        will be substracted from this parameter.
``headers``             Persistent headers to send with each request.
``params``              Persistent query parameters to send with each request.
``format``              The format or content type of the request and response
                        data. This can be either type :py:class:`str`.
                        :py:class:`tuple` or :py:class:`list`.
``cache_lifetime``      The amount of time to hold cached responses.
======================= ======================================================
