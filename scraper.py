from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
from selenium.webdriver.edge.options import Options
import time
import random
import json
import os

def init_driver():
    """
    Initialise le driver Microsoft Edge avec des options pour éviter la détection de bot.
    
    Returns:
        WebDriver: Instance du driver Edge.
        
    Raises:
        FileNotFoundError: Si le fichier msedgedriver.exe n'est pas trouvé.
    """
    edge_options = Options()
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    edge_options.add_argument('--ignore-certificate-errors')
    PATH = "C:\\Program Files (x86)\\msedgedriver.exe"
    if not os.path.exists(PATH):
        raise FileNotFoundError(
            f"msedgedriver.exe non trouvé à {PATH}. Téléchargez-le depuis https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/."
        )
    return webdriver.Edge(service=Service(PATH), options=edge_options)

def scrape_data():
    """
    Scrape les annonces immobilières sur le site tunisie-annonce.com entre les pages 149 et 280.
    
    Returns:
        List[Dict]: Liste des annonces collectées sous forme de dictionnaires.
    """
    driver = init_driver()
    properties_list = []
    base_url = "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp"
    start_page = 149
    end_page = 280
    json_file = "data.json"

    try:
        for page in range(start_page, end_page + 1):
            url = f"{base_url}?rech_page={page}"
            print(f"Récupération des annonces de la page {page}...")
            driver.get(url)
            print(f"Page {page} chargée.")
            
            # Attendre que le tableau soit présent
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "Tableau1")))
            print(f"Tableau trouvé sur la page {page}.")
            
            # Ajouter un délai aléatoire pour éviter la détection
            time.sleep(random.uniform(3, 7))
            
            # Faire défiler la page pour charger tout le contenu
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(3, 7))

            # Parser la page avec BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            rows = soup.find_all("tr", class_="Tableau1")
            print(f"Nombre de lignes trouvées sur la page {page} : {len(rows)}")

            if not rows:
                print(f"Aucune annonce trouvée sur la page {page}. Arrêt possible.")
                break

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 12:
                    continue

                # Extraire les informations de chaque cellule
                region = cells[1].get_text(strip=True) or "Région non trouvée"
                nature = cells[3].get_text(strip=True) or "Nature non trouvée"
                property_type = cells[5].get_text(strip=True) or "Type non trouvé"
                description_link = cells[7].find("a")
                description = description_link.get_text(strip=True) if description_link else "Description non trouvée"
                price = cells[9].get_text(strip=True) or "Prix non trouvé"
                modified_date_str = cells[11].get_text(strip=True) or "Date non trouvée"

                # Créer le dictionnaire de l'annonce
                property_data = {
                    "titre": description,
                    "prix": price,
                    "type": property_type,
                    "localisation": region,
                    "superficie": "Non disponible",
                    "description": description,
                    "contact": "Non disponible",
                    "date_publication": modified_date_str,
                    "lien": f"http://www.tunisie-annonce.com/{description_link['href']}" if description_link else "Lien non trouvé"
                }
                properties_list.append(property_data)

                # Afficher les détails de l'annonce pour le débogage
                print(f"Titre : {property_data['titre']}")
                print(f"  Prix : {property_data['prix']}")
                print(f"  Type : {property_data['type']}")
                print(f"  Localisation : {property_data['localisation']}")
                print(f"  Superficie : {property_data['superficie']}")
                print(f"  Description : {property_data['description']}")
                print(f"  Contact : {property_data['contact']}")
                print(f"  Date de publication : {property_data['date_publication']}")
                print("-" * 40)

            # Ajouter un délai pour éviter de surcharger le serveur
            time.sleep(10)

        # Sauvegarder dans le fichier JSON à la fin
        if properties_list:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(properties_list, f, ensure_ascii=False, indent=4)
            print(f"Données enregistrées dans {json_file}. Total d'annonces : {len(properties_list)}")
            return properties_list
        else:
            print("Aucune donnée trouvée entre les pages 149 et 280.")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            print(f"Fichier vide enregistré dans {json_file}.")
            return []

    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        if properties_list:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(properties_list, f, ensure_ascii=False, indent=4)
            print(f"Données partielles enregistrées dans {json_file}. Total d'annonces : {len(properties_list)}")
        return properties_list
    finally:
        driver.quit()
        print("Navigateur fermé.")

if __name__ == "__main__":
    scrape_data()