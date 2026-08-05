from .gpx import Point, distance
from .models import Segment, WayInfo

FORBIDDEN = {"no", "private", "customers", "agricultural", "forestry"}
GOOD = {"motorway", "trunk", "primary", "secondary", "tertiary", "residential", "service", "unclassified"}
POOR = {"footway", "path", "steps", "pedestrian", "cycleway", "bridleway"}

def classify(index: int, a: Point, b: Point, way: WayInfo | None = None) -> Segment:
    d = distance(a, b); slope = None
    if a.ele is not None and b.ele is not None and d > 0: slope = abs(b.ele-a.ele)/d*100
    score, reasons, relation = 35, [], "unknown"
    if way:
        highway = way.tags.get("highway", "inconnu")
        if way.distance_m <= 12: score += 30; relation = "direct"; reasons.append(f"voie {highway} à {way.distance_m:.0f} m")
        elif way.distance_m <= 50: score += 15; relation = "nearby"; reasons.append(f"voie potentielle à proximité ({way.distance_m:.0f} m)")
        else: score -= 15; reasons.append("aucune voie proche")
        if highway in GOOD: score += 20
        if highway == "track": score += 5; reasons.append(f"piste {way.tags.get('tracktype', 'sans catégorie')}")
        if highway in POOR: score -= 35; reasons.append("type de voie défavorable à un VL")
        if any(way.tags.get(k) in FORBIDDEN for k in ("access", "vehicle", "motor_vehicle")):
            score -= 60; reasons.append("restriction automobile détectée")
        if way.tags.get("barrier") or way.tags.get("highway") == "steps": score -= 40; reasons.append("obstacle ou escalier détecté")
        surface = way.tags.get("surface")
        if surface in {"asphalt", "concrete", "paved"}: score += 10; reasons.append(f"surface {surface}")
        elif not surface: reasons.append("surface non renseignée")
    else: reasons.append("données cartographiques indisponibles")
    if slope is None: reasons.append("pente inconnue")
    elif slope > 20: score -= 35; reasons.append(f"pente forte ({slope:.0f} %)")
    elif slope > 12: score -= 15; reasons.append(f"pente à vérifier ({slope:.0f} %)")
    score = max(0, min(100, score))
    category = "gray" if way is None else "green" if score >= 70 else "orange" if score >= 45 else "red"
    return Segment(index=index, coordinates=[[a.lon,a.lat],[b.lon,b.lat]], distance_m=d,
        slope_percent=slope, score=score, classification=category, relation=relation,
        reasons=reasons, nearest_way=way)
