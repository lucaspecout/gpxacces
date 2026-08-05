from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from defusedxml import ElementTree as ET

@dataclass(frozen=True)
class Point:
    lat: float
    lon: float
    ele: float | None = None

def distance(a: Point, b: Point) -> float:
    p1, p2 = radians(a.lat), radians(b.lat)
    dp, dl = radians(b.lat-a.lat), radians(b.lon-a.lon)
    h = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
    return 6371000 * 2 * asin(sqrt(h))

def parse_gpx(data: bytes) -> tuple[str, list[Point]]:
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("Les DTD et entités XML sont interdites")
    try:
        root = ET.fromstring(data)
    except Exception as exc:
        raise ValueError("Fichier GPX ou XML invalide") from exc
    if not root.tag.endswith("gpx"):
        raise ValueError("Le document n'est pas un fichier GPX")
    name = next((e.text for e in root.iter() if e.tag.endswith("name") and e.text), "Parcours")
    points: list[Point] = []
    for node in root.iter():
        if not node.tag.endswith("trkpt"):
            continue
        try:
            lat, lon = float(node.attrib["lat"]), float(node.attrib["lon"])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180): raise ValueError
            ele_node = next((x for x in node if x.tag.endswith("ele")), None)
            ele = float(ele_node.text) if ele_node is not None and ele_node.text else None
            points.append(Point(lat, lon, ele))
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("Point GPX invalide") from exc
    if len(points) < 2:
        raise ValueError("La trace doit contenir au moins deux points")
    if len(points) > 200_000:
        raise ValueError("La trace contient trop de points")
    return name, points

def resample(points: list[Point], target_m: float) -> list[tuple[Point, Point]]:
    result: list[tuple[Point, Point]] = []
    start = points[0]
    accumulated = 0.0
    for current in points[1:]:
        accumulated += distance(start, current)
        if accumulated >= target_m:
            result.append((start, current)); start = current; accumulated = 0.0
    if start != points[-1]: result.append((start, points[-1]))
    return result

