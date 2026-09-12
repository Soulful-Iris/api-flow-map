import httpx
from app.config import PAYMENTS_URL


class PaymentDeclined(Exception):
    pass


async def charge(amount, token, request_id):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{PAYMENTS_URL}/v2/charges", json={"amount": amount, "token": token}, headers={"X-Request-Id": request_id})
    if resp.status_code == 402:
        raise PaymentDeclined(resp.text)
    return resp.json()


async def refund(payment_id):
    async with httpx.AsyncClient() as client:
        await client.post(f"{PAYMENTS_URL}/v2/charges/{payment_id}/refund")
