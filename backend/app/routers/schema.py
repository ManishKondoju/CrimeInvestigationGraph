from fastapi import APIRouter, Depends, HTTPException, Response

from app.deps import get_schema_viz
from app.models.schema_models import SchemaData

router = APIRouter(prefix="/api/schema", tags=["schema"])


@router.get("", response_model=SchemaData)
def schema(viz=Depends(get_schema_viz)):
    return viz.get_schema_data()


@router.get("/sample/{label}")
def sample(label: str, viz=Depends(get_schema_viz)):
    # Allow-list check: label must be a real node label already discovered by
    # get_schema_data(), never interpolated from arbitrary user input directly
    # into the f-string Cypher inside get_schema_data()'s sibling query below.
    known_labels = {n["node_type"] for n in viz.get_schema_data()["nodes"]}
    if label not in known_labels:
        raise HTTPException(status_code=400, detail=f"Unknown node label: {label}")

    rows = viz.db.query(f"MATCH (n:{label}) RETURN n LIMIT 3")
    return {"label": label, "samples": [dict(r["n"]) for r in rows]}


@router.get("/export/{fmt}")
def export(fmt: str, viz=Depends(get_schema_viz)):
    schema_data = viz.get_schema_data()

    if fmt == "json":
        import json

        return Response(
            content=json.dumps(schema_data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=graph_schema.json"},
        )
    if fmt == "cypher":
        return Response(
            content=viz._generate_cypher_schema(schema_data),
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=graph_schema.cypher"},
        )
    if fmt == "markdown":
        return Response(
            content=viz._generate_markdown_schema(schema_data),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=graph_schema.md"},
        )

    raise HTTPException(status_code=400, detail=f"Unknown export format: {fmt}")
