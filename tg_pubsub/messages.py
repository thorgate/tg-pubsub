import json

try:
    from django.apps import apps

    get_model = apps.get_model

except ImportError:  # pragma: no cover
    from django.db.models import get_model


from . import pubsub
from .exceptions import IgnoreMessageException


class BaseMessage(object):
    MESSAGE_IDENTIFIER = 'base'

    def __init__(self, channels, data):
        assert ':' not in self.MESSAGE_IDENTIFIER

        if not isinstance(channels, (list, tuple)):
            channels = [channels, ]

        self.channels = channels
        self.data = data

    def as_message(self):
        return ':'.join([
            self.MESSAGE_IDENTIFIER,
            json.dumps(self.data),
        ])

    def publish(self):
        """ Publish message to redis que
        """
        message = self.as_message()

        for channel in self.channels:
            if isinstance(channel, (list, tuple)):
                channel = ':'.join(channel)

            pubsub.publish(channel, message)

    @classmethod
    def prepare_for_send(cls, ws, data):
        return data


class ModelChanged(BaseMessage):
    MESSAGE_IDENTIFIER = 'model'

    def __init__(self, klass, action, instance):
        # We publish to `django`, `django:app_name-model_name`, `django:app_name-model_name:action`
        channels = ['django', '%s-%s' % (klass._meta.app_label, klass._meta.object_name), action]

        super().__init__([channels[0:k] for k in range(1, len(channels) + 1)], {
            'app': klass._meta.app_label,
            'model': klass._meta.object_name,
            'action': action,
            'pk': instance.pk,
        })

    @classmethod
    def prepare_for_send(cls, ws, data):
        model = get_model(data['app'], data['model'])
        inst = model.objects.get(pk=data['pk'])

        if not inst.has_access(ws.user):
            raise IgnoreMessageException("Ignoring update on %s.%s:%s:%s, not authorized" % (data['app'], data['model'],
                                                                                             data['action'],data['pk']))

        return {
            'model': '%s.%s' % (data['app'], data['model']),
            'action': data['action'],
            'pk': data['pk'],
            'data': inst.serialize(),
        }


registry = {
    BaseMessage.MESSAGE_IDENTIFIER: BaseMessage,
    ModelChanged.MESSAGE_IDENTIFIER: ModelChanged,
}
