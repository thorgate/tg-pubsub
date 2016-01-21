from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.functional import SimpleLazyObject
from django.utils.module_loading import import_string

from rest_framework import serializers

get_model = apps.get_model

def get_protocol_handler():
    return getattr(settings, 'TG_PUBSUB_PROTOCOL_HANDLER', 'tg_pubsub.protocol.RequestServerProtocol')


def get_protocol_handler_klass():
    return import_string(get_protocol_handler())


def get_pubsub_server_host():
    return getattr(settings, 'TG_PUBSUB_HOST', 'localhost')


def get_pubsub_server_port():
    return getattr(settings, 'TG_PUBSUB_PORT', 8090)


def get_hello_packets():
    """ Get all packets to send right after doing websocket handshake

        TG_PUBSUB_HELLO_PACKETS: List of import paths to callables that must return an instance of BaseMessage
    :return:
    """
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


def get_extra_models():
    """ Get extra models to mark as listenable. This is useful if one needs to listen to changes
        on a model that is coming from external apps so subclassing variant is impossible.

        TG_PUBSUB_EXTRA_MODELS: list(config_path, ...)

    :rtype: dict
    """
    from .models import ListenableModelMixin, ModelListenConfig

    extra = getattr(settings, 'TG_PUBSUB_EXTRA_MODELS', [])

    res = {}

    assert isinstance(extra, (list, tuple))

    for config_path in extra:
        klass = import_string(config_path)

        if not issubclass(klass, ModelListenConfig):
            raise ImproperlyConfigured('extra_models: Config path %s is not a ModelListenConfig' % config_path)

        if klass.model_path in res:
            raise ImproperlyConfigured('extra_models: Model %s already listenable' % klass.model_path)

        instance = klass()

        if isinstance(instance.model, ListenableModelMixin):
            raise ImproperlyConfigured('extra_models: Model %s already listenable' % klass.model_path)

        res[instance.model_path] = instance

    return res


extra_models = SimpleLazyObject(get_extra_models)
