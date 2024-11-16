import sqlite3
import pandas as pd
from kmodes.kmodes import KModes
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import silhouette_score
from sklearn.metrics import pairwise_distances

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

# Créer une copie des données pour le clustering
X = df[['type_travail']]

# Appliquer K-modes avec un nombre de clusters (par exemple, 4 clusters)
kmodes = KModes(n_clusters=4, init='Cao', n_init=5, verbose=1, random_state=42)
df['cluster'] = kmodes.fit_predict(X)

# Encoder la colonne 'type_travail' pour calculer la matrice de dissimilarité
label_encoder = LabelEncoder()
X_encoded = label_encoder.fit_transform(df['type_travail']).reshape(-1, 1)

# Calculer la matrice de dissimilarité et le score de silhouette
dissimilarity_matrix = pairwise_distances(X_encoded, metric='hamming')
silhouette_avg = silhouette_score(dissimilarity_matrix, df['cluster'], metric='precomputed')
print(f"Score de silhouette : {silhouette_avg:.2f}")

# Afficher les résultats avec les clusters
print("Données avec clusters attribués :")
print(df.head())

# Regrouper les salariés par cluster
clusters_salaries = df.groupby('cluster')['salarie_id'].apply(list)
print("\nSalariés dans chaque cluster :")
print(clusters_salaries)
