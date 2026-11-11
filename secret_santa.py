import sqlite3
import random

# 1. Connexion à la base de données (crée le fichier 'secret_santa.db' automatiquement)
conn = sqlite3.connect("secret_santa.db")
cursor = conn.cursor()

# 2. Création des tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        partner TEXT,
        viewed INTEGER DEFAULT 0
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        giver TEXT PRIMARY KEY,
        receiver TEXT NOT NULL
    )
""")
conn.commit()

# 3. Données initiales (participants et leurs conjoints respectifs)
participants_data = [
    ("Claire", "Baptiste"),
    ("Stephane", "Sandra"),
    ("Sandra", "Stephane"),
    ("Corentin", "Eva"),
    ("Eva", "Corentin"),
    ("Baptiste", "Claire"),
    ("Téo", None)
]

# Insertion des participants s'ils n'existent pas encore
cursor.executemany("""
    INSERT OR IGNORE INTO participants (name, partner) VALUES (?, ?)
""", participants_data)
conn.commit()

# 4. Fonction pour effectuer le tirage au sort (si non fait) en respectant les règles
def effectuer_tirage():
    cursor.execute("SELECT COUNT(*) FROM assignments")
    if cursor.fetchone()[0] > 0:
        print("Le tirage a déjà été effectué dans la base de données.")
        return

    names = [p[0] for p in participants_data]
    couples = {p[0]: p[1] for p in participants_data}
    
    success = False
    attempts = 0
    targets = names[:]

    while not success and attempts < 5000:
        attempts += 1
        random.shuffle(targets)
        
        is_valid = True
        for i in range(len(names)):
            giver = names[i]
            receiver = targets[i]
            # Règle : Pas d'auto-attribution et pas son/sa partenaire
            if giver == receiver or couples.get(giver) == receiver:
                is_valid = False
                break
        if is_valid:
            success = True

    if success:
        for i in range(len(names)):
            cursor.execute("INSERT INTO assignments (giver, receiver) VALUES (?, ?)", (names[i], targets[i]))
        conn.commit()
        print("Tirage au sort effectué et enregistré avec succès !")
    else:
        print("Erreur lors du tirage.")

# 5. Fonction pour qu'un participant découvre sa cible et mette à jour son statut
def decouvrir_cible(nom):
    cursor.execute("SELECT receiver FROM assignments WHERE giver = ?", (nom,))
    result = cursor.fetchone()
    if result:
        # Met à jour le statut de consultation dans la base de données
        cursor.execute("UPDATE participants SET viewed = 1 WHERE name = ?", (nom,))
        conn.commit()
        return result[0]
    return None

# --- Exécution d'exemple ---
if __name__ == "__main__":
    effectuer_tirage()
    
    # Exemple : Claire consulte sa cible
    nom_test = "Claire"
    cible = decouvrir_cible(nom_test)
    if cible:
        print(f"{nom_test} doit offrir un cadeau à : {cible}")

conn.close()