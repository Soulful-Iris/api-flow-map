from fastapi import Depends, HTTPException


async def get_current_user(token: str = Depends(lambda: "t")):
    return token


def require_scope(scope: str):
    async def dep(user=Depends(get_current_user)):
        return user
    return dep
