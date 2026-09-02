from fastapi import APIRouter, Depends, Query

from app.deps import get_db
from app.services import timeline_service

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("/crime-types")
def crime_types(db=Depends(get_db)):
    return {"types": timeline_service.get_crime_types(db)}


@router.get("/locations")
def locations(db=Depends(get_db)):
    return {"locations": timeline_service.get_locations(db)}


@router.get("/data")
def data(
    start_date: str | None = None,
    end_date: str | None = None,
    crime_types: list[str] | None = Query(None),
    locations: list[str] | None = Query(None),
    severity: list[str] | None = Query(None),
    db=Depends(get_db),
):
    df = timeline_service.get_crime_timeline_data(db, start_date, end_date, crime_types, locations, severity)
    return {"count": len(df), "rows": df.to_dict(orient="records")}


@router.get("/summary")
def summary(
    start_date: str | None = None,
    end_date: str | None = None,
    crime_types: list[str] | None = Query(None),
    locations: list[str] | None = Query(None),
    severity: list[str] | None = Query(None),
    db=Depends(get_db),
):
    return timeline_service.get_timeline_summary(db, start_date, end_date, crime_types, locations, severity)
