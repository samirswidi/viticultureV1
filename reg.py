import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

# Se connecter à la base de données SQLite
sqlite_DB = 'agriculture_db.sqlite'
conn = sqlite3.connect(sqlite_DB)
c = conn.cursor()

def entrainer_model_regression():
   
    query = "SELECT maladie_visee, stade_maladie, methodes_traitement, observations, etat FROM operations_phytosanitaires"
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

    # Encoder la variable cible 'etat'
    df['etat'] = df['etat'].map({'Vivante': 1, 'Morte': 0})
    
    # Vérifier les NaN dans la colonne 'etat'
    print(df['etat'].isnull().sum())  # Vérifier si 'etat' contient des NaN
    df['etat'] = df['etat'].fillna(0)  # Remplir les NaN avec une valeur par défaut (0)

    # Sélectionner les variables explicatives et la cible
    X = df[['maladie_visee', 'stade_maladie', 'methodes_traitement', 'observations']]
    y = df['etat']

    # Séparer les données en ensemble d'entraînement et ensemble de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Créer le modèle de régression logistique
    model = LogisticRegression(max_iter=1000)

    # Former le modèle avec les données d'entraînement
    model.fit(X_train, y_train)

    # Prédire les résultats pour l'ensemble de test
    y_pred = model.predict(X_test)

    # Afficher la matrice de confusion
    print("Matrice de confusion :")
    print(confusion_matrix(y_test, y_pred))

    # Afficher un rapport détaillé sur les performances
    print("\nRapport de classification :")
    print(classification_report(y_test, y_pred))

    # Précision du modèle
    accuracy = model.score(X_test, y_test)
    print(f"\nPrécision du modèle : {accuracy * 100:.2f}%")

    return model, label_encoder_maladie, label_encoder_stade, label_encoder_methodes, label_encoder_observations

# Entrainer le modèle et récupérer les objets nécessaires
model, label_encoder_maladie, label_encoder_stade, label_encoder_methodes, label_encoder_observations = entrainer_model_regression()

# Fonction pour entrer de nouvelles données et prédire l'état
def tester_modele(model, label_encoder_maladie, label_encoder_stade,
                  label_encoder_methodes, label_encoder_observations,
                  maladie_visee, stade_maladie, methodes_traitement, observations):
    # Vérifier et encoder chaque entrée
    try:
        maladie_visee_encoded = label_encoder_maladie.transform([maladie_visee])[0]
    except KeyError:
        maladie_visee_encoded = -1  # Valeur par défaut

    try:
        stade_maladie_encoded = label_encoder_stade.transform([stade_maladie])[0]
    except KeyError:
        stade_maladie_encoded = -1
    
    try:
        methodes_traitement_encoded = label_encoder_methodes.transform([methodes_traitement])[0]
    except KeyError:
        methodes_traitement_encoded = -1

    try:
        observations_encoded = label_encoder_observations.transform([observations])[0]
    except KeyError:
        observations_encoded = -1

    # Créer un DataFrame avec ces données encodées
    new_data = pd.DataFrame({
        'maladie_visee': [maladie_visee_encoded],
        'stade_maladie': [stade_maladie_encoded],
        'methodes_traitement': [methodes_traitement_encoded],
        'observations': [observations_encoded]
    })

    # Prédire l'état (vivante ou morte) avec le modèle
    prediction = model.predict(new_data)

    # Retourner la prédiction
    return 'Vivante' if prediction == 1 else 'Morte'

# Tester le modèle avec des entrées utilisateur

# Tester le modèle avec des entrées utilisateur
etat=tester_modele(model, label_encoder_maladie, label_encoder_stade,
               label_encoder_methodes, label_encoder_observations,'Mildiou','Moyen','Insecticide','Besoin de suivi')
print(etat)