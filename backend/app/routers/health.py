from fastapi import APIRouter, Depends

from app.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db=Depends(get_db)):
    try:
        rows = db.query("RETURN 1 as ok")
        neo4j_up = bool(rows) and rows[0].get("ok") == 1
    except Exception as e:
        return {"status": "degraded", "neo4j": "down", "error": str(e)}

    return {"status": "ok" if neo4j_up else "degraded", "neo4j": "up" if neo4j_up else "down"}
