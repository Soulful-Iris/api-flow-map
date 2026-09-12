from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.auth import get_current_user, require_scope
from app.schemas import CreateOrderRequest, OrderOut
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_user)])


@router.get("/{order_id}", response_model=OrderOut, summary="Fetch an order")
async def get_order(order_id: int, include_items: bool = False, user=Depends(get_current_user)):
    order = await order_service.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    if order.customer_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return order


@router.post("", status_code=201, response_model=OrderOut)
async def create_order(payload: CreateOrderRequest, x_request_id: str = Header(...), user=Depends(require_scope("orders:write"))):
    try:
        return await order_service.place_order(payload, user, x_request_id)
    except order_service.OutOfStock as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{order_id}/cancel", status_code=204)
async def cancel_order(order_id: int, user=Depends(require_scope("orders:write"))):
    await order_service.cancel_order(order_id, user)
