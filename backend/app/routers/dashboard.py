from fastapi import APIRouter, Depends

from app.deps import get_db
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis")
def kpis(db=Depends(get_db)):
    return dashboard_service.get_kpis(db)


@router.get("/trends")
def trends(db=Depends(get_db)):
    return dashboard_service.get_trends(db)


@router.get("/gangs")
def gangs(db=Depends(get_db)):
    return dashboard_service.get_gangs(db)


@router.get("/breakdowns")
def breakdowns(db=Depends(get_db)):
    return dashboard_service.get_breakdowns(db)


@router.get("/operations")
def operations(db=Depends(get_db)):
    return dashboard_service.get_operations(db)


@router.get("/activity")
def activity(db=Depends(get_db)):
    return dashboard_service.get_activity(db)
