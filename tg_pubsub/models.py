import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from rest_framework.serializers import ModelSerializer

from .messages import ModelChanged

logger = logging.getLogger('tg_pubsub')


class ListenableModelMixin:
    """
    Mixin that will mark model as 'listenable'. Such models will send messages to Redis queue whenever they're updated.
    """
    SERIALIZER_CLASS = ModelSerializer

    def get_serializer(self):
        class Serializer(ModelSerializer):
            class Meta:
                model = self.__class__

        return Serializer

    def has_access(self, user):
        return True

    def serialize(self):
        serializer = self.get_serializer()

        if serializer is not None:
            serializer = serializer(self)
            return serializer.to_representation(self)

        else:
            return {
                'pk': self.pk,
            }

    @classmethod
    def should_notify(cls, instance, action):
        return True


def model_changed(cls, action, instance):
    # This should never cause problems for the outside code, so wrap it all in try: except:, just to be sure.
    try:
        if not issubclass(cls, ListenableModelMixin):
            return

        if not cls.should_notify(instance, action):
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
