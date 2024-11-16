import sqlite3
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import silhouette_score

# Connexion à la base de données SQLite
sqlite_DB = 'agriculture_db.sqlite'
conn = sqlite3.connect(sqlite_DB)
c = conn.cursor()

# Charger les données avec uniquement les colonnes nécessaires
query = "SELECT type_travail, salarie_id FROM travaux_agricoles"
df = pd.read_sql(query, conn)
conn.close()

# Vérifier les valeurs manquantes
print(df.isnull().sum())

# Encoder la colonne 'type_travail' (par exemple : Irrigation, Entretien, etc.)
label_encoder = LabelEncoder()
df['type_travail_encoded'] = label_encoder.fit_transform(df['type_travail'])

# Sélectionner uniquement les colonnes nécessaires pour le clustering
X = df[['type_travail_encoded']]

# Appliquer K-means avec un nombre de clusters optimal (par exemple, 3 clusters)
kmeans = KMeans(n_clusters=4, random_state=42)
df['cluster'] = kmeans.fit_predict(X)

# Calculer le score de silhouette pour évaluer la qualité du clustering
silhouette_avg = silhouette_score(X, df['cluster'])
print(f"Score de silhouette : {silhouette_avg:.2f}")

# Afficher les résultats avec les clusters
print("Données avec clusters attribués :")
print(df.head())

# Regrouper les salariés par cluster
clusters_salaries = df.groupby('cluster')['salarie_id'].apply(list)
print("\nSalariés dans chaque cluster :")
print(clusters_salaries)
