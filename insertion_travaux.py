import sqlite3
import random
from datetime import datetime, timedelta

# Fonction pour se connecter à la base de données
def get_db_connection():
    conn = sqlite3.connect('agriculture_db.sqlite')  # Remplacez par le nom de votre base de données
    conn.row_factory = sqlite3.Row
    return conn

# Insertion de 100 enregistrements
def insert_data():
    conn = get_db_connection()
    c = conn.cursor()

    # Vérifiez que les ID d'exploitation et d'opération sanitaire existent
    exploitation_ids = [row['id_exploitation'] for row in c.execute('SELECT id_exploitation FROM exploitations').fetchall()]
    operation_sanitaire_ids = 0
    for i in range(100):
        type_travail = random.choice(['Plantation', 'Entretien', 'Récolte', 'Irrigation'])
        date_travail = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
        
        # Obtenez un ID d'exploitation valide
        id_exploitation = random.choice(exploitation_ids) if exploitation_ids else 1  # Choisissez un ID ou utilisez 1 par défaut

        # Obtenez un ID de salarié valide
        salarie_id = 1  # Remplacez par la logique pour obtenir un ID valide

        operation_culturale = random.choice(['Fertilisation', 'Pulvérisation', 'Labour'])
        duree = random.uniform(1.0, 8.0)  # Durée en heures
        
        # Obtenez un ID d'opération sanitaire valide
        id_operation_sanitaire = random.choice(operation_sanitaire_ids) if operation_sanitaire_ids else 1  # Choisissez un ID ou utilisez 1 par défaut

        # Insertion dans la base de données
        c.execute(f'''
            INSERT INTO travaux_agricoles (type_travail, date_travail, id_exploitation, salarie_id, operation_culturale, Duree, id_operation_sanitaire)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (type_travail, date_travail, id_exploitation, salarie_id, operation_culturale, duree, id_operation_sanitaire))

    conn.commit()
    conn.close()

# Exécution de l'insertion
insert_data()
