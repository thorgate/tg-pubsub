import json

from rest_framework.utils import encoders

from . import pubsub

from .config import get_model, extra_models
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
            json.dumps(self.data, cls=encoders.JSONEncoder),
        ])

    def publish(self):
        """ Publish message to redis queue
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
        from .models import ListenableModelMixin

        model_path = '%s.%s' % (data['app'], data['model'])
        model = get_model(data['app'], data['model'])
        inst = model.objects.get(pk=data['pk'])

        if issubclass(model, ListenableModelMixin):
            has_access = inst.has_access
            pubsub_serialize = inst.pubsub_serialize
            serializer = inst.get_serializer(inst)

        else:
            if model_path in extra_models:
                has_access = extra_models[model_path].has_access
                pubsub_serialize = extra_models[model_path].pubsub_serialize
                serializer = extra_models[model_path].get_serializer(inst)

            else:
                raise Exception('Model %s is not listenable' % model)

        if not has_access(inst, ws.user):
            raise IgnoreMessageException("Ignoring update on %s.%s:%s:%s, not authorized" % (data['app'], data['model'],
                                                                                             data['action'],data['pk']))

        return {
            'model': '%s.%s' % (data['app'], data['model']),
            'action': data['action'],
            'pk': data['pk'],
            'data': pubsub_serialize(inst, serializer),
        }


registry = {
    BaseMessage.MESSAGE_IDENTIFIER: BaseMessage,
    ModelChanged.MESSAGE_IDENTIFIER: ModelChanged,
}
