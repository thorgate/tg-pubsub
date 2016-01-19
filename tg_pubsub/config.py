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

    assert isinstance(packets, (list, tuple)) and all([isinstance(p, (list, tuple)) for p in packets])

    for path, kwargs in packets:
        assert isinstance(kwargs, dict)

        klass = import_string(path)
        assert issubclass(klass, BaseMessage)

        res.append(klass(**kwargs))

    return res
