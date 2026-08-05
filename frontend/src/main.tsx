import React,{useEffect,useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {GeoJSON,MapContainer,Marker,Popup,TileLayer,useMap,useMapEvents} from 'react-leaflet';
import L from 'leaflet';
import type {Feature,FeatureCollection,Point} from 'geojson';
import 'leaflet/dist/leaflet.css';
import './style.css';
import './options.css';

type Result={name:string;profile:string;warning:string;source_status:string;statistics:{distance_m:number;ascent_m:number;uncertain_percent:number;coverage_percent:number;by_class_m:Record<string,number>};geojson:FeatureCollection};
type BaseMap='standard'|'topo'|'humanitarian'|'satellite';
type PointKind='access'|'start'|'aid'|'vehicle'|'danger'|'other';
type Tool={mode:'none'}|{mode:'add';kind:PointKind}|{mode:'streetview'};
type OperationalPoint={id:string;kind:PointKind;lat:number;lon:number};

const colors:Record<string,string>={green:'#1f9d55',orange:'#e79024',red:'#d64242',gray:'#7a8491'};
const pointTypes:Record<PointKind,{icon:string;label:string;color:string}>={
  access:{icon:'🚑',label:'Accès secours',color:'#087f5b'},start:{icon:'🏁',label:'Départ',color:'#2267a8'},
  aid:{icon:'✚',label:'Poste de secours',color:'#d93434'},vehicle:{icon:'🚒',label:'Véhicule',color:'#e36b18'},
  danger:{icon:'⚠',label:'Danger / obstacle',color:'#b42318'},other:{icon:'●',label:'Autre repère',color:'#5e4aa8'}
};
const maps:Record<BaseMap,{url:string;attribution:string;maxZoom?:number}>={
  standard:{url:'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',attribution:'© OpenStreetMap contributors'},
  topo:{url:'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',attribution:'© OpenStreetMap · SRTM | OpenTopoMap',maxZoom:17},
  humanitarian:{url:'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',attribution:'© OpenStreetMap contributors · HOT'},
  satellite:{url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',attribution:'Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics et partenaires',maxZoom:19}
};

function validCoordinate(node:Element):[number,number]|undefined{const lon=Number(node.getAttribute('lon'));const lat=Number(node.getAttribute('lat'));return Number.isFinite(lon)&&Number.isFinite(lat)&&lon>=-180&&lon<=180&&lat>=-90&&lat<=90?[lon,lat]:undefined}
function reduceLine(line:[number,number][],limit:number){if(line.length<=limit)return line;const step=Math.ceil(line.length/limit);const reduced=line.filter((_,index)=>index%step===0);if(reduced[reduced.length-1]!==line[line.length-1])reduced.push(line[line.length-1]);return reduced}
async function parsePreview(file:File):Promise<FeatureCollection>{
  if(file.size>10*1024*1024)throw Error('Fichier trop volumineux (maximum 10 Mo)');
  const xml=new DOMParser().parseFromString(await file.text(),'application/xml');
  if(xml.querySelector('parsererror'))throw Error('Fichier GPX invalide');
  let lines=Array.from(xml.querySelectorAll('trkseg')).map(seg=>Array.from(seg.querySelectorAll('trkpt')).map(validCoordinate).filter((p):p is [number,number]=>Boolean(p))).filter(line=>line.length>1);
  if(!lines.length){const route=Array.from(xml.querySelectorAll('rtept')).map(validCoordinate).filter((p):p is [number,number]=>Boolean(p));if(route.length>1)lines=[route]}
  if(!lines.length)throw Error('Aucune trace exploitable dans ce GPX');
  const limit=Math.max(500,Math.floor(6000/lines.length));lines=lines.map(line=>reduceLine(line,limit));
  return {type:'FeatureCollection',features:lines.map(line=>({type:'Feature',properties:{preview:true},geometry:{type:'LineString',coordinates:line}}))};
}
function FitTrace({data}:{data?:FeatureCollection}){const map=useMap();useEffect(()=>{if(!data?.features.length)return;try{const bounds=L.geoJSON(data).getBounds();if(bounds.isValid())map.fitBounds(bounds,{padding:[28,28],maxZoom:18})}catch{ /* Le reste de l'interface doit rester disponible. */ }},[data,map]);return null}
function MapActions({tool,onAdd,onCoordinate}:{tool:Tool;onAdd:(lat:number,lon:number,kind:PointKind)=>void;onCoordinate:(lat:number,lon:number)=>void}){useMapEvents({click(e){onCoordinate(e.latlng.lat,e.latlng.lng);if(tool.mode==='add')onAdd(e.latlng.lat,e.latlng.lng,tool.kind);if(tool.mode==='streetview'){const point=`${e.latlng.lat},${e.latlng.lng}`;window.open(`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${encodeURIComponent(point)}`,'_blank','noopener,noreferrer')}}});return null}
function Locate({request,onFound}:{request:number;onFound:(lat:number,lon:number)=>void}){const map=useMap();useEffect(()=>{if(!request)return;map.locate({setView:true,maxZoom:17,enableHighAccuracy:true});const found=(e:L.LocationEvent)=>onFound(e.latlng.lat,e.latlng.lng);map.once('locationfound',found);return()=>{map.off('locationfound',found)}},[request,map,onFound]);return null}
function markerIcon(kind:PointKind){const type=pointTypes[kind];return L.divIcon({className:'op-marker-wrap',html:`<span class="op-marker" style="--marker:${type.color}">${type.icon}</span>`,iconSize:[36,42],iconAnchor:[18,38],popupAnchor:[0,-38]})}

function loadPoints():OperationalPoint[]{try{const value=JSON.parse(localStorage.getItem('gpx-operational-points')||'[]');if(!Array.isArray(value))return[];return value.filter((p):p is OperationalPoint=>p&&typeof p.id==='string'&&p.kind in pointTypes&&Number.isFinite(p.lat)&&Number.isFinite(p.lon))}catch{return[]}}
class MapErrorBoundary extends React.Component<React.PropsWithChildren,{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return{failed:true}}render(){return this.state.failed?<div className="map-fallback"><b>La carte n’a pas pu afficher ce fichier.</b><span>Le GPX est peut-être trop complexe ou contient une géométrie invalide.</span><button onClick={()=>location.reload()}>Recharger l’application</button></div>:this.props.children}}

function App(){
  const [file,setFile]=useState<File>();const [preview,setPreview]=useState<FeatureCollection>();const [result,setResult]=useState<Result>();const [error,setError]=useState('');const [loading,setLoading]=useState(false);const [profile,setProfile]=useState('standard');const [baseMap,setBaseMap]=useState<BaseMap>('standard');const [tool,setTool]=useState<Tool>({mode:'none'});const [coordinate,setCoordinate]=useState<[number,number]>();const [locateRequest,setLocateRequest]=useState(0);
  const [points,setPoints]=useState<OperationalPoint[]>(loadPoints);
  const displayed=useMemo(()=>result?.geojson||preview,[result,preview]);
  useEffect(()=>localStorage.setItem('gpx-operational-points',JSON.stringify(points)),[points]);
  async function selectFile(next?:File){setFile(next);setResult(undefined);setPreview(undefined);setError('');if(!next)return;try{setPreview(await parsePreview(next))}catch(e){setError(e instanceof Error?e.message:'Aperçu impossible')}}
  async function run(){if(!file)return;setLoading(true);setError('');const body=new FormData();body.append('file',file);try{const query=new URLSearchParams({profile});const r=await fetch(`/api/v1/analyze?${query}`,{method:'POST',body});const j=await r.json();if(!r.ok)throw Error(j.detail||'Analyse impossible');setResult(j)}catch(e){setError(e instanceof Error?e.message:'Erreur')}finally{setLoading(false)}}
  function addPoint(lat:number,lon:number,kind:PointKind){const id=globalThis.crypto?.randomUUID?.()||`${Date.now()}-${Math.random()}`;setPoints(old=>[...old,{id,kind,lat,lon}])}
  function download(){const markerFeatures:Feature<Point>[] = points.map(p=>({type:'Feature',geometry:{type:'Point',coordinates:[p.lon,p.lat]},properties:{type:p.kind,label:pointTypes[p.kind].label}}));const geojson:FeatureCollection={type:'FeatureCollection',features:[...(result?.geojson.features||preview?.features||[]),...markerFeatures]};const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(geojson,null,2)],{type:'application/geo+json'}));a.download=`${result?.name||'carte-operationnelle'}.geojson`;a.click();URL.revokeObjectURL(a.href)}
  function copyCoordinate(){if(coordinate)navigator.clipboard.writeText(`${coordinate[0].toFixed(6)}, ${coordinate[1].toFixed(6)}`)}
  return <main><header><div><span className="mark">✚</span><b>GPX Accès</b><small>Préparation opérationnelle</small></div><span className="badge">Profil · {profile==='standard'?'VL standard':profile==='suv'?'4×4 / SUV':'Secours'}</span></header><section className="layout"><aside><h1>Analyser un parcours</h1><p className="muted">Importez une trace GPX : elle apparaît immédiatement sur la carte.</p><label className="drop"><strong>Déposer un fichier GPX</strong><span>{file?.name||'ou cliquer pour parcourir'}</span><input type="file" accept=".gpx,application/gpx+xml" onChange={e=>selectFile(e.target.files?.[0])}/></label>
  <div className="options"><label>Profil véhicule<select value={profile} onChange={e=>setProfile(e.target.value)}><option value="standard">VL standard</option><option value="suv">4×4 / SUV</option><option value="emergency">Véhicule de secours</option></select></label><label>Fond de carte<select value={baseMap} onChange={e=>setBaseMap(e.target.value as BaseMap)}><option value="standard">Plan OSM</option><option value="satellite">Satellite</option><option value="topo">Topographique</option><option value="humanitarian">Humanitaire détaillé</option></select></label></div><button disabled={!file||loading||!preview} onClick={run}>{loading?'Analyse cartographique en cours…':'Lancer l’analyse'}</button>{error&&<p className="error">{error}</p>}{result?.source_status==='degraded'&&<p className="error">Les services cartographiques sont momentanément indisponibles : le tracé reste visible, mais l’analyse est incomplète.</p>}
  <hr/><h2>Outils opérationnels</h2><p className="hint">Choisissez un repère puis cliquez sur la carte.</p><div className="point-tools">{(Object.keys(pointTypes) as PointKind[]).map(kind=><button key={kind} className={tool.mode==='add'&&tool.kind===kind?'active':''} onClick={()=>setTool({mode:'add',kind})}><span>{pointTypes[kind].icon}</span>{pointTypes[kind].label}</button>)}</div><div className="map-tools"><button className={tool.mode==='streetview'?'active':''} onClick={()=>setTool({mode:'streetview'})}>◉ Street View</button><button onClick={()=>setLocateRequest(x=>x+1)}>⌖ Ma position</button><button onClick={()=>setTool({mode:'none'})}>↖ Navigation</button></div>{coordinate&&<button className="coordinate" onClick={copyCoordinate}>📋 {coordinate[0].toFixed(5)}, {coordinate[1].toFixed(5)}</button>}<div className="tool-footer"><button disabled={!points.length} onClick={()=>setPoints([])}>Effacer les repères</button><button disabled={!displayed&&!points.length} onClick={download}>Exporter la carte</button></div>
  <hr/><h2>Légende de l’analyse</h2>{[['green','Accessible en VL'],['orange','Probablement accessible'],['red','Non accessible'],['gray','Données insuffisantes']].map(([c,t])=><p className="legend" key={c}><i style={{background:colors[c]}}/> {t}</p>)}<div className="warning">⚠ Résultat indicatif. Vérifiez barrières, restrictions, largeur et état du terrain.</div></aside>
  <article className={`tool-${tool.mode}`}><MapContainer center={[45.18,5.72]} zoom={11}><TileLayer key={baseMap} attribution={maps[baseMap].attribution} url={maps[baseMap].url} maxZoom={maps[baseMap].maxZoom}/><FitTrace data={displayed}/><MapActions tool={tool} onAdd={addPoint} onCoordinate={(lat,lon)=>setCoordinate([lat,lon])}/><Locate request={locateRequest} onFound={(lat,lon)=>setCoordinate([lat,lon])}/>{displayed&&<GeoJSON key={`${file?.name}-${result?'result':'preview'}`} data={displayed} style={f=>({color:f?.properties?.preview?'#2878b8':colors[String(f?.properties?.classification)]||colors.gray,weight:result?6:5,dashArray:result?undefined:'8 7'})} onEachFeature={(f,l)=>{if(f.properties&&!f.properties.preview)l.bindPopup(`<b>Score ${f.properties.score}/100</b><br>${(f.properties.reasons||[]).join('<br>')}`)}}/>}{points.map(p=><Marker key={p.id} position={[p.lat,p.lon]} icon={markerIcon(p.kind)} draggable eventHandlers={{dragend:e=>{const ll=e.target.getLatLng();setPoints(old=>old.map(x=>x.id===p.id?{...x,lat:ll.lat,lon:ll.lng}:x))}}}><Popup><b>{pointTypes[p.kind].icon} {pointTypes[p.kind].label}</b><br/>{p.lat.toFixed(6)}, {p.lon.toFixed(6)}<br/><button className="popup-delete" onClick={()=>setPoints(old=>old.filter(x=>x.id!==p.id))}>Supprimer</button></Popup></Marker>)}</MapContainer>{result&&<section className="stats"><div><small>PARCOURS</small><b>{result.name}</b></div><div><small>DISTANCE</small><b>{(result.statistics.distance_m/1000).toFixed(1)} km</b></div><div><small>DÉNIVELÉ +</small><b>{result.statistics.ascent_m.toFixed(0)} m</b></div><div><small>COUVERTURE CARTO</small><b>{result.statistics.coverage_percent}%</b></div><div><small>INCERTAIN</small><b>{result.statistics.uncertain_percent}%</b></div></section>}</article></section></main>
}
createRoot(document.getElementById('root')!).render(<MapErrorBoundary><App/></MapErrorBoundary>);
