import logging
from app.db import session
from app.models import Order
from app.clients import payments, inventory
from app.events import publish
from app.flags import flags

log = logging.getLogger(__name__)
REVIEW_THRESHOLD = 1000


class OutOfStock(Exception):
    pass


async def get_order(order_id: int):
    return session.query(Order).filter(Order.id == order_id).first()


async def place_order(payload, user, request_id):
    if not payload.items:
        raise ValueError("order must contain items")
    order = Order.from_payload(payload, customer_id=user.id)
    reserved = await inventory.reserve(order.items)
    if not reserved.ok:
        raise OutOfStock(reserved.missing)
    if order.total > REVIEW_THRESHOLD and flags.is_enabled("manual-review"):
        order.status = "UNDER_REVIEW"
        session.add(order)
        session.commit()
        await publish("order-events", {"type": "ORDER_FLAGGED", "id": order.id})
        return order
    try:
        result = await payments.charge(order.total, payload.payment_token, request_id)
    except payments.PaymentDeclined:
        await inventory.release(order.items)
        raise
    order.payment_id = result["id"]
    order.status = "CONFIRMED"
    session.add(order)
    session.commit()
    await publish("order-events", {"type": "ORDER_PLACED", "id": order.id})
    return order


async def cancel_order(order_id: int, user):
    order = session.query(Order).get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    match order.status:
        case "CONFIRMED":
            await payments.refund(order.payment_id)
            await inventory.release(order.items)
        case "UNDER_REVIEW":
            pass
        case _:
            raise ValueError(f"cannot cancel order in status {order.status}")
    order.status = "CANCELLED"
    session.commit()
    await publish("order-events", {"type": "ORDER_CANCELLED", "id": order.id})
