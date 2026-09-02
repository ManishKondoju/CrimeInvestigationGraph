from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_network_viz
from app.models.network import EntityOption, NetworkGraph

router = APIRouter(prefix="/api/network", tags=["network"])

ENTITY_TYPES = ["Organization", "Person", "Crime", "Location", "Investigator", "Evidence", "Weapon", "Vehicle"]


@router.get("/entity-types")
def entity_types(viz=Depends(get_network_viz)):
    return {"types": ENTITY_TYPES, "colors": viz.color_map}


@router.get("/entities", response_model=list[EntityOption])
def entities(type: str, viz=Depends(get_network_viz)):
    if type not in ENTITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {type}")
    rows = viz.get_all_entities_of_type(type)
    return [EntityOption(id=r["id"], name=r["name"]) for r in rows]


@router.get("/graph", response_model=NetworkGraph)
def graph(type: str, id: str | None = None, viz=Depends(get_network_viz)):
    if type not in ENTITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {type}")
    return viz.get_network_data(type, id)
