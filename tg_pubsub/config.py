from importlib import import_module

from django.conf import settings


def get_protocol_handler():
    return getattr(settings, 'TG_PUBSUB_PROTOCOL_HANDLER', 'tg_pubsub.protocol.RequestServerProtocol')


def get_protocol_handler_klass():
    return import_module(get_protocol_handler())


def get_control_server_host():
    return getattr(settings, 'TG_PUBSUB_HOST', 'localhost')


def get_control_server_port():
    return getattr(settings, 'TG_PUBSUB_PORT', 8090)
