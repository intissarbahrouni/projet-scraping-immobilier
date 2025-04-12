# Projet de Scraping et Visualisation des Annonces Immobilières

## Description du projet
Ce projet vise à collecter, analyser et visualiser des annonces immobilières à partir du site **Tayara.tn**. Il utilise le scraping pour extraire les données, une base de données **PostgreSQL** hébergée sur **Supabase** pour les stocker, et un tableau de bord interactif construit avec Dash pour les visualiser. L'objectif est de fournir une interface utilisateur permettant d'explorer les annonces et d'analyser les tendances immobilières en Tunisie.

### Fonctionnalités principales :
- **Scraping** : Extraction des annonces immobiliéres (titre, prix, type, localisation, date de publication, lien) depuis Tunisieannonces.tn.
- **Stockage** : Chargement des données dans une base de données **PostgreSQL** sur **Supabase**.
- **Visualisation** :
  - **KPIs** : Nombre total d'annonces, prix moyen, localisation la plus fréquente, date la plus récente, nombre de types distincts d'immobilier.
  - **Graphiques** :
    - Répartition des types d'immobiliers (diagramme en donut).
    - Répartition des localisations (diagramme en camembert).
    - Prix moyen par localisation (graphique en barres verticales avec échelle logarithmique).
    -Top 5 des annonces les plus chères : diag en barres horizontal titre, prix, localisation.
    -Top 5 des annonces les plus basses : diag en barres horizontal titre, prix, localisation.
    -Tableau qui montre Prix min/max : MIN(prix) et MAX(prix) globaux  par localisation.

  - **Tableau interactif** : Exploration des annonces avec options de tri (par prix, date) et filtres (type, localisation, plage de prix, plage de dates).
  
## Prérequis
- Python 3.8 ou supérieur
- Un compte **Supabase** (pour héberger la base de données **PostgreSQL**)
- Accès à Internet (pour le scraping et la connexion à Supabase)

## Installation
1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/votre-utilisateur/projet-scraping-immobilier.git
   cd projet-scraping-immobilier
2. **Installer les dépendances :**
   pip install -r requirements.txt
 installez manuellement les dépendances suivantes :pip install requests beautifulsoup4 pandas sqlalchemy psycopg2-binary dash plotly dash-table
3. **Accés a la base de données:**
Configurer la connexion à la base de données PostgreSQL sur Supabase :
DATABASE_URL = "postgresql://postgres.lpdyhnlgdpnheclcpzzg:[VOTRE-MOT-DE-PASSE]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

## Execution

1. **Scraper les données:**
    python scraper.py
2.**Charger les données dans la base de données PostgreSQL sur Supabase**
    python load_to_postgres.py
3. **Lancer le tableau de bord**
    python dashboard.py