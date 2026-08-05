# GPX Accès Secours

MVP auto-hébergé d'analyse **indicative** de l'accessibilité d'un parcours GPX pour un VL. Il affiche la trace, interroge OpenStreetMap via Overpass côté serveur, classe les portions et exporte le résultat en GeoJSON.

> Cette analyse ne constitue jamais une autorisation ni une garantie de passage. Une reconnaissance terrain reste indispensable (barrières, propriété privée, largeur réelle, météo, boue, neige, végétation et dégradations récentes).

## Démarrage

Prérequis : Docker et Docker Compose.

```bash
docker compose up -d --build
```

Toute la configuration se trouve dans `docker-compose.yml`. Les mots de passe PostgreSQL et administrateur y sont déjà initialisés avec des valeurs robustes. Restreignez l'accès à ce fichier et renouvelez ces secrets s'il est partagé.

Ouvrir `http://localhost:3117`. État de l'API : `http://localhost:3117/api/health`; OpenAPI : `http://localhost:3117/api/docs`.

Le navigateur ne contacte jamais Overpass directement. Si tous les fournisseurs échouent, l'analyse est rendue en gris, avec un statut dégradé, plutôt que d'inventer un résultat.

## Développement et tests

```bash
cd backend
python -m pip install -e ".[dev]"
pytest
ruff check app tests

cd ../frontend
npm install
npm run build
```

Essayez [demo.gpx](tests/data/demo.gpx). La longueur de segmentation est réglable entre 10 et 100 m dans l'API.

## Exploitation

- Les ports PostgreSQL et Redis ne sont pas publiés.
- La configuration et les secrets sont déclarés directement dans `docker-compose.yml`, conformément au mode de déploiement retenu. Restreignez l'accès à ce fichier.
- Le conteneur backend tourne sans privilèges.
- Nginx limite l'import à 10 Mo et pose les principaux en-têtes de sécurité.
- Sauvegarde : `./scripts/backup.ps1`; restauration documentée dans [operations.md](docs/operations.md).
- HTTPS doit être terminé par le reverse proxy de l'hébergeur (Traefik, Caddy ou Nginx externe).

## Périmètre du MVP

Inclus : GPX, carte OSM, Overpass avec deux fournisseurs, analyse explicable VL, pente si altitude présente, statistiques, mode dégradé, export GeoJSON, Docker/PostGIS/Redis/worker, tests de parsing et classification.

Le schéma PostGIS, les comptes, projets persistants, profils supplémentaires, corrections, points d'accès et PDF appartiennent à l'étape 2. Les conteneurs de données et worker sont présents pour permettre cette évolution sans refonte. Voir [architecture.md](docs/architecture.md) et [limitations.md](docs/limitations.md).
