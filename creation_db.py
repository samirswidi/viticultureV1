import sqlite3
import pandas as pd

# Nom de la base de données
sqlite_DB = 'agriculture_db.sqlite'

# Connexion à la base de données
conn = sqlite3.connect(sqlite_DB)
c = conn.cursor()

# Définition des noms de tables
table1 = 'exploitations'
table2 = 'chefs_exploitation'
table3 = 'salaries'
table4 = 'travaux_agricoles'
table5 = 'operations_phytosanitaires'
table6 = 'synthese_annuelle'

# Création des tables
def create_tables():
    c.execute(f'''CREATE TABLE IF NOT EXISTS {table1} (
                    id_exploitation INTEGER PRIMARY KEY,
                    nom_exploitation TEXT,
                    superficie REAL
                )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS {table2} (
                    id_chef INTEGER PRIMARY KEY,
                    username_chef TEXT ,
                    nom_chef TEXT,
                    prenom_chef TEXT,
                    password_chef TEXT,
                    id_exploitation INTEGER,
                    FOREIGN KEY(id_exploitation) REFERENCES {table1}(id_exploitation)
                )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS {table3} (
                    id_salarie INTEGER PRIMARY KEY,
                    identifiant_sal TEXT,
                    nom_salarie TEXT,
                    prenom_salarie TEXT,
                    date_embauche TEXT,
                    id_exploitation INTEGER,
                    FOREIGN KEY(id_exploitation) REFERENCES {table1}(id_exploitation)
                )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS {table4} (
                    id_travail INTEGER PRIMARY KEY,
                    type_travail TEXT,
                    date_travail TEXT,
                    id_exploitation INTEGER,
                    salarie_id INTEGER,
                    operation_culturale TEXT,
                    Duree FLOAT,
                    id_operation_sanitaire INTEGER,
                    FOREIGN KEY(id_operation_sanitaire) REFERENCES {table5}(id_operation_sanitaire),
                    FOREIGN KEY(id_exploitation) REFERENCES {table1}(id_exploitation)
                )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS {table5} (
                    id_operation_sanitaire INTEGER PRIMARY KEY,
                    maladie_visee TEXT,
                    stade_maladie TEXT,
                    methodes_traitement TEXT,
                    observations TEXT,
                    date_traitement,
                    id_exploitation INTEGER,
                    FOREIGN KEY(id_exploitation) REFERENCES {table1}(id_exploitation)
                )''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS {table6} (
                    id_synthese INTEGER PRIMARY KEY,
                    annee INTEGER,
                    production_totale REAL,
                    id_exploitation INTEGER,
                    FOREIGN KEY(id_exploitation) REFERENCES {table1}(id_exploitation)
                )''')
    c.execute(f'''CREATE TABLE IF NOT EXISTS authentification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL,
    password TEXT NOT NULL
                ) ''')
    c.execute(f''' INSERT INTO authentification (login, password) VALUES ('admin', '21232f297a57a5a743894a0e4a801fc3')''')



  

# Appel de la fonction pour créer les tables
create_tables()

def to_csv():
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    for table_name in tables:
        table_name = table_name[0]
        table = pd.read_sql_query(f"SELECT * from {table_name}", conn)
        table.to_csv(f"{table_name}.csv", index_label='index')

#to_csv()

# Validation et fermeture de la connexion
conn.commit()
c.close()
conn.close()
