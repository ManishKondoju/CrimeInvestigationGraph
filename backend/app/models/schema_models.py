from typing import Any

from pydantic import BaseModel


class NodeType(BaseModel):
    node_type: str
    count: int


class RelationshipType(BaseModel):
    source_type: str
    relationship_type: str
    target_type: str
    count: int


class SchemaData(BaseModel):
    nodes: list[NodeType]
    relationships: list[RelationshipType]
    properties: dict[str, list[str]]


class SampleNode(BaseModel):
    properties: dict[str, Any]
