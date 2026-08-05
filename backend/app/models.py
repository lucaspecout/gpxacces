from typing import Literal
from pydantic import BaseModel, Field

Classification = Literal["green", "orange", "red", "gray"]

class WayInfo(BaseModel):
    distance_m: float
    tags: dict[str, str] = Field(default_factory=dict)

class Segment(BaseModel):
    index: int
    coordinates: list[list[float]]
    distance_m: float
    slope_percent: float | None
    score: int
    classification: Classification
    relation: str
    reasons: list[str]
    nearest_way: WayInfo | None = None

