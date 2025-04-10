from fastapi import FastAPI, HTTPException
import json
import os
from typing import List, Dict
from scraper import scrape_data  # Importer la fonction de scraping

app = FastAPI(
    title="API de Scraping Immobilier",
    description="API pour gérer les annonces immobilières collectées",
    version="1.0.0"
)

# Chemin vers le fichier JSON
DATA_PATH = "data.json"

def load_annonces() -> List[Dict]:
    """
    Charge les annonces depuis le fichier data.json.
    
    Returns:
        List[Dict]: Liste des annonces sous forme de dictionnaires.
        
    Raises:
        HTTPException: Si une erreur survient lors de la lecture du fichier.
    """
    if not os.path.exists(DATA_PATH):
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des annonces : {str(e)}")

def save_annonces(annonces: List[Dict]):
    """
    Sauvegarde les annonces dans le fichier data.json.
    
    Args:
        annonces (List[Dict]): Liste des annonces à sauvegarder.
        
    Raises:
        HTTPException: Si une erreur survient lors de l'écriture dans le fichier.
    """
    try:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(annonces, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde des annonces : {str(e)}")

@app.get("/annonces", response_model=List[Dict])
async def get_annonces():
    """
    Retourne toutes les annonces collectées.
    
    Returns:
        List[Dict]: Liste des annonces au format JSON.
        
    Raises:
        HTTPException: Si aucune annonce n'est trouvée (404) ou en cas d'erreur (500).
    """
    annonces = load_annonces()
    if not annonces:
        raise HTTPException(status_code=404, detail="Aucune annonce trouvée")
    return annonces

@app.post("/scrape")
async def scrape_new_data():
    """
    Lance une nouvelle session de scraping et met à jour les annonces.
    
    Returns:
        Dict: Message de confirmation et nombre total d'annonces.
        
    Raises:
        HTTPException: Si une erreur survient lors du scraping (500).
    """
    try:
        new_annonces = scrape_data()  # Appel à la fonction de scraping
        save_annonces(new_annonces)
        return {"message": "Scraping terminé avec succès", "total_annonces": len(new_annonces)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du scraping : {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)