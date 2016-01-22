=====
Usage
=====


Given a django model, for example::

    from django.db import models

    class Topping(models.Model):
        # ...
        pass

To make the ``Topping`` listenable it must use :py:class:`~tg_pubsub.models.ListenableModelMixin`::

    from tg_pubsub.models import ListenableModelMixin

    class Topping(ListenableModelMixin, models.Model):
        # ...
        pass


Now when a topping is created/updated a message is pushed to redis message queue on the following channels::

    django
    django:app_name-model_name
    django:app_name-model_name:action

Start the pubsub server::

    $ python manage.py pubsub_server


Use http://www.websocket.org/echo.html to connect to ``localhost:8090`` to see the
messages being sent to the users

Limit instances
---------------

This can be controlled via the ``should_notify(instance, action)`` method on the listenable model class.

Permission checks
-----------------

Every publish to the client will call the special ``has_access(instance, user)`` method on the listenable
model class. Returning False means the user won't get a push for a model that they don't have access to.

Serialization
-------------

By default only the pk will be published by the pubsub server to the clients. To add more model fields one
can use ``serializer_fields`` attribute on the listenable model. However, this will only work if the added
fields can be serialized to json (by drf) and are available as instance attributes.

For more fine-grained serialization use ``serializer_class`` attribute and set it to a ``django-rest-framework``
serializer based on your needs.

.. _cant-extend-listenable:

Cant extend the model with ListenableModelMixin?
------------------------------------------------

If you are unable to use :py:class:`~tg_pubsub.models.ListenableModelMixin` there is still hope. First you must
declare your model listening config::

    from tg_pubsub.models import ModelListenConfig


    class HiddenModelListener(ModelListenConfig):
        model_path = 'some_app.Hidden'  # app_name.model_name of the model you want to listen to

And also add the path of your :py:class:`~tg_pubsub.models.ModelListenConfig` to ``settings.TG_PUBSUB_EXTRA_MODELS``::

    TG_PUBSUB_EXTRA_MODELS = [
        'path.to.HiddenModelListener',
    ]

ModelListenConfig supports the same features as :py:class:`~tg_pubsub.models.ListenableModelMixin`
