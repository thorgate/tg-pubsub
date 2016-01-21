from django.core.management import BaseCommand

from ...worker import run_pubsub_server
from ...config import get_pubsub_server_host, get_pubsub_server_port


class Command(BaseCommand):
    help = "Runs websocket-based control server for pubsub."
    args = '[optional port number]'

    def handle(self, port='', *args, **options):
        port = int(port) if port else get_pubsub_server_port()
        run_pubsub_server(get_pubsub_server_host(), port)
