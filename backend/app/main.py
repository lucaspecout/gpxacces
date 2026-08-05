from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .classifier import classify
from .config import settings
from .gpx import distance, parse_gpx, resample
from .overpass import fetch_ways, nearest_way

app=FastAPI(title=settings.app_name, version="0.1.0", description="Analyse indicative d'accessibilité de parcours GPX.")
app.add_middleware(CORSMiddleware, allow_origins=[], allow_methods=["GET","POST"], allow_headers=["content-type"])

@app.get("/health")
def health(): return {"status":"ok"}

@app.post("/v1/analyze")
async def analyze(file: UploadFile=File(...), segment_length_m: float=settings.segment_length_m, profile: str="standard"):
    if not file.filename or not file.filename.lower().endswith(".gpx"):
        raise HTTPException(415,"Seuls les fichiers GPX sont acceptés")
    if not 10 <= segment_length_m <= 100: raise HTTPException(422,"La longueur doit être comprise entre 10 et 100 m")
    if profile not in {"standard","suv","emergency"}: raise HTTPException(422,"Profil véhicule inconnu")
    data=await file.read(settings.max_upload_mb*1024*1024+1)
    if len(data)>settings.max_upload_mb*1024*1024: raise HTTPException(413,"Fichier trop volumineux")
    try: name,points=parse_gpx(data)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    ways=await fetch_ways(points)
    pairs=resample(points,segment_length_m)
    segments=[]
    for i,(a,b) in enumerate(pairs): segments.append(classify(i,a,b,nearest_way(a,ways),profile))
    total=sum(distance(a,b) for a,b in zip(points,points[1:])); elevations=[p.ele for p in points if p.ele is not None]
    ascent=sum(max(0,b-a) for a,b in zip(elevations,elevations[1:]))
    by_class={c:sum(s.distance_m for s in segments if s.classification==c) for c in ("green","orange","red","gray")}
    geojson={"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"LineString","coordinates":s.coordinates},"properties":s.model_dump(exclude={"coordinates"})} for s in segments]}
    measured=sum(s.distance_m for s in segments); covered=sum(s.distance_m for s in segments if s.nearest_way and s.nearest_way.distance_m <= 60)
    labels={"standard":"VL standard","suv":"4×4 / SUV","emergency":"Véhicule de secours"}
    return {"name":name,"profile":labels[profile],"warning":"Analyse indicative : une reconnaissance terrain reste indispensable.","source_status":"online" if ways else "degraded","statistics":{"distance_m":round(total,1),"ascent_m":round(ascent,1),"elevation_min_m":min(elevations) if elevations else None,"elevation_max_m":max(elevations) if elevations else None,"by_class_m":{k:round(v,1) for k,v in by_class.items()},"coverage_percent":round(100*covered/measured,1) if measured else 0,"uncertain_percent":round(100*by_class["gray"]/sum(by_class.values()),1) if segments else 100},"geojson":geojson}

@app.exception_handler(HTTPException)
async def http_error(_,exc): return JSONResponse({"detail":exc.detail},status_code=exc.status_code)
