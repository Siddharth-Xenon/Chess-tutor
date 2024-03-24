from fastapi import APIRouter, Depends
from fastapi_jwt_auth import AuthJWT

from app.api.controllers import app

router = APIRouter()


@router.get("/delete_this_route")
async def delete_this_route(
    Authorize: AuthJWT = Depends(),
):
    res: dict = await app.delete_this_route()
    return res
