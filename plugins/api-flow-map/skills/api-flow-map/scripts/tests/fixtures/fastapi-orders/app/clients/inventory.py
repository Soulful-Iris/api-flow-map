import httpx
from app.config import INVENTORY_URL


async def reserve(items):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{INVENTORY_URL}/reservations", json=[i.dict() for i in items])
    return resp.json()


async def release(items):
    async with httpx.AsyncClient() as client:
        await client.delete(f"{INVENTORY_URL}/reservations", params={"skus": [i.sku for i in items]})
