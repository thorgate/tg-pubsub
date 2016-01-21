import logging

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from rest_framework.serializers import ModelSerializer

from .config import extra_models, get_model
from .messages import ModelChanged

logger = logging.getLogger('tg_pubsub')


class ListenableBase(object):
    """ Base mixin that declares the api for listenables
    """
    serializer_class = None
    serializer_fields = ('pk', )

    def pubsub_get_model(self):
        return self.__class__

    def get_serializer_class(self):
        """ Return the class to use for the serializer.
        """
        if self.serializer_class is None:
            class ListenableSerializer(ModelSerializer):
                class Meta:
                    model = self.pubsub_get_model()

                    fields = self.serializer_fields

            return ListenableSerializer

        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, **kwargs)

    @classmethod
    def has_access(cls, instance, user):
        """ Does the given user has access to the model instance. This can be used to only send model data to specific users.

        (Note: The user may be anonymous)

        :param instance: Model instance
        :param user:     User connected via pubsub
        :rtype: bool
        """
        return True

    @classmethod
    def should_notify(cls, instance, action):
        """ Should the given instance send out a change notification. This can be used to limit publishes to only specific instances.

        :param instance: Model instance
        :param action:   Action that triggered the notification (created, saved, deleted)
        :rtype: bool
        """
        return True

    @classmethod
    def pubsub_serialize(cls, instance, serializer):
        """ Serialize the given model instance before sending it to the users.

        :param instance: Model instance
        :param serializer: Drf serializer
        :return:
        """
        return serializer.to_representation(instance)


class ListenableModelMixin(ListenableBase):
    """ Mixin that will mark model as 'listenable'. Such models will send messages to Redis queue whenever they're updated.
    """
    pass


class ModelListenConfig(ListenableModelMixin):
    """ Special class that can be used to mark external app models as listenable.

        via: TG_PUBSUB_EXTRA_MODELS
    """

    model_path = None

    def __init__(self):
        super().__init__()

        if self.model_path is None:
            raise ImproperlyConfigured('ModelListenConfig invalid model path %s' % self.model_path)

        self.model = get_model(self.model_path)

    def pubsub_get_model(self):
        return self.model


def is_model_listenable(cls, action, instance):
    if not issubclass(cls, models.Model):
        return False

    if issubclass(cls, ListenableModelMixin):
        should_notify = cls.should_notify

    else:
        model_path = '%s.%s' % (cls._meta.app_label, cls._meta.object_name)

        if model_path in extra_models:
            should_notify = extra_models[model_path].should_notify

        else:
            return False

    if not should_notify(instance, action):
        return False

    return True


def model_changed(cls, action, instance):
    # This should never cause problems for the outside code, so wrap it all in try: except:, just to be sure.
    try:
        if not is_model_listenable(cls, action, instance):
            return

        logging.info("model_changed(): %s-%s:%s:%s", cls._meta.app_label, cls._meta.object_name, action, str(instance.id))

        ModelChanged(cls, action, instance).publish()

    except Exception as e:
        logging.warning("Exception in model_changed(%s, %s, %s: %s): %s", cls, action, type(instance), getattr(instance, 'id', '-'), e)


@receiver(post_save)
def model_post_save_handler(sender, instance, created, **kwargs):
    if created:
        model_changed(sender, 'created', instance)
    else:
        model_changed(sender, 'saved', instance)


@receiver(pre_delete)
def model_pre_delete_handler(sender, instance, **kwargs):
    model_changed(sender, 'deleted', instance)
