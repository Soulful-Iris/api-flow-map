from fastapi import FastAPI
from app.routers import orders, health

app = FastAPI(title="Orders")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(health.router)
