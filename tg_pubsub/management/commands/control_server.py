from django.core.management import BaseCommand

from ...worker import run_control_server
from ...config import get_control_server_host, get_control_server_port


class Command(BaseCommand):
    help = "Runs websocket-based control server for pubsub."
    args = '[optional port number]'

    def handle(self, port='', *args, **options):
        port = int(port) if port else get_control_server_port()
        run_control_server(get_control_server_host(), port)
