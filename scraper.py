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
import requests
from requests.exceptions import Timeout

# Configuration des options de Edge
edge_options = Options()
edge_options.add_argument("--disable-blink-features=AutomationControlled")
edge_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
edge_options.add_argument('--ignore-certificate-errors')

# Chemin vers msedgedriver.exe
PATH = "C:\\Program Files (x86)\\msedgedriver.exe"

# Initialiser le WebDriver avec Edge
try:
    driver = webdriver.Edge(service=Service(PATH), options=edge_options)
    print("WebDriver initialisé.")
except Exception as e:
    print(f"Erreur lors du chargement du pilote Edge : {e}")
    exit()

# Générer un nom de fichier JSON unique basé sur la date et l'heure actuelles
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
json_file = f"proprietes_janv_fev_2025_{current_time}.json"

# Liste pour stocker les annonces immobilières
properties_list = []

# Fonction pour récupérer les annonces d'une page
def get_properties_from_page(url, page_num):
    """Récupère les annonces immobilières depuis une page donnée."""
    try:
        driver.get(url)
        # Attendre que la table soit présente (timeout réduit pour éviter de longues attentes)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "Tableau1")))
        time.sleep(random.uniform(3, 7))  # Délai aléatoire réduit
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll jusqu’en bas
        time.sleep(random.uniform(3, 7))  # Attendre le chargement dynamique

        # Récupérer la source de la page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        print(f"Aperçu de la page {page_num} source (premiers 1000 caractères) :")
        print(driver.page_source[:1000])

        # Recherche des lignes de la table avec la classe "Tableau1"
        rows = soup.find_all("tr", class_="Tableau1")

        if not rows:
            print(f"Aucune annonce trouvée sur la page {page_num} avec le sélecteur 'Tableau1'.")
            return True  # Continuez à la page suivante même si aucune annonce n'est trouvée

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 12:
                continue  # Ignore les lignes qui ne contiennent pas assez de colonnes

            # Extraction des données
            region = cells[1].get_text(strip=True) or "Région non trouvée"
            nature = cells[3].get_text(strip=True) or "Nature non trouvée"
            property_type = cells[5].get_text(strip=True) or "Type non trouvé"
            description_link = cells[7].find("a")
            description = description_link.get_text(strip=True) if description_link else "Description non trouvée"
            price = cells[9].get_text(strip=True) or "Prix non trouvé"
            modified_date_str = cells[11].get_text(strip=True) or "Date non trouvée"

            # Vérification et filtrage par date (janvier ou février 2025)
            try:
                modified_date = datetime.strptime(modified_date_str, "%d/%m/%Y")
                if modified_date.year == 2025 and modified_date.month in [1, 2]:  # Janvier ou Février 2025
                    # Création du dictionnaire pour l’annonce
                    property_data = {
                        "region": region,
                        "nature": nature,
                        "type": property_type,
                        "description": description,
                        "price": price,
                        "modified_date": modified_date_str,
                        "link": f"http://www.tunisie-annonce.com/{description_link['href']}" if description_link else "Lien non trouvé"
                    }
                    properties_list.append(property_data)

                    # Affichage des informations récupérées
                    print(f"Région: {region}")
                    print(f"Nature: {nature}")
                    print(f"Type: {property_type}")
                    print(f"Description: {description}")
                    print(f"Prix: {price}")
                    print(f"Date modifiée: {modified_date_str}")
                    print(f"Lien: {property_data['link']}")
                    print("-" * 40)
            except ValueError:
                print(f"Date invalide sur la page {page_num}: {modified_date_str}")
                continue

        return True  # Indique que la page a été traitée avec succès

    except Timeout:
        print(f"Timeout lors de la récupération de la page {page_num}.")
        return True  # Continue malgré le timeout
    except Exception as e:
        print(f"Erreur lors de la récupération des annonces de la page {page_num} : {e}")
        print(f"Source de la page {page_num} pour débogage :")
        print(driver.page_source[:1000])
        return True  # Continue même en cas d'erreur pour ne pas arrêter le scraping

# Scraping des annonces immobilières pour toutes les pages
try:
    base_url = "http://www.tunisie-annonce.com/AnnoncesImmobilier.asp"
    max_pages = 100  # Limite arbitraire, ajustez si nécessaire ou détectez dynamiquement

    # Vérifier la première page
    print("Récupération des annonces de la page 0 (première page)...")
    get_properties_from_page(base_url, 0)

    # Boucle sur toutes les pages
    page = 1
    while page <= max_pages:
        url = f"{base_url}?rech_page={page}"
        print(f"Récupération des annonces de la page {page}...")
        if not get_properties_from_page(url, page):
            print(f"Arrêt volontaire à la page {page}.")
            break
        # Vérifier si la page contient un indicateur de "dernière page" (par exemple, absence de lien "suivant")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        next_link = soup.find("a", text="Suivante")  # Ajustez selon la structure réelle du site
        if not next_link and page > 1:  # Si pas de lien "Suivante" et ce n'est pas la première page
            print(f"Probable dernière page détectée à {page}.")
            break
        page += 1

    # Sauvegarde des données dans un fichier JSON
    if properties_list:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties_list, f, ensure_ascii=False, indent=4)
        print(f"Les annonces ont été enregistrées dans {json_file}.")
    else:
        print("Aucune donnée pour janvier ou février 2025 à enregistrer.")

except Exception as e:
    print(f"Erreur lors du scraping : {e}")
finally:
    driver.quit()
    print("WebDriver fermé.")