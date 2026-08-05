# Exploitation

## Sauvegarde

Depuis PowerShell : `./scripts/backup.ps1`. Les archives sont placées dans `backups/` et contiennent un dump PostgreSQL. Conserver une copie chiffrée hors machine et tester régulièrement la restauration.

## Restauration

Arrêter les écritures, sélectionner explicitement le dump, puis exécuter :

```powershell
Get-Content -Raw .\backups\gpxaccess-YYYYMMDD-HHMMSS.sql | docker compose exec -T db psql -U gpxaccess -d gpxaccess
```

Vérifier le nom de base et effectuer la restauration d'abord dans un environnement isolé. Redis est un cache et n'a pas besoin d'être restauré.

