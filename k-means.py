import sqlite3
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Se connecter à la base de données SQLite
sqlite_DB = 'agriculture_db.sqlite'
conn = sqlite3.connect(sqlite_DB)
c = conn.cursor()

def appliquer_clustering_kmeans():
    # Charger les données depuis la base de données
    query = "SELECT maladie_visee, stade_maladie, methodes_traitement, observations FROM operations_phytosanitaires"
    df = pd.read_sql(query, conn)
    conn.close()

    # Vérifier les NaN dans les données
    print(df.isnull().sum())  # Vérifier toutes les colonnes

    # Supprimer les lignes contenant des NaN
    df = df.dropna()

    # Encoder les variables catégorielles
    label_encoder_maladie = LabelEncoder()
    label_encoder_stade = LabelEncoder()
    label_encoder_methodes = LabelEncoder()
    label_encoder_observations = LabelEncoder()

    df['maladie_visee'] = label_encoder_maladie.fit_transform(df['maladie_visee'])
    df['stade_maladie'] = label_encoder_stade.fit_transform(df['stade_maladie'])
    df['methodes_traitement'] = label_encoder_methodes.fit_transform(df['methodes_traitement'])
    df['observations'] = label_encoder_observations.fit_transform(df['observations'])

    # Normalisation des données
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df)

    # Appliquer K-means avec un nombre de clusters, par exemple 3
    kmeans = KMeans(n_clusters=10, random_state=42)
    kmeans.fit(df_scaled)
    df['cluster'] = kmeans.labels_

    # Calculer le score de silhouette pour évaluer la qualité du clustering
    silhouette_avg = silhouette_score(df_scaled, kmeans.labels_)
    print(f"Score de silhouette : {silhouette_avg:.2f}")

    # Afficher les données avec les clusters attribués
    print("Données avec clusters attribués :")
    print(df)

    return kmeans, label_encoder_maladie, label_encoder_stade, label_encoder_methodes, label_encoder_observations

# Appliquer k-means et obtenir les objets nécessaires
kmeans, label_encoder_maladie, label_encoder_stade, label_encoder_methodes, label_encoder_observations = appliquer_clustering_kmeans()

# Fonction pour entrer de nouvelles données et prédire le cluster avec K-means
def predire_cluster(kmeans, label_encoder_maladie, label_encoder_stade,
                    label_encoder_methodes, label_encoder_observations,
                    maladie_visee, stade_maladie, methodes_traitement, observations):
    
    # Encoder chaque entrée
    try:
        maladie_visee_encoded = label_encoder_maladie.transform([maladie_visee])[0]
    except ValueError:
        maladie_visee_encoded = -1  # Valeur par défaut si inconnue

    try:
        stade_maladie_encoded = label_encoder_stade.transform([stade_maladie])[0]
    except ValueError:
        stade_maladie_encoded = -1
    
    try:
        methodes_traitement_encoded = label_encoder_methodes.transform([methodes_traitement])[0]
    except ValueError:
        methodes_traitement_encoded = -1

    try:
        observations_encoded = label_encoder_observations.transform([observations])[0]
    except ValueError:
        observations_encoded = -1

    # Créer un DataFrame avec ces données encodées
    new_data = pd.DataFrame({
        'maladie_visee': [maladie_visee_encoded],
        'stade_maladie': [stade_maladie_encoded],
        'methodes_traitement': [methodes_traitement_encoded],
        'observations': [observations_encoded]
    })

    # Normaliser les nouvelles données
    new_data_scaled = StandardScaler().fit_transform(new_data)

    # Prédire le cluster avec le modèle K-means
    cluster_predicted = kmeans.predict(new_data_scaled)

    # Retourner le numéro du cluster prédit
    return f"Cluster assigné : {cluster_predicted[0]}"

# Tester le clustering avec des entrées utilisateur
cluster_result = predire_cluster(kmeans, label_encoder_maladie, label_encoder_stade,
                                 label_encoder_methodes, label_encoder_observations,
                                 'Mildiou', 'Moyen', 'Insecticide', 'Besoin de suivi')
print(cluster_result)
