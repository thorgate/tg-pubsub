========
Settings
========

List of available settings
--------------------------

TG_PUBSUB_HOST
~~~~~~~~~~~~~~

Network interface on which the pubsub control server should bind to (default: ``localhost``).

TG_PUBSUB_PORT
~~~~~~~~~~~~~~

Port on which the pubsub control server should listen on (default: ``8090``).

TG_PUBSUB_EXTRA_MODELS
~~~~~~~~~~~~~~~~~~~~~~

List of import strings to subclasses of :py:class:`~tg_pubsub.messages.ModelListenConfig` representing extra models
that should be listened on (see: :ref:`cant-extend-listenable`). (default: ``[]``)


TG_PUBSUB_HELLO_PACKETS
~~~~~~~~~~~~~~~~~~~~~~~

List of import strings to callables that must return an instance of :py:class:`~tg_pubsub.messages.BaseMessage`. These are
sent to clients after successful connection has been established. (default: ``[]``)

TG_PUBSUB_PROTOCOL_HANDLER
~~~~~~~~~~~~~~~~~~~~~~~~~~

The protocol handler for your application (default: ``tg_pubsub.protocol.RequestServerProtocol``).

Builtin protocols:

.. autoclass:: tg_pubsub.protocol.RequestServerProtocol()
.. autoclass:: tg_pubsub.protocol.SessionRequiredServerProtocol()
.. autoclass:: tg_pubsub.protocol.AnyUserServerProtocol()
.. autoclass:: tg_pubsub.protocol.AnonymousUserServerProtocol()
.. autoclass:: tg_pubsub.protocol.AuthenticatedUserServerProtocol()
.. autoclass:: tg_pubsub.protocol.StaffUserServerProtocol()
.. autoclass:: tg_pubsub.protocol.SuperUserServerProtocol()

Custom protocols should extend built-in protocols
