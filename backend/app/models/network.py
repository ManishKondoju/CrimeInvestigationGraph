from pydantic import BaseModel


class EntityOption(BaseModel):
    id: str | int
    name: str


class NetworkNode(BaseModel):
    id: str | int
    label: str | None = None
    type: str


class NetworkEdge(BaseModel):
    source: str | int
    target: str | int
    label: str


class NetworkGraph(BaseModel):
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
