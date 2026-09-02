import io

from fastapi import APIRouter, Depends, Query, Response

from app.deps import get_db, get_geo_mapper
from app.services import geo_service

router = APIRouter(prefix="/api/geo", tags=["geo"])


@router.get("/crime-types")
def crime_types(db=Depends(get_db)):
    return {"types": geo_service.get_crime_types(db)}


@router.get("/districts")
def districts(db=Depends(get_db)):
    return {"districts": geo_service.get_districts(db)}


@router.get("/all-locations")
def all_locations(db=Depends(get_db)):
    return {"locations": geo_service.get_all_locations(db)}


@router.get("/locations")
def locations(
    crime_types: list[str] | None = Query(None),
    start_date: str | None = None,
    end_date: str | None = None,
    districts: list[str] | None = Query(None),
    limit: int = Query(5000, ge=1, le=10000),
    db=Depends(get_db),
):
    df = geo_service.get_crime_locations(db, crime_types, start_date, end_date, districts, limit)
    return {"count": len(df), "rows": df.to_dict(orient="records")}


@router.get("/hotspots")
def hotspots(
    crime_types: list[str] | None = Query(None),
    start_date: str | None = None,
    end_date: str | None = None,
    districts: list[str] | None = Query(None),
    limit: int = Query(5000, ge=1, le=10000),
    db=Depends(get_db),
    mapper=Depends(get_geo_mapper),
):
    df = geo_service.get_crime_locations(db, crime_types, start_date, end_date, districts, limit)
    predictions = mapper.predict_hotspots(df)
    return {"count": len(predictions), "predictions": predictions.to_dict(orient="records")}


@router.get("/export.csv")
def export_csv(
    crime_types: list[str] | None = Query(None),
    start_date: str | None = None,
    end_date: str | None = None,
    districts: list[str] | None = Query(None),
    limit: int = Query(5000, ge=1, le=10000),
    db=Depends(get_db),
):
    df = geo_service.get_crime_locations(db, crime_types, start_date, end_date, districts, limit)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=crime_locations.csv"},
    )
