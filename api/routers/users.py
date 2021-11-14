from fastapi import Depends, APIRouter
from models.tables import User
from ..dependencies import get_current_user, get_db, schema_to_row, pwd_context
from models.schemas import UserSchema
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from icecream import ic
from fastapi import FastAPI, Query as fastapi_Query, Depends, HTTPException, status
from sqlalchemy.sql import Update

router = APIRouter(
    prefix="/users", tags=["users"], responses={404: {"description": "Not found"}},
)


# THIS ENDPOINT CREATES A NEW USER
# PUBLIC ENDPOINT
@router.post("/create")
async def create_user(
    incoming_user: UserSchema, Session: AsyncSession = Depends(get_db)
):
    # check to see if user exists in db
    async with Session as s:
        async with s.begin():
            presence_test = await s.get(User, incoming_user.email)

    # if they do, raise an exception
    if presence_test:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This user already exists"
        )

    # otherwise, make the user in the database
    else:
        user = schema_to_row(
            incoming_user, User
        )  # convert incoming user schema to table object
        user.hashed_password = pwd_context.hash(
            user.hashed_password
        )  # hash password before sending to db

        async with Session as s:
            async with s.begin():
                s.add(user)

        return {"status": "created"}


# THIS ENDPOINT GETS A USER'S FAVORITE PLAYGROUNDS
# AUTHENTICATED ENDPOINT
@router.get("/me/favorites")
async def get_favorites(
    user=Depends(get_current_user), Session: AsyncSession = Depends(get_db)
):
    async with Session as s:
        async with s.begin():
            res = await s.get(User, user.email).first()

    return {"favorites": res.favorite_parks}


# THIS ENDPOINT ADDS OR REMOVES A FAVORITE FROM THE USER'S FAVORITES
# AUTHENTICATED ENDPOINT
@router.post("/me/favorites")
async def modify_favorites(
    operation: str,  # add/remove
    site_id: str,
    user=Depends(get_current_user),
    Session: AsyncSession = Depends(get_db),
):
    # get the existing favorites
    async with Session as s:
        # note that we need to commmit this manually since we're not using the begin() pattern to autocommit
        res = await s.get(User, user.email)
        favorites = res.favorite_parks

        if operation == "add":
            favorites.append(site_id)  # add the site to their favorites
        elif operation == "remove":
            favorites.remove(site_id)  # remove the site from their favorites

        # this update statement will apply changes to the database
        stmt = (
            User.__table__.update()
            .where(User.email == user.email)
            .values(favorite_parks=favorites)
        )

        await s.execute(stmt)  # send update
        await s.commit()  # commit the transaction

    return {"favorites": favorites}
