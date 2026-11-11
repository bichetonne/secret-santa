import sqlite3
import random

# Nom du fichier de la base de données SQLite
DB_NAME = "secret_santa.db"

def init_database():
    """Initialise la base de données et crée les tables nécessaires."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table des participants et de leurs conjoints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            partner TEXT,
            viewed INTEGER DEFAULT 0
        )
    """)

    # Table des attributions (le tirage au sort secret)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            giver TEXT PRIMARY KEY,
            receiver TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def seed_participants():
    """Insère la liste fixe des participants et leurs couples."""
    participants_data = [
        ("Stephane", "Sandra"),
        ("Sandra", "Stephane"),
        ("Corentin", "Eva"),
        ("Eva", "Corentin"),
        ("Baptiste", "Claire"),
        ("Claire", "Baptiste"),
        ("Téo", None)  # Téo n'a pas de partenaire
    ]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    for name, partner in participants_data:
        cursor.execute("""
            INSERT OR IGNORE INTO participants (name, partner) VALUES (?, ?)
        """, (name, partner))
        
    conn.commit()
    conn.close()

def effectuer_tirage_si_besoin():
    """Effectue le tirage au sort en respectant la règle anti-couples et anti-auto-attribution si ce n'est pas déjà fait."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Vérifie si un tirage existe déjà
    cursor.execute("SELECT COUNT(*) FROM assignments")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # Le tirage est déjà figé dans la base de données

    # Récupérer tous les participants
    cursor.execute("SELECT name, partner FROM participants")
    rows = cursor.fetchall()
    
    names = [row[0] for row in rows]
    couples = {row[0]: row[1] for row in rows}

    success = False
    attempts = 0
    targets = names[:]

    # Algorithme de tirage sécurisé
    while not success and attempts < 10000:
        attempts += 1
        random.shuffle(targets)
        
        is_valid = True
        for i in range(len(names)):
            giver = names[i]
            receiver = targets[i]
            # Règle : Interdit de se piocher soi-même ou son/sa partenaire
            if giver == receiver or couples.get(giver) == receiver:
                is_valid = False
                break
        if is_valid:
            success = True

    if success:
        for i in range(len(names)):
            cursor.execute("INSERT OR REPLACE INTO assignments (giver, receiver) VALUES (?, ?)", (names[i], targets[i]))
        conn.commit()
        print("✨ Tirage au sort généré et enregistré définitivement dans la base de données SQLite !")
    else:
        print("Erreur : Impossible de trouver une combinaison valide.")

    conn.close()

def voir_cible(nom):
    """Permet à un participant de découvrir sa cible et met à jour son statut 'viewed'."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT receiver FROM assignments WHERE giver = ?", (nom,))
    result = cursor.fetchone()

    if result:
        # Met à jour le statut de consultation dans la base de données
        cursor.execute("UPDATE participants SET viewed = 1 WHERE name = ?", (nom,))
        conn.commit()
        conn.close()
        return result[0]
    
    conn.close()
    return None

def afficher_statut_base():
    """Affiche l'état de la base de données (qui a consulté ou non)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, viewed FROM participants")
    print("\n--- État de la base de données ---")
    for name, viewed in cursor.fetchall():
        status = "✓ A consulté" if viewed == 1 else "En attente"
        print(f"👤 {name} : {status}")
    print("----------------------------------\n")
    conn.close()

# --- Exécution du script ---
if __name__ == "__main__":
    init_database()
    seed_participants()
    effectuer_tirage_si_besoin()
    
    afficher_statut_base()

    # Exemple de test : Claire consulte sa cible
    test_user = "Claire"
    cible = voir_cible(test_user)
    if cible:
        print(f"🎁 {test_user} découvre sa cible secrète : {cible}")

    afficher_statut_base()