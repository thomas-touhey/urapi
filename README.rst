``urapi`` -- your API for User Registration
===========================================

``urapi`` (**U**\ ser **R**\ egistration **API**, pronounced "your API") is
a simple user registration API made for demonstration purposes.

The project targets Python 3, and depends on PostgreSQL_ and an SMTP server
being present and usable. A Docker_ setup is available to test, see
:ref:`guide-docker` for more information.

The following sections are organized following `Diátaxis`_.

Getting started
---------------

The following subsections are how-to guides on how to accomplish given tasks
with or using ``urapi``.

Running ``urapi`` with Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to run ``urapi`` with Docker, you must run the following command:

.. code-block:: bash

    docker compose -f docker/docker-compose.yaml up

This command will occupy your terminal, and display the logs as the API
is running. Once you are done running the stack, you can stop the machines by
doing Ctrl+C.

While the stack is running, the following ports will be exposed on your
machine once all services are run:

``localhost:1080``
    Web interface for MailCatcher_, an SMTP server that presents all
    e-mails sent by the API. You can go to `http://localhost:1080/
    <http://localhost:1080/>`_ to view them, which is used during the tests.

``localhost:5432``
    PostgreSQL server used by the API. The API uses it to store its data
    in the ``urapi`` database, using the ``postgres`` account (password:
    ``postgres``).

    For debug purposes, you can access the database using psql_:

    .. code-block:: bash

        PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres urapi

    All tables are present in the ``public`` (default) schema.

``localhost:8080``
    API server. You can access the OpenAPI web interface over at
    `localhost:8080/docs <http://localhost:8080/docs>`_.

The following sections assume you are running the stack with Docker.

Registering a user
~~~~~~~~~~~~~~~~~~

In order to register a user using the API, the steps are the following:

1. Create the user, by issuing a ``POST http://localhost:8080/v1/users``
   request with the following JSON payload:

   .. code-block:: json

       {
           "email_address": "your@email.example",
           "password": "your.password"
       }

   If the request has succeeded, you should have obtained the **201** HTTP
   status code.
2. Obtain your code, which has been sent over SMTP.

   In order to do this, go on the MailCatcher instance at
   `http://localhost:1080/ <http://localhost:1080/>`_, and click on the last
   received e-mail.
3. Validate your account, by issuing a ``POST
   http://localhost:8080/v1/users/self/validate`` request with the following
   components:

   * The ``Authorization`` header should be set to ``Basic`` auth with your
     username and password, e.g. with the credentials above::

       Authorization: Basic eW91ckBlbWFpbC5leGFtcGxlOnlvdXIucGFzc3dvcmQ=

   * The body being the following JSON payload:

     .. code-block:: json

         {
             "code": "<your received 4-digit code>"
         }

   If the request succeeds, you should receive a **204** HTTP status code.

You can verify that your account has been verified by issuing a
``GET http://localhost:8080/v1/users/self`` request with the same
``Authorization`` header as on step 2; it will return data regarding your
account **only if your account is validated**.

Running the tests
~~~~~~~~~~~~~~~~~

.. todo:: Write this part!

API concepts and architecture
-----------------------------

The following sections dig deeper into how the API is conceived and organized,
and why it is the way it is.

Network architecture
~~~~~~~~~~~~~~~~~~~~

.. figure:: contrib/network-architecture.png

    An overview of the network architecture.

The network architecture of the API is bare bones, with only a dependency
to an SMTP server to send e-mails, and a PostgreSQL for the API to be
as stateless as possible.

API workers are responsible both for responding to requests, as well as
running `background tasks`_, i.e. asynchronous functions set up by the routers
run after the response is sent to the client.

.. warning::

    This approach is only viable if the traffic isn't already overwhelming for
    API workers, and if the SMTP server responds in a timely manner.
    If any of these conditions is not met, background tasks should instead send
    a message on message queues such as RabbitMQ, for a separate worker pool
    to communicate with the SMTP server.

API structure
~~~~~~~~~~~~~

The API structure is inspired by REST, by adopting the following conventions
for endpoints:

``GET /v1/<resource-plural>``
    Search for resources of a given type.

``POST /v1/<resource-plural>``
    Create a resource of a given type.

    *Example:* ``POST /v1/users``

``GET /v1/<resource-plural>/<id>``
    Get a resource of a given type with the provided identifier.

    *Example:* ``GET /v1/users/self``

``POST /v1/<resource-plural>/<id>/<operation>``
    Run an operation on a resource of a given type with the provided
    identifier.

    *Example:* ``POST /v1/users/self/validate``

.. note::

    The ``/v1`` prefix is only placed out of convention, as no versioning
    plan is decided yet (e.g. per endpoint or global).

Correlation identifiers
~~~~~~~~~~~~~~~~~~~~~~~

Requests done with the API have a correlation identifier, that:

* Can be set by the client using the ``X-Correlation-ID`` header, otherwise
  it will be set as a random UUIDv4;
* Are placed in logs, if formatters support it;
* Are placed in the ``X-Correlation-ID`` header of the corresponding response;
* Are also placed as the ``correlation_id`` attribute in errors.

.. note::

    While that last point may seem extraneous since the information is already
    in the headers, it actually helps in debugging with some users that may
    only send a copy of the response body, and not of the headers.

Logging
~~~~~~~

Logging for the API can be configured through Python's standard logging
system; see `Python Logging Cookbook`_ for more information.

However, a formatter is provided, and is configured to be used by default in
the Docker setup, to format logs using `Elastic Common Schema`_ (ECS).
This schema is an effort in order to standardize logs for multiple
applications. Combined with correlation identifiers, if used by multiple
(or all!) systems, it can be used to trace the path an operation takes
using a single query on all datasets, which is especially useful in a
microservice context.

An example log using ECS emitted by the API is the following:

.. code-block:: json

    {
        "@timestamp": "2025-02-25 00:41:29,820.820Z",
        "ecs.version": "8.17.0",
        "host": {
            "hostname": "51b6ff0430cb"
        },
        "http": {
            "request": {
                "id": "d6f0bfb3-2009-49e9-bc8b-f22b245999d4"
            }
        },
        "log": {
            "level": "warning",
            "origin": {
                "function": "validate_user",
                "file": {
                    "line": 114,
                    "name": "user.py"
                },
            }
        },
        "message": "Incorrect code 1234 (expected: 2430) for user with e-mail addr.: ridley.scott2@example.org"
    }

Errors
~~~~~~

Error representations for the API follow `RFC 9457`_ "Problem Details for
HTTP APIs", meaning they bear at least the following elements:

``type``
    Machine-readable error type, which may be used for example to
    match the error to an exception in a client library, or trigger
    other behaviours.

    It is represented as a ``urn:example:`` URN, since the standard mandates
    that the type must be a URI.

``title``
    Human-readable title, which is mostly the error type transcribed into
    capitalized text. If displaying both the title and detail, this can be
    used in an ``<h1>`` HTML tag.

``detail``
    Human-readable detail, which is a sentence in English that describes what
    error has occurred. It can be used in an error "pop-up" on a front-end
    application, or as the description in an ``<p>`` HTML tag if displaying
    both the title and detail.

Other attributes may be present depending on the error type.

.. _Diátaxis: https://diataxis.fr/
.. _Docker: https://www.docker.com/
.. _PostgreSQL: https://www.postgresql.org/
.. _psql: https://www.postgresql.org/docs/current/app-psql.html
.. _MailCatcher: https://mailcatcher.me/
.. _Background tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
.. _Python Logging Cookbook:
    https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook
.. _Elastic Common Schema:
    https://www.elastic.co/guide/en/ecs/current/index.html
.. _RFC 9457:
    https://www.rfc-editor.org/rfc/rfc9457.html
