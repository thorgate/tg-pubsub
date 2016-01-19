from django.conf import settings
from django.utils.module_loading import import_string


def get_protocol_handler():
    return getattr(settings, 'TG_PUBSUB_PROTOCOL_HANDLER', 'tg_pubsub.protocol.RequestServerProtocol')


def get_protocol_handler_klass():
    return import_string(get_protocol_handler())


def get_control_server_host():
    return getattr(settings, 'TG_PUBSUB_HOST', 'localhost')


def get_control_server_port():
    return getattr(settings, 'TG_PUBSUB_PORT', 8090)


def get_hello_packets():
    from .messages import BaseMessage

    packets = getattr(settings, 'TG_PUBSUB_HELLO_PACKETS', [])
    res = []

    assert isinstance(packets, (list, tuple))

    for path in packets:
        fn = import_string(path)

        assert callable(fn)

        instance = fn()
        assert isinstance(instance, BaseMessage)

        res.append(instance)

    return res
