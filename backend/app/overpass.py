import json
from math import cos, radians
import httpx
from .config import settings
from .gpx import Point, distance
from .models import WayInfo

TAGS = ("highway","surface","smoothness","tracktype","width","maxwidth","maxheight","lanes","access","vehicle","motor_vehicle","emergency","barrier","incline","ford","bridge","tunnel","service")

def _point_segment_distance(p: Point, a: Point, b: Point) -> float:
    scale = cos(radians(p.lat)); x, y = p.lon*scale, p.lat; ax, ay = a.lon*scale, a.lat; bx, by = b.lon*scale, b.lat
    dx, dy = bx-ax, by-ay
    t = max(0, min(1, ((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return distance(p, Point(ay+t*dy, (ax+t*dx)/scale))

async def fetch_ways(points: list[Point]) -> list[dict]:
    # Environ 200 m de marge : assez pour rapprocher la trace d'une voie sans
    # charger inutilement toutes les données d'une commune.
    south=min(p.lat for p in points)-.002; north=max(p.lat for p in points)+.002
    west=min(p.lon for p in points)-.003; east=max(p.lon for p in points)+.003
    query=f'[out:json][timeout:20];way["highway"]({south},{west},{north},{east});out tags geom;'
    for url in settings.overpass_urls.split(","):
        try:
            async with httpx.AsyncClient(timeout=settings.overpass_timeout_seconds) as client:
                response=await client.post(url.strip(), data={"data":query}, headers={"User-Agent":"GPXAccess/0.2 (analyse GPX)"})
                response.raise_for_status(); return response.json().get("elements", [])
        except (httpx.HTTPError, json.JSONDecodeError):
            continue
    return []

def nearest_way(point: Point, ways: list[dict]) -> WayInfo | None:
    best: tuple[float,dict] | None = None
    for way in ways:
        geometry=way.get("geometry", [])
        for x,y in zip(geometry, geometry[1:]):
            d=_point_segment_distance(point, Point(x["lat"],x["lon"]), Point(y["lat"],y["lon"]))
            if best is None or d < best[0]: best=(d,way)
    if best is None: return None
    return WayInfo(distance_m=round(best[0],1), tags={k:str(v) for k,v in best[1].get("tags",{}).items() if k in TAGS})
