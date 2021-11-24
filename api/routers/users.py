from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from models.schemas import UserSchema, UserResponseSchema
from models.tables import User
from ..dependencies import get_current_user, get_db, schema_to_row, pwd_context
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

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
@router.get("/me/favorites", response_model=UserResponseSchema)
async def get_favorites(
        user=Depends(get_current_user), Session: AsyncSession = Depends(get_db)
):
    async with Session as s:
        async with s.begin():
            res = await s.get(User, user.email)
            user_response = UserResponseSchema(
                first_name=res.first_name,
                last_name=res.last_name,
                favorite_parks=res.favorite_parks,
                email=res.email
            )
            json_response = jsonable_encoder(user_response)
            return JSONResponse(json_response)


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
