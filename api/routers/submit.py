from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas import ReviewSchema, ReportSchema
from models.tables import Review, Report
from ..dependencies import (
    get_current_user,
    get_db,
    submit_and_retrieve_site,
    make_site_geojson
)

router = APIRouter(
    prefix="/submit", tags=["users"], responses={404: {"description": "Not found"}},
)


@router.post("/review")
async def submit_review(
    stars: str,
    comment: str,
    site_id: str,
    Session: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    review = Review(
        stars=int(stars),
        comment=comment,
        site_id=site_id
    )
    review.user_email = user.email

    site = await submit_and_retrieve_site(Session, review)

    site_geojson = await make_site_geojson(site)
    return site_geojson

    """except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable submit review",
            headers={"WWW-Authenticate": "Bearer"},
        )"""


@router.post("/report")
async def submit_report(
    report_schema: ReportSchema,
    Session: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    try:

        report = Report(**report_schema.dict())
        report.user_email = user.email

        site = await submit_and_retrieve_site(Session, report)

        site_geojson = await make_site_geojson(site)

        return site_geojson

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable submit review",
        )
