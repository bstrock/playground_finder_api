from fastapi import Depends, APIRouter
from models.tables import User, Review, Report
from ..dependencies import get_current_user, get_db, schema_to_row, pwd_context, submit_and_retrieve_site, \
    make_site_schema_response
from models.schemas import (
    UserSchema,
    ReviewSchema,
    ReportSchema)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from icecream import ic
from fastapi import FastAPI, Query as fastapi_Query, Depends, HTTPException, status
from sqlalchemy.sql import Update

router = APIRouter(
    prefix="/submit",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post('/review')
async def submit_review(
        review_schema: ReviewSchema,
        Session: AsyncSession = Depends(get_db),
        user=Depends(get_current_user),
):
    try:
        review = Review(**review_schema.dict())
        review.user_email = user.email

        site = await submit_and_retrieve_site(Session, review)

        site_schema = await make_site_schema_response(site)
        return site_schema

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable submit review",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/report")
async def submit_report(
        report_schema: ReportSchema,
        Session: AsyncSession = Depends(get_db),
        user=Depends(get_current_user)
):
    try:

        report = Report(**report_schema.dict())
        report.user_email = user.email

        site = await submit_and_retrieve_site(Session, report)

        site_schema = await make_site_schema_response(site)

        return site_schema

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable submit review",
        )
