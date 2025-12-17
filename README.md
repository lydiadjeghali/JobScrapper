# Free-Work Job Scraper

Scrapeur d'offres tech UK depuis free-work.com. Extrait titres, entreprises, **salaires précis** (via sidebar Pay/Rate) et calcule KPI (tâches/salaire). Export CSV avec statistiques.

## Fonctionnalités

- Titres, entreprises, types de contrat
- **Parsing salaire précis** (£57k-85k → valeur numérique)
- Comptage tâches dans descriptions
- Calcul KPI : plus bas = meilleur rapport
- Pagination (3 pages par défaut)
- Gestion d'erreurs robuste

## Installation

pip install requests beautifulsoup4 pandas lxml


## Utilisation

python JobScraper.py


**Sortie** : `jobs_with_kpi.csv` + stats console (Jobs trouvées)

## Colonnes CSV

| Colonne | Description |
|---------|-------------|
| `titre` | Intitulé poste |
| `entreprise` | Nom société |
| `salaire` | Texte salaire brut |
| `salaire_num` | Valeur numérique (£) |
| `kpi_salaire_taches` | KPI taches/salaire |
| `lien` | URL offre |

## Personnalisation
scraper.scrape_job_list("https://www.free-work.com/en-gb/tech-it/jobs", max_pages=5) --- Nombre de pages
scraper.save_to_csv("mes_offres.csv") --- nom du fichier CSV
