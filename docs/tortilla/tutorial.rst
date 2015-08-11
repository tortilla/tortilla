Intro
~~~~~

Tortilla is a Python library to interface with web APIs in Python scripts.

Using Tortilla can be divided into four stages; the wrapping stage, the
endpoint stage, the request stage and the response stage. We will go over the
basics of each of these stages in this tutorial.

Ultimately, we're going to request the following *fictional* endpoint::

    https://api.example.org/animals/dodo

Which will respond with the following JSON-encoded data::

    {"name": "Dodo", "status": "Extinct"}

It is assumed that Tortilla is imported in the subsequent code blocks::

    import tortilla

The wrapping stage
~~~~~~~~~~~~~~~~~~

Tortilla needs to know at least the API's base URL from which all the endpoints
emerge. This can be provided at the wrapping stage; the first sign of life
of your fresh gluten-free API wrap. After the Tortilla library is included,
the following code will take care of the wrapping::

    api = tortilla.wrap('https://api.example.org')

Now, there are a bunch of other options that can be defined here, but we'll
look into that later.

The endpoint stage
~~~~~~~~~~~~~~~~~~

At this point, we will chain together the parts of the endpoint we want to
request and receive data from. Parts are basically the sections in between the
directory separators. They can be dynamic and static. In this tutorial, we're
going request an endpoint which returns information about animals::

    animal = api.animals('dodo')

What did this do? First of all, the ``api`` wrap works a bit magically.
It creates sub-wraps whenever non-existing attributes are accessed. These
sub-wraps then represent a part of the URL, ``.animal`` represents ``/animals``
in this case.

A sub-wrap also accepts multiple extra parts to append to the URL, as seen
in the example. These are also wraps, but they're dynamically created.

So, right now we have added ``.animals('dodo')`` which will give us
``/animals/dodo``.

The request stage
~~~~~~~~~~~~~~~~~

We could chain endpoints forever until the sun stops burning, but at one point
we would want to have some interaction with a server as a client;
make a request.

Tortilla supports all HTTP request methods, but six of those have a dedicated
function; ``get``, ``post``, ``put``, ``patch``, ``delete``, and ``head``.
For others, `~Wrap.request` can be used.

Once we have formed the endpoint we want to request, we will execute the
request using one of the previously mentioned functions::

    dodo = api.animals.get('dodo')

.. note:: Scratching your head? Aren't these functions a bit ambigious in
    combination with these magic attributes? Yes, they are. If you come across
    an endpoint that expects one of these words in the path, it is advised to
    use a dynamic sub-wrap; something like ``api('get').get()``.

The response stage
~~~~~~~~~~~~~~~~~~
