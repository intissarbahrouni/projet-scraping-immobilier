Projet de Scraping Immobilier
Description
Ce projet automatise la collecte et la gestion des annonces immobilières du site tunisie-annonce.com. Il utilise un script de web scraping (scraper.py) pour extraire les données (titre, prix, type, localisation, etc.) des pages 149 à 280, et les sauvegarde dans un fichier JSON (data.json). Une API REST (api.py), construite avec FastAPI, permet de consulter ces données ou de déclencher un nouveau scraping. Ce système est conçu pour faciliter l'accès structuré aux informations immobilières pour des analyses ou une intégration future.

Structure du répertoire
.pycache/ : Dossier généré par Python contenant les fichiers bytecode.
venv/ : Environnement virtuel pour isoler les dépendances du projet.
.gitignore : Fichier pour exclure les dossiers/fichiers du contrôle de version (ex. : venv/, .pycache/).
api.py : Script Python contenant l'API REST (FastAPI) pour gérer les annonces.
data.json : Fichier JSON stockant les annonces scrapées.
requirements.txt : Liste des dépendances Python nécessaires.
scraper.py : Script Python pour scraper les annonces immobilières.
Prérequis
Python 3.8 ou supérieur.
Microsoft Edge installé (pour Selenium).
msedgedriver.exe (driver Edge) téléchargé et placé à C:\Program Files (x86)\msedgedriver.exe. Téléchargez-le depuis Microsoft Edge WebDriver.
Installation
Clonez ou téléchargez ce répertoire sur votre machine.
bash

Réduire

Envelopper

Copier
git clone <URL-du-dépôt>
Naviguez dans le répertoire du projet.
bash

Réduire

Envelopper

Copier
cd PROJET-SCRAPING-IMMOBILIER
Créez et activez un environnement virtuel (si venv/ n'existe pas déjà).
bash

Réduire

Envelopper

Copier
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
Installez les dépendances listées dans requirements.txt.
bash

Réduire

Envelopper

Copier
pip install -r requirements.txt
Vérifiez que msedgedriver.exe est présent au chemin spécifié dans scraper.py. Sinon, modifiez le chemin dans le script.
Utilisation
1. Lancer le scraping
Exécutez scraper.py pour collecter les annonces et les sauvegarder dans data.json.

bash

Réduire

Envelopper

Copier
python scraper.py
Le script scrape les pages 149 à 280 de tunisie-annonce.com.
Les données seront enregistrées dans data.json.
2. Lancer l'API
Exécutez api.py pour démarrer l'API REST.

bash

Réduire

Envelopper

Copier
python api.py
L'API sera accessible à http://localhost:8000.
Endpoints disponibles :
GET /annonces : Récupère toutes les annonces stockées dans data.json.
POST /scrape : Déclenche un nouveau scraping et met à jour data.json.
Consultez la documentation interactive à http://localhost:8000/docs (Swagger UI).
Exemple de requête API
Récupérer les annonces :
bash

Réduire

Envelopper

Copier
curl http://localhost:8000/annonces
Déclencher un nouveau scraping :
bash

Réduire

Envelopper

Copier
curl -X POST http://localhost:8000/scrape
Dépendances
Les principales bibliothèques utilisées (listées dans requirements.txt) :

selenium : Pour automatiser le navigateur Edge.
beautifulsoup4 : Pour parser le HTML.
fastapi : Pour créer l'API REST.
uvicorn : Serveur ASGI pour exécuter l'API.
requests : (Si utilisé pour des requêtes HTTP supplémentaires).
Limites
Le scraping est spécifique à la structure HTML de tunisie-annonce.com. Toute modification du site peut casser le script.
Le chemin du driver Edge (msedgedriver.exe) est fixe dans scraper.py et doit être adapté selon votre système.
Certains champs comme superficie et contact ne sont pas extraits.
Améliorations possibles
Ajouter une base de données (ex. : SQLite) pour remplacer data.json.
Extraire des champs supplémentaires (ex. : superficie) en explorant les pages de détail des annonces.
Implémenter des proxies ou un mode headless pour plus de discrétion lors du scraping.
Ajouter des filtres à l'API (ex. : GET /annonces?region=Tunis).
Avertissement
Ce projet est à des fins éducatives. Assurez-vous de respecter les conditions d'utilisation de tunisie-annonce.com et les lois locales sur le web scraping.
L'utilisation excessive peut entraîner un blocage par le site cible.
Auteur
[Votre nom]

Pour toute question, contactez [votre email ou autre moyen de contact].

Instructions pour l’utilisation
Créez un fichier nommé README.md à la racine de votre répertoire PROJET-SCRAPING-IMMOBILIER.
Copiez-collez le contenu ci-dessus dans ce fichier.
Remplacez [Votre nom] et [votre email ou autre moyen de contact] par vos informations personnelles.
Si vous avez un dépôt Git (ex. : sur GitHub), remplacez <URL-du-dépôt> par l’URL réelle de votre dépôt. Sinon, vous pouvez supprimer la commande git clone
