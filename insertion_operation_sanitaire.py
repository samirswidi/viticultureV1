import sqlite3
from random import choice, randint, random
from datetime import datetime, timedelta

# Connexion à la base de données
sqlite_DB = 'agriculture_db.sqlite'
conn = sqlite3.connect(sqlite_DB)
c = conn.cursor()

table5 = 'operations_phytosanitaires'
table1 = 'exploitations'
table3 = 'salaries'
c.execute(f'''DROP TABLE IF EXISTS {table5} ''')
c.execute(f'''CREATE TABLE IF NOT EXISTS {table5} (
                    id_operation_sanitaire INTEGER PRIMARY KEY,
                    maladie_visee TEXT,
                    stade_maladie TEXT,
                    methodes_traitement TEXT,
                    observations TEXT,
                    etat TEXT,
                    date_traitement,
                    id_exploitation INTEGER,
                    id_salarie INTEGER,
                    FOREIGN KEY(id_exploitation) REFERENCES {table1}(id_exploitation),
                    FOREIGN KEY(id_salarie) REFERENCES {table3}(id_salarie)
                )''')

# Définir les valeurs possibles pour les champs
maladies = ['Mildiou', 'Oïdium', 'Botrytis', 'Anthracnose']
stades = ['Début', 'Moyen', 'Avancé']
etat = ['Vivante', 'Morte']
methodes = ['Pulvérisation', 'Traitement biologique', 'Fongicide', 'Insecticide', 'Herbicide', 'Décoller', 'Traitement thermique']
observations = ['Traitement effectué avec succès', 'Besoin de suivi', 'Réinfection possible']
id_exploitation = 1
id_salarie = 1

# Insérer 100 enregistrements
for _ in range(100):
    maladie_visee = choice(maladies)
    stade_maladie = choice(stades)
    methodes_traitement = choice(methodes)
    observations_text = choice(observations)
    
    # Logique pour déterminer l'état
    if stade_maladie in ['Moyen', 'Avancé'] or observations_text in ['Traitement effectué avec succès', 'Besoin de suivi'] or methodes_traitement in ['Fongicide', 'Insecticide', 'Herbicide', 'Décoller', 'Traitement thermique']:
        # 80% de chances que l'état soit 'Morte'
        etat_text = 'Morte' if random() < 0.80 else 'Vivante'
    else:
        # Si les conditions ne sont pas remplies, l'état est aléatoire
        etat_text = choice(etat)
    
    # Générer une date aléatoire dans l'année passée
    date_traitement = datetime.now() - timedelta(days=randint(0, 365))
    date_traitement = date_traitement.strftime('%Y-%m-%d')  # Format de date SQLite

    # Insertion dans la table
    c.execute(f'''
        INSERT INTO {table5} (maladie_visee, stade_maladie, methodes_traitement, observations, etat, date_traitement, id_exploitation, id_salarie)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (maladie_visee, stade_maladie, methodes_traitement, observations_text, etat_text, date_traitement, id_exploitation, id_salarie))

# Valider les modifications et fermer la connexion
conn.commit()
conn.close()

print("18 enregistrements ont été insérés dans la table operations_phytosanitaires.")
