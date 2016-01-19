import asyncio
import json
import logging

import websockets

from django.contrib.auth.models import AnonymousUser
from django.utils.encoding import force_text

from .exceptions import InvalidMessageException, IgnoreMessageException

try:
    from django.apps import apps

    get_model = apps.get_model

except ImportError:  # pragma: no cover
    from django.db.models import get_model

from . import pubsub

from .config import get_protocol_handler_klass, get_hello_packets
from .messages import registry


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
        yield from self.send_hello()
        yield from self.send_on_change()

    @asyncio.coroutine
    def send_hello(self):
        packets = get_hello_packets()

        self.logger.debug("Sending %d hello packets", len(packets))

        for packet in packets:
            yield from self.ws.send(packet.prepare_for_send(self.ws, packet.data))

        self.logger.debug("Sent %d hello packets", len(packets))

    @asyncio.coroutine
    def send_on_change(self):
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

            try:
                self.logger.debug("Got update from Redis: %s", msg)
                identifier, data = self.message_valid(msg)

            except InvalidMessageException:
                continue

            else:
                try:
                    yield from self.ws.send(identifier.prepare_for_send(self.ws, data))

                except IgnoreMessageException as e:
                    self.logger.debug('%s' % e)

    @classmethod
    def message_valid(cls, message):
        msg_data = force_text(message['data'])

        if not msg_data or ':' not in msg_data:
            raise InvalidMessageException()

        identifier, data = force_text(msg_data).split(':', 1)

        if not (identifier and data):
            raise InvalidMessageException()

        # Only accept valid identifiers
        if identifier not in registry.keys():
            raise InvalidMessageException()

        # Parse the message body
        try:
            data = json.loads(data)

        except:
            raise InvalidMessageException()

        return registry[identifier], data


@asyncio.coroutine
def client_handler(ws, path, request=None):
    handler = WebSocketHandler(ws, request)

    yield from handler.run()


def run_control_server(host, port):
    logger.info("Starting control server on %s:%d", host, port)

    start_server = websockets.serve(client_handler, host, port, klass=get_protocol_handler_klass())

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
