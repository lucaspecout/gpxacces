# Architecture technique

```text
Navigateur → Nginx → React/Vite
                  └→ FastAPI → Overpass (priorité + fallback)
                              → Redis / Celery (tâches longues, étape 2)
                              → PostgreSQL/PostGIS (persistance, étape 2)
```

Le module `gpx` valide et rééchantillonne les traces. `overpass` encapsule la source cartographique afin qu'une source OSM locale puisse ultérieurement implémenter la même interface. `classifier` est pur, déterministe et testé. Chaque résultat garde score, relation à la voie et motifs lisibles.

## Schéma cible (étape 2)

```text
organizations 1─* memberships *─1 users
organizations 1─* events 1─* tracks 1─* analyses 1─* segments
tracks 1─* access_points
tracks 1─* field_surveys 1─* photos
vehicle_profiles 1─* analyses
users 1─* audit_events
```

Les géométries `tracks`, `segments`, `access_points` seront en PostGIS (SRID 4326), avec index GiST. Les corrections manuelles seront stockées séparément des résultats automatiques afin de rester identifiables et auditables.

## Classification VL du MVP

Score initial 35. Une voie à moins de 12 m ajoute 30 points, à moins de 50 m 15. Une route carrossable ajoute 20, un revêtement dur 10. Sentiers, escaliers, restrictions automobiles et fortes pentes retirent des points. Seuils : vert ≥70, orange ≥45, rouge <45. Sans voie OSM, gris. La proximité est étiquetée séparément (`direct` ou `nearby`) ; la continuité du réseau sera ajoutée avec un graphe routable à l'étape 2.

