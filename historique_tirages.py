import sqlite3
from datetime import datetime

class GestionnaireTirages:
    def __init__(self, db_name="historique_secret_santa.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initialise la base de données et crée la table des tirages."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Table pour enregistrer chaque association de tirage au sort avec une date et un identifiant de session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historique_tirages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                donateur TEXT NOT NULL,
                receveur TEXT NOT NULL,
                date_tirage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def enregistrer_tirage(self, session_id, attributions):
        """
        Enregistre un tirage complet (dictionnaire giver: receiver) 
        associé à un identifiant de session (ex: 'Noel_2026').
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        date_actuelle = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for donateur, receveur in attributions.items():
            cursor.execute("""
                INSERT INTO historique_tirages (session_id, donateur, receveur, date_tirage)
                VALUES (?, ?, ?, ?)
            """, (session_id, donateur, receveur, date_actuelle))
            
        conn.commit()
        conn.close()
        print(f"💾 [Base de données] Tirage de la session '{session_id}' enregistré avec succès !")

    def voir_historique(self):
        """Affiche tous les tirages au sort passés et présents enregistrés dans la base."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT session_id, donateur, receveur, date_tirage FROM historique_tirages ORDER BY date_tirage DESC")
        resultats = cursor.fetchall()
        conn.close()

        if resultats:
            print("\n📜 --- HISTORIQUE DE TOUS LES TIRAGES AU SORT ---")
            session_actuelle = ""
            for session_id, donateur, receveur, date in resultats:
                if session_id != session_actuelle:
                    session_actuelle = session_id
                    print(f"\n🏷️ Session : {session_id} (Effectué le {date})")
                print(f"   • {donateur} offre un cadeau à ➔ {receveur}")
            print("\n-----------------------------------------------\n")
        else:
            print("📭 Aucun tirage enregistré pour le moment.")


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    archive = GestionnaireTirages()

    # Simulation d'un tirage au sort avec vos participants
    Paires_2026 = {
        "Claire": "Téo",
        "Stephane": "Corentin",
        "Sandra": "Baptiste",
        "Corentin": "Claire",
        "Eva": "Stephane",
        "Baptiste": "Sandra",
        "Téo": "Eva"
    }

    # 1. Sauvegarder ce tirage dans la base de données
    archive.enregistrer_tirage("Noel_2026_Officiel", Paires_2026)

    # 2. Consulter l'historique complet stocké
    archive.voir_historique()