import sqlite3
from datetime import datetime

class AgentMemoireTotale:
    def __init__(self, db_name="memoire_agent.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initialise la base de données de l'agent."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memoire (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cle TEXT UNIQUE NOT NULL,
                valeur TEXT NOT NULL,
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def retenir(self, cle, valeur):
        """Enregistre ou met à jour une information dans la mémoire de l'agent."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memoire (cle, valeur, date_ajout) 
            VALUES (?, ?, ?)
        """, (cle.lower().strip(), valeur, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        print(f"🧠 [Agent] C'est noté ! J'ai enregistré : « {cle} » -> « {valeur} »")

    def se_souvenir(self, cle):
        """Retrouve une information précise stockée dans sa mémoire."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT valeur, date_ajout FROM memoire WHERE cle = ?", (cle.lower().strip(),))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"🤖 [Agent] Je m'en souviens ! (Enregistré le {result[1]}) : {result[0]}")
            return result[0]
        else:
            print(f"🤖 [Agent] Désolé, je n'ai aucun souvenir à propos de « {cle} ».")
            return None

    def tout_oublier(self):
        """Efface toute la mémoire de l'agent."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memoire")
        conn.commit()
        conn.close()
        print("🧹 [Agent] Ma mémoire a été entièrement effacée.")

    def lister_tout(self):
        """Affiche tout ce que l'agent a retenu."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT cle, valeur, date_ajout FROM memoire")
        results = cursor.fetchall()
        conn.close()

        if results:
            print("\n📚 --- Tout ce dont je me souviens ---")
            for cle, valeur, date in results:
                print(f"• [{date}] {cle.capitalize()} : {valeur}")
            print("--------------------------------------\n")
        else:
            print("📭 [Agent] Ma mémoire est actuellement vide.")


# --- Test interactif de l'Agent ---
if __name__ == "__main__":
    mon_agent = AgentMemoireTotale()

    print("--- 1. Enregistrement d'informations ---")
    mon_agent.retenir("anniversaire_maman", "14 mai")
    mon_agent.retenir("code_wifi", "Noel2026!")
    mon_agent.retenir("projet_secret", "Application Secret Santa avec 7 participants")

    print("\n--- 2. Consultation de la mémoire ---")
    mon_agent.se_souvenir("code_wifi")
    mon_agent.se_souvenir("anniversaire_maman")

    print("\n--- 3. Affichage global de la mémoire ---")
    mon_agent.lister_tout()