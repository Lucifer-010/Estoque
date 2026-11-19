import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.blockchain.services import BlockchainService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Run Soroban smart contract event listener and indexer for Estoque"

    def add_arguments(self, parser):
        parser.add_argument(
            '--poll-interval',
            type=int,
            default=5,
            help='Polling interval in seconds (default: 5)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run a single polling cycle and exit'
        )

    def handle(self, *args, **options):
        interval = options['poll_interval']
        run_once = options['once']
        service = BlockchainService()

        self.stdout.write(self.style.SUCCESS(
            f"Starting Estoque Soroban Event Listener [Network: {service.network}, Contract: {service.contract_id}]"
        ))

        while True:
            try:
                # Simulated or live event indexing heartbeat
                info = service.get_contract_info()
                self.stdout.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checked Soroban ledger. Status: {info['contract_status']}")
                if run_once:
                    break
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("Stopping event listener..."))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in event listener cycle: {e}"))
                if run_once:
                    raise e
                time.sleep(interval)

