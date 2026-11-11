from flask import Flask, render_template_string, request, jsonify
import sqlite3
import random
import os

app = Flask(__name__)
DB_NAME = "secret_santa.db"

# Participants et couples (règles strictes anti-couples et anti-auto-attribution)
PARTICIPANTS = ["Claire", "Stephane", "Sandra", "Corentin", "Eva", "Baptiste", "Téo"]
COUPLES = {
    "Stephane": "Sandra",
    "Sandra": "Stephane",
    "Corentin": "Eva",
    "Eva": "Corentin",
    "Baptiste": "Claire",
    "Claire": "Baptiste"
}

def init_db():
    """Initialise la base de données SQLite et génère le tirage unique si besoin."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            name TEXT PRIMARY KEY,
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
    
    # Enregistre les participants s'ils n'existent pas
    for p in PARTICIPANTS:
        cursor.execute("INSERT OR IGNORE INTO participants (name, viewed) VALUES (?, 0)", (p,))
    
    # Génère le tirage au sort figé et définitif s'il n'existe pas encore
    cursor.execute("SELECT COUNT(*) FROM assignments")
    if cursor.fetchone()[0] == 0:
        targets = PARTICIPANTS[:]
        success = False
        attempts = 0
        while not success and attempts < 10000:
            attempts += 1
            random.shuffle(targets)
            valid = True
            for i in range(len(PARTICIPANTS)):
                giver = PARTICIPANTS[i]
                receiver = targets[i]
                if giver == receiver or COUPLES.get(giver) == receiver:
                    valid = False
                    break
            if valid:
                success = True
        
        if success:
            for i in range(len(PARTICIPANTS)):
                cursor.execute("INSERT INTO assignments (giver, receiver) VALUES (?, ?)", (PARTICIPANTS[i], targets[i]))
            conn.commit()
            
    conn.close()

init_db()

# Page HTML de l'interface utilisateur intégrée
HTML_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Père Noël Secret - Secret Santa 🎄</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Mountains+of+Christmas:wght@700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
            color: #f3f4f6;
            min-height: 100vh;
        }
        .christmas-title { font-family: 'Mountains of Christmas', cursive; }
    </style>
</head>
<body class="flex flex-col items-center justify-center p-4">

    <div class="w-full max-w-xl bg-emerald-900/85 backdrop-blur-md border border-emerald-700/50 rounded-3xl shadow-2xl p-6 sm:p-8 my-8">
        
        <div class="text-center mb-8">
            <span class="text-5xl">🎁</span>
            <h1 class="christmas-title text-4xl sm:text-5xl font-bold text-amber-300 mt-2 tracking-wide">Secret Santa</h1>
            <p class="text-emerald-200 text-sm sm:text-base mt-1">Serveur Backend Python & Base SQLite</p>
        </div>

        <!-- STATUT DES PARTICIPANTS -->
        <div class="bg-emerald-950/60 p-4 rounded-2xl border border-emerald-800 mb-6">
            <h2 class="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <span>👥</span> Statut des consultations
            </h2>
            <div id="status-list" class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <!-- Chargé dynamiquement -->
            </div>
        </div>

        <!-- ZONE DE CONSULTATION -->
        <div class="bg-emerald-950/60 p-6 rounded-2xl border border-emerald-800 text-center space-y-4">
            <h2 class="text-xl font-bold text-amber-300">Découvre ta cible secrète 🎅</h2>
            <p class="text-sm text-emerald-200">Sélectionne ton prénom pour découvrir ton destinataire.</p>
            
            <div class="max-w-xs mx-auto">
                <select id="user-select" class="w-full px-4 py-3 bg-emerald-900 border border-emerald-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-amber-400">
                    <option value="">-- Qui es-tu ? --</option>
                </select>
            </div>

            <button onclick="decouvrirCible()" class="w-full max-w-xs mx-auto block py-3 bg-amber-500 hover:bg-amber-400 text-emerald-950 font-bold rounded-xl transition shadow-lg cursor-pointer">
                🎁 Découvrir ma cible
            </button>
        </div>

    </div>

    <!-- MODALE DE REVELATION -->
    <div id="reveal-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
        <div class="bg-emerald-900 border-2 border-amber-400 max-w-md w-full rounded-3xl p-6 sm:p-8 text-center shadow-2xl space-y-6">
            <div class="text-5xl">🎄</div>
            <h3 class="text-2xl font-bold text-amber-300">Chut ! C'est un secret...</h3>
            
            <div class="bg-emerald-950 p-6 rounded-2xl border border-emerald-700">
                <p class="text-base text-emerald-200">Tu dois offrir un cadeau à :</p>
                <p id="target-name" class="text-3xl font-extrabold text-amber-400 mt-3 tracking-wide"></p>
            </div>

            <button onclick="fermerModale()" class="w-full py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl transition shadow-lg cursor-pointer">
                🔒 J'ai compris, masquer
            </button>
        </div>
    </div>

    <script>
        async function chargerStatut() {
            let response = await fetch('/api/status');
            let data = await response.json();
            let listEl = document.getElementById('status-list');
            let selectEl = document.getElementById('user-select');
            
            listEl.innerHTML = '';
            selectEl.innerHTML = '<option value="">-- Qui es-tu ? --</option>';

            data.forEach(p => {
                listEl.innerHTML += `
                    <div class="p-2.5 rounded-xl text-sm font-medium flex items-center justify-between border ${p.viewed ? 'bg-emerald-900/60 border-emerald-600 text-emerald-300' : 'bg-emerald-950/80 border-emerald-800 text-white'}">
                        <span>👤 ${p.name}</span>
                        <span class="text-xs px-2 py-0.5 rounded-full ${p.viewed ? 'bg-emerald-800 text-emerald-200' : 'bg-amber-500/20 text-amber-300'}">${p.viewed ? '✓ A consulté' : 'En attente'}</span>
                    </div>
                `;
                selectEl.innerHTML += `<option value="${p.name}">${p.name}</option>`;
            });
        }

        async function decouvrirCible() {
            let user = document.getElementById('user-select').value;
            if(!user) {
                alert("Veuillez sélectionner votre prénom !");
                return;
            }

            let response = await fetch('/api/reveal', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: user})
            });
            let data = await response.json();

            document.getElementById('target-name').textContent = data.target;
            document.getElementById('reveal-modal').classList.remove('hidden');
            chargerStatut();
        }

        function fermerModale() {
            document.getElementById('reveal-modal').classList.add('hidden');
            document.getElementById('user-select').value = '';
        }

        chargerStatut();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/status")
def api_status():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, viewed FROM participants")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"name": r[0], "viewed": r[1]} for r in rows])

@app.route("/api/reveal", methods=["POST"])
def api_reveal():
    data = request.json
    name = data.get("name")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT receiver FROM assignments WHERE giver = ?", (name,))
    res = cursor.fetchone()
    
    cursor.execute("UPDATE participants SET viewed = 1 WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    
    return jsonify({"target": res[0] if res else "Inconnu"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)