from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_graph_algorithms

router = APIRouter(prefix="/api/graph", tags=["graph-algorithms"])


@router.get("/pagerank")
def pagerank(algo=Depends(get_graph_algorithms)):
    return {"results": algo.calculate_pagerank()}


@router.get("/communities")
def communities(algo=Depends(get_graph_algorithms)):
    return {
        "communities": algo.detect_communities(),
        "hidden_rings": algo.find_hidden_crime_rings(),
    }


@router.get("/degree-centrality")
def degree_centrality(algo=Depends(get_graph_algorithms)):
    return {"results": algo.calculate_degree_centrality()}


@router.get("/betweenness-centrality")
def betweenness_centrality(algo=Depends(get_graph_algorithms)):
    return {"results": algo.calculate_betweenness_centrality()}


@router.get("/persons")
def persons(algo=Depends(get_graph_algorithms)):
    rows = algo.db.query("MATCH (p:Person) RETURN p.name as name ORDER BY name LIMIT 100")
    return {"names": [r["name"] for r in rows]}


@router.get("/shortest-path")
def shortest_path(person1: str, person2: str, algo=Depends(get_graph_algorithms)):
    result = algo.find_shortest_path(person1, person2)
    if not result:
        raise HTTPException(status_code=404, detail=f"No path found between {person1} and {person2}")
    return result


@router.get("/all-paths")
def all_paths(person1: str, person2: str, max_length: int = Query(4, ge=1, le=6), algo=Depends(get_graph_algorithms)):
    return {"paths": algo.find_all_paths_between(person1, person2, max_length)}


@router.get("/stats")
def stats(algo=Depends(get_graph_algorithms)):
    return algo.get_network_statistics()
