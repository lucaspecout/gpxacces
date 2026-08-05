import json
from itertools import islice
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

def _batches(values: list[Point], size: int):
    iterator=iter(values)
    while batch:=list(islice(iterator,size)): yield batch

async def fetch_ways(points: list[Point]) -> tuple[list[dict], bool]:
    """Charge un corridor autour de la trace et indique si Overpass a répondu.

    Une bbox unique devient énorme pour une trace longue ou en diagonale. Les
    petits corridors ci-dessous gardent les requêtes rapides et évitent qu'un
    seul timeout ne rende tout le parcours gris.
    """
    stride=max(1,len(points)//80)
    sampled=points[::stride]
    if sampled[-1] != points[-1]: sampled.append(points[-1])
    ways: dict[int,dict]={}; successful_batches=0
    headers={"User-Agent":"GPXAccess/0.3"}
    async with httpx.AsyncClient(timeout=settings.overpass_timeout_seconds,follow_redirects=True) as client:
        for batch in _batches(sampled,40):
            clauses="".join(f'way["highway"](around:120,{p.lat},{p.lon});' for p in batch)
            query=f'[out:json][timeout:20];({clauses});out tags geom;'
            for url in settings.overpass_urls.split(","):
                try:
                    response=await client.post(url.strip(),data={"data":query},headers=headers)
                    response.raise_for_status()
                    elements=response.json().get("elements",[])
                    for way in elements:
                        if way.get("type")=="way" and way.get("id") is not None: ways[way["id"]]=way
                    successful_batches+=1; break
                except (httpx.HTTPError,json.JSONDecodeError,ValueError):
                    continue
    return list(ways.values()), successful_batches > 0

def nearest_way(point: Point, ways: list[dict]) -> WayInfo | None:
    best: tuple[float,dict] | None = None
    for way in ways:
        geometry=way.get("geometry", [])
        for x,y in zip(geometry, geometry[1:]):
            d=_point_segment_distance(point, Point(x["lat"],x["lon"]), Point(y["lat"],y["lon"]))
            if best is None or d < best[0]: best=(d,way)
    if best is None: return None
    return WayInfo(distance_m=round(best[0],1), tags={k:str(v) for k,v in best[1].get("tags",{}).items() if k in TAGS})
