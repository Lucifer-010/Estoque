from celery import shared_task
import logging
from apps.inventory.models import InventoryBatch
from apps.orders.models import PurchaseOrder
from .services import BlockchainService

logger = logging.getLogger(__name__)

@shared_task(name='tasks.async_anchor_batch_proof')
def task_anchor_batch_proof(batch_id: int):
    try:
        batch = InventoryBatch.objects.get(id=batch_id)
        service = BlockchainService()
        result = service.register_batch_proof(batch)
        logger.info(f"Successfully anchored batch proof for batch {batch_id}: {result['tx_hash']}")
        return result
    except Exception as exc:
        logger.error(f"Error anchoring batch {batch_id}: {exc}")
        raise exc

@shared_task(name='tasks.async_fund_escrow')
def task_fund_escrow(order_id: int):
    try:
        order = PurchaseOrder.objects.get(id=order_id)
        service = BlockchainService()
        result = service.fund_escrow(order)
        logger.info(f"Successfully funded escrow for order {order_id}: {result['tx_hash']}")
        return result
    except Exception as exc:
        logger.error(f"Error funding escrow for order {order_id}: {exc}")
        raise exc

@shared_task(name='tasks.async_release_escrow')
def task_release_escrow(order_id: int):
    try:
        order = PurchaseOrder.objects.get(id=order_id)
        service = BlockchainService()
        result = service.release_escrow(order)
        logger.info(f"Successfully released escrow for order {order_id}: {result['tx_hash']}")
        return result
    except Exception as exc:
        logger.error(f"Error releasing escrow for order {order_id}: {exc}")
        raise exc

@shared_task(name='tasks.async_refund_escrow')
def task_refund_escrow(order_id: int):
    try:
        order = PurchaseOrder.objects.get(id=order_id)
        service = BlockchainService()
        result = service.refund_escrow(order)
        logger.info(f"Successfully refunded escrow for order {order_id}: {result['tx_hash']}")
        return result
    except Exception as exc:
        logger.error(f"Error refunding escrow for order {order_id}: {exc}")
        raise exc

