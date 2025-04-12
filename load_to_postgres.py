# load_to_postgres.py
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Remplacez cette ligne par votre URL de connexion Supabase
# DATABASE_URL = "postgresql://postgres:[secretdbprojectml]@db.lpdyhnlgdpnheclcpzzg.supabase.co:5432/postgres"  # <- METTEZ VOTRE URL ICI

DATABASE_URL = "postgresql://postgres.lpdyhnlgdpnheclcpzzg:B5BEKdICOZVYMp2m@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("Connexion réussie à la base de données !")
    connection.close()
except Exception as e:
    print(f"Erreur de connexion : {e}")

# Configuration de la connexion

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modèle de la table Annonce
class Annonce(Base):
    __tablename__ = "annonces"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String)
    prix = Column(Float)  # Changé en Float
    type = Column(String)
    localisation = Column(String)
    superficie = Column(String)
    description = Column(String)
    contact = Column(String)
    date_publication = Column(Date)  # Changé en Date
    lien = Column(String)

# Créer la table dans la base de données
Base.metadata.create_all(bind=engine)

def load_json_to_postgres():
    # Charger le fichier data.json
    with open("data.json", "r", encoding="utf-8") as f:
        annonces = json.load(f)

    # Connexion à la base de données
    db = SessionLocal()
    try:
        # Insérer chaque annonce dans la table
        for annonce in annonces:
            # Convertir le prix en float (en supprimant les espaces)
            prix_str = annonce["prix"].replace(" ", "")  # "230 000" -> "230000"
            prix_float = float(prix_str)  # Convertir en float

            # Convertir la date en format DATE (de "20/01/2025" à objet date)
            date_str = annonce["date_publication"]  # "20/01/2025"
            date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()  # Convertir en objet date

            # Créer l'objet Annonce avec les types corrects
            db_annonce = Annonce(
                titre=annonce["titre"],
                prix=prix_float,  # Float
                type=annonce["type"],
                localisation=annonce["localisation"],
                superficie=annonce["superficie"],
                description=annonce["description"],
                contact=annonce["contact"],
                date_publication=date_obj,  # Date
                lien=annonce["lien"]
            )
            db.add(db_annonce)
        db.commit()
        print(f"{len(annonces)} annonces chargées avec succès dans PostgreSQL.")
    except Exception as e:
        db.rollback()
        print(f"Erreur lors du chargement : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_json_to_postgres()