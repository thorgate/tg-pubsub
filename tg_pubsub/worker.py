import asyncio
import json
import logging

import websockets

from django.contrib.auth.models import AnonymousUser
from django.utils.encoding import force_text

try:
    from django.apps import apps

    get_model = apps.get_model

except ImportError:  # pragma: no cover
    from django.db.models import get_model

from . import pubsub

from .config import get_protocol_handler_klass


logger = logging.getLogger('tg_pubsub.server')


class HandlerProtocol(object):
    def __init__(self, ws, request):
        self.socket = ws
        self.request = request

        assert self.socket is not None

    @property
    def open(self):
        return self.socket.open

    @property
    def user(self):
        if self.request is None:
            return AnonymousUser()

        return self.request.user

    @property
    def logging_key(self):
        return 'tg_pubsub.handler-%s' % (self.user.pk or 'none')

    @asyncio.coroutine
    def send(self, data):
        if isinstance(data, dict):
            data = json.dumps(data)

        yield from self.socket.send(data)


class WebSocketHandler(object):
    def __init__(self, ws, request):
        super().__init__()

        self.ws = HandlerProtocol(ws, request)
        self.logger = logging.getLogger(self.ws.logging_key)

    @asyncio.coroutine
    def run(self):
        yield from self.model_changes()

    @asyncio.coroutine
    def model_changes(self):
        # Create Redis connection, subscribe channels
        self.logger.debug("Entering main Redis loop")
        r = pubsub.create_redis_connection()
        p = r.pubsub()

        # Subscribe to django channel.
        p.subscribe('django')

        while self.ws.open:
            msg = p.get_message(ignore_subscribe_messages=True)
            if msg is None:
                # If there was no message, sleep for one second, and try again
                yield from asyncio.sleep(1.0)
                continue

            model_path, action, instance_id = force_text(msg['data']).split(':')
            self.logger.debug("Got update from Redis: %s", msg)

            model = get_model(*model_path.split('-'))
            inst = model.objects.get(pk=instance_id)

            if not inst.has_access(self.ws.user):
                self.logger.debug("Ignoring update on %s:%s:%s, not authorized", model_path, action, instance_id)
                continue

            yield from self.ws.send({
                'model': model_path.replace('-', '.'),
                'action': action,
                'pk': instance_id,
                'data': inst.serialize(),  # This should always be defined
            })


@asyncio.coroutine
def client_handler(ws, path, request=None):
    handler = WebSocketHandler(ws, request)

    yield from handler.run()


def run_control_server(host, port):
    logger.info("Starting control server on %s:%d", host, port)

    start_server = websockets.serve(client_handler, host, port, klass=get_protocol_handler_klass())

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
