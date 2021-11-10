from fastapi import Depends, APIRouter
from models.tables import User
from ..dependencies import get_current_user, get_db, schema_to_row, pwd_context
from models.schemas import (
    UserSchema,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from icecream import ic
from fastapi import FastAPI, Query as fastapi_Query, Depends, HTTPException, status


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/create")
async def create_user(
        incoming_user: UserSchema,
        Session: AsyncSession = Depends(get_db)
):
    ic(incoming_user)
    async with Session as s:
        async with s.begin():
            presence_test = await s.get(User, incoming_user.email)

    if presence_test:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="This user already exists"
        )

    else:
        user = schema_to_row(incoming_user, User)
        user.hashed_password = pwd_context.hash(user.hashed_password)
        async with Session as s:
            async with s.begin():
                s.add(user)


@router.get("/me")
async def read_users_me(current_user: UserSchema = Depends(get_current_user)):
    return current_user


@router.get("/me/items")
async def read_own_items(current_user: UserSchema = Depends(get_current_user)):
    return [{"item_id": "Foo", "owner": current_user.email}]