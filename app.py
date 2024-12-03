import locale  

from flask import Flask, render_template, request, redirect, url_for, session, flash  
import sqlite3  
import hashlib  
import smtplib  
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText  
from email.mime.base import MIMEBase  
from email import encoders  
import pandas as pd  
from sklearn.model_selection import train_test_split  
from sklearn.preprocessing import LabelEncoder  
from sklearn.linear_model import LogisticRegression  
from sklearn.metrics import classification_report, confusion_matrix, silhouette_score, pairwise_distances  
from kmodes.kmodes import KModes  

import matplotlib.pyplot as plt  
import io  
import base64  
import csv  


app = Flask(__name__)
app.secret_key = 'samirswidisecretkey'
# Nom de la base de données
DB_NAME = 'agriculture_db.sqlite'

# Fonction pour se connecter à la base de données
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Retourne les résultats sous forme de dictionnaire
    return conn
# Page d'accueil (redirection vers login si non connecté)
def generer_fichier_csv(travaux):
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Ajouter les en-têtes
    writer.writerow(["nom salrie","prenom salrie","operation sanitaire","duree","Type Travail", "Date Travail"])
    
    # Ajouter les données
    for travail in travaux:
        writer.writerow([
            

            travail['nom_salarie'],
            travail['prenom_salarie'],
            travail['operation_culturale'],
            travail['Duree'],
            travail['type_travail'],
            travail['date_travail'],
           
        ])
    
    output.seek(0)
    return output.getvalue()
def send_email(chef_nom, travaux):
    # Générer le fichier CSV
    csv_data = generer_fichier_csv(travaux)
    
    # Créer le message
    msg = MIMEMultipart()
    msg['Subject'] = 'Saisie Mensuelle Effectuée'
    msg['From'] = 'no-reply@exploitation.com'
    msg['To'] = "samirswidi@gmail.com"
    
    # Ajouter le corps de l'email
    body = f"La saisie mensuelle des travaux a été effectuée par {chef_nom}."
    msg.attach(MIMEText(body, 'plain'))
    
    # Ajouter le fichier CSV en pièce jointe
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(csv_data.encode('utf-8'))
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename='travaux_mensuels.csv')
    msg.attach(part)
    
    # Envoyer l'email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('samirswidi@gmail.com', 'dmxm dxoo evut fptv')  # Remplacez par votre mot de passe d'application
            server.send_message(msg)
    except Exception as e:
        raise Exception(f"Erreur lors de l'envoi de l'email : {e}")
@app.route('/envoiemail/<string:nom>', methods=['POST'])
def envoimail(nom):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Récupérer les travaux depuis la base de données
    conn = get_db_connection()
    travaux = conn.execute(f'''
        SELECT id_travail, type_travail, date_travail, salarie_id,salaries.nom_salarie ,salaries.prenom_salarie ,
                           operation_culturale, Duree FROM travaux_agricoles 
        JOIN exploitations ON exploitations.id_exploitation = travaux_agricoles.id_exploitation 
        JOIN salaries ON salaries.id_salarie = travaux_agricoles.salarie_id
    ''').fetchall()
    conn.close()
    
    # Envoyer l'email avec la pièce jointe
    try:
        send_email(nom, travaux)
        flash("Email envoyé avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de l'envoi de l'email : {e}", "error")
    
    return redirect(url_for('travaux'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')
def get_user_by_id(user_id):
    # Connexion à la base de données (ajustez les paramètres selon votre configuration)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chefs_exploitation WHERE id_chef = ?", (user_id,))
    user = cursor.fetchone()  # Récupérer l'utilisateur
    conn.close()
    return user
# Route pour afficher toutes les exploitations
@app.route('/login', methods=('GET', 'POST'))
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        login = request.form['login']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        conn = get_db_connection()
        
        if login == "admin":
            admin_login = conn.execute(
                'SELECT * FROM authentification WHERE login = ? AND password = ?', 
                (login, password)
            ).fetchone()
            
            if admin_login:
                session['admin'] = admin_login['login']
                session['user_id']=admin_login['id']
                return redirect(url_for('index'))
            else:
                flash('Nom d\'utilisateur ou mot de passe incorrect.')
        
        else:
            user = conn.execute(
                'SELECT * FROM chefs_exploitation WHERE username_chef = ? AND password_chef = ?', 
                (login, password)
            ).fetchone()
            conn.close()
            
            if user:
                session['user_id'] = user['id_chef']
                user_data = get_user_by_id(session['user_id'])
                session['admin'] = user_data['nom_chef'] + ' ' + user_data['prenom_chef']
                return redirect(url_for('index'))
            else:
                flash('Nom d\'utilisateur ou mot de passe incorrect.')

    return render_template('login.html')

# Déconnexion
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/exploitations')
def exploitations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()
    conn.close()
    return render_template('exploitations.html', exploitations=exploitations)

# Route pour ajouter une exploitation
@app.route('/exploitations/add', methods=('GET', 'POST'))
def add_exploitation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nom = request.form['nom']
        superficie = request.form['superficie']

        conn = get_db_connection()
        conn.execute('INSERT INTO exploitations (nom_exploitation, superficie) VALUES (?, ?)', (nom, superficie))
        conn.commit()
        conn.close()
        return redirect(url_for('exploitations'))
    
    return render_template('add_exploitation.html')

# Route pour modifier une exploitation
@app.route('/exploitations/edit/<int:id>', methods=('GET', 'POST'))
def edit_exploitation(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    exploitation = conn.execute('SELECT * FROM exploitations WHERE id_exploitation = ?', (id,)).fetchone()

    if request.method == 'POST':
        nom = request.form['nom']
        superficie = request.form['superficie']
        
        conn.execute('UPDATE exploitations SET nom_exploitation = ?, superficie = ? WHERE id_exploitation = ?', (nom, superficie, id))
        conn.commit()
        conn.close()
        return redirect(url_for('exploitations'))

    return render_template('edit_exploitation.html', exploitation=exploitation)

# Route pour supprimer une exploitation
@app.route('/exploitations/delete/<int:id>', methods=('GET', 'POST'))
def delete_exploitation(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM exploitations WHERE id_exploitation = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('exploitations'))

# Routes pour les autres tables (chefs_exploitation, salariés, etc.) fonctionnent de la même manière.
# Vous pouvez dupliquer le modèle utilisé pour 'exploitations' pour chaque table.



# Lister les chefs d'exploitation
@app.route('/chefs_exploitation')
def chefs_exploitation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    chefs = conn.execute('SELECT * FROM chefs_exploitation').fetchall()
    conn.close()
    return render_template('chefs_exploitation.html', chefs=chefs)

# Route pour ajouter un chef d'exploitation
@app.route('/chefs_exploitation/add', methods=('GET', 'POST'))
def add_chef_exploitation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()  # Récupérer toutes les exploitations
    conn.close()

    if request.method == 'POST':
        username_chef=request.form['username_chef']
        nom = request.form['nom']
        prenom = request.form['prenom']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        id_exploitation = request.form['id_exploitation']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO chefs_exploitation (username_chef,nom_chef, prenom_chef,password_chef, id_exploitation) VALUES (?,?, ?,?, ?)',
                     (username_chef,nom, prenom,password, id_exploitation))
        conn.commit()
        conn.close()
        return redirect(url_for('chefs_exploitation'))

    return render_template('add_chef_exploitation.html', exploitations=exploitations)

# Modifier un chef d'exploitation
@app.route('/chefs_exploitation/edit/<int:id>', methods=('GET', 'POST'))
def edit_chef_exploitation(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    chef = conn.execute('SELECT * FROM chefs_exploitation WHERE id_chef = ?', (id,)).fetchone()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()  # Récupérer toutes les exploitations
    conn.close()

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        id_exploitation = request.form['id_exploitation']
        
        conn = get_db_connection()
        conn.execute('UPDATE chefs_exploitation SET nom_chef = ?, prenom_chef = ?, id_exploitation = ? WHERE id_chef = ?',
                     (nom, prenom, id_exploitation, id))
        conn.commit()
        conn.close()
        return redirect(url_for('chefs_exploitation'))

    return render_template('edit_chef_exploitation.html', chef=chef, exploitations=exploitations)

# Supprimer un chef d'exploitation
@app.route('/chefs_exploitation/delete/<int:id>', methods=('POST',))
def delete_chef_exploitation(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM chefs_exploitation WHERE id_chef = ?', (id,))
    conn.commit()
    conn.close()
    #flash('Chef d\'exploitation supprimé avec succès.')
    return redirect(url_for('chefs_exploitation'))


# salarié
@app.route('/salaries')
def salaries():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    salaries = conn.execute('SELECT * FROM salaries inner join exploitations on exploitations.id_exploitation=salaries.id_exploitation').fetchall()
    conn.close()
    
    return render_template('salaries.html', salaries=salaries)
# Route pour ajouter un salarié
@app.route('/salaries/add_salarie', methods=('GET', 'POST'))
def add_salarie():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()  # Récupérer toutes les exploitations
    conn.close()    
    if request.method == 'POST':
        identifiant = request.form['identifiant']
        nom = request.form['nom']
        prenom = request.form['prenom']
        date_embauche = request.form['date_embauche']
        id_exploitation=request.form['id_exploitation']
        # Ouverture de la connexion
        conn = get_db_connection()
        
        # Vérification si le salarié existe déjà
        verif = conn.execute('SELECT * FROM salaries WHERE identifiant_sal = ?', (identifiant, )).fetchone()
        
        if verif:
            flash('Salarié déjà existe.', 'error')
            conn.close()  # Fermer la connexion après la vérification
            return render_template('add_salarie.html', exploitations=exploitations)
        else:
            # Insertion du salarié dans la base de données
            conn.execute(
                'INSERT INTO salaries (identifiant_sal, nom_salarie, prenom_salarie, date_embauche,id_exploitation) VALUES (?, ?, ?, ?,?)',
                (identifiant, nom, prenom, date_embauche,id_exploitation)
            )
            conn.commit()  # Enregistrer les modifications dans la base de données
            flash('Salarié ajouté avec succès.', 'success')
            conn.close()  # Fermer la connexion après l'insertion
            
            return redirect(url_for('add_salarie'))  # Redirection vers la même page après l'insertion
    
    return render_template('add_salarie.html', exploitations=exploitations)

    

@app.route('/salaries/edit/<int:id>', methods=('GET', 'POST'))
def edit_salarie(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Récupérer le salarié et les exploitations en utilisant une seule connexion
    salarie = conn.execute('SELECT * FROM salaries WHERE id_salarie = ?', (id,)).fetchone()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()  # Récupérer toutes les exploitations
    
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        date_embauche = request.form['date_embauche']
        id_exploitation = request.form['id_exploitation']
        
        # Mettre à jour les informations du salarié
        conn.execute(
            'UPDATE salaries SET nom_salarie = ?, prenom_salarie = ?, date_embauche = ?, id_exploitation = ? WHERE id_salarie = ?',
            (nom, prenom, date_embauche, id_exploitation, id)
        )
        conn.commit()  # Confirmer les changements
        
        # Fermer la connexion après toutes les opérations
        conn.close()
        
        return redirect(url_for('salaries'))

    # Fermer la connexion après toutes les opérations de récupération si pas de mise à jour
    conn.close()
    flash('Salarié modifié avec succès.')
    return render_template('edit_salarie.html', salarie=salarie, exploitations=exploitations)

# Route pour supprimer une salarie

@app.route('/salaries/delete/<int:id>', methods=('POST',) )
def delete_salarie(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM salaries WHERE id_salarie = ?', (id,))
    conn.commit()
    conn.close()
    flash('Salarié supprimé avec succès.')
    return redirect(url_for('salaries'))

# travaux agricole
@app.route('/travaux')
def travaux():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    travaux = conn.execute('SELECT * FROM travaux_agricoles  join exploitations on exploitations.id_exploitation=travaux_agricoles.id_exploitation join salaries on salaries.id_salarie=travaux_agricoles.salarie_id ').fetchall()
    conn.close()
    
    return render_template('travaux_agricoles.html', travaux=travaux)
# Route pour ajouter un travail
@app.route('/travaux/add_travail', methods=('GET', 'POST'))
def add_travail():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()  # Récupérer toutes les exploitations
    salaries=conn.execute('SELECT * FROM salaries').fetchall()  # Récupérer toutes les salaries
    conn.close()    
    if request.method == 'POST':
        type_travail=request.form['type_travail']
        date_travail=request.form['date_travail']
        id_exploitation=request.form['id_exploitation']
        salarie_id=request.form['salarie_id']
        operation_culturale=request.form['operation_culturale']
        duree=request.form['duree']
        id_operation_sanitaire=request.form['id_operation_sanitaire']
        # Ouverture de la connexion
        conn = get_db_connection()
        
        # Vérification si le salarié existe déjà
        verif = conn.execute(f'''SELECT * FROM travaux_agricoles
                              WHERE type_travail = ? and date_travail=? and id_exploitation=?
                                and salarie_id=? and operation_culturale=? and duree=? and id_operation_sanitaire=?
                             ''', (type_travail,date_travail,id_exploitation,salarie_id,operation_culturale,duree,id_operation_sanitaire, )).fetchone()
        print('ok')
        if verif:
            flash('Travail déjà existe.', 'error')
            conn.close()  # Fermer la connexion après la vérification
            return render_template('add_travail.html', exploitations=exploitations)
        else:
            # Insertion du salarié dans la base de données
            conn.execute(
                'INSERT INTO travaux_agricoles (type_travail, date_travail, id_exploitation, salarie_id,operation_culturale,duree,id_operation_sanitaire) VALUES (?, ?, ?, ?,?,?,?)',
                (type_travail, date_travail, id_exploitation, salarie_id,operation_culturale,duree,id_operation_sanitaire)
            )
            conn.commit()  # Enregistrer les modifications dans la base de données
            flash('Travail ajouté avec succès.', 'success')
            conn.close()  # Fermer la connexion après l'insertion
            
            return redirect(url_for('add_travail'))  # Redirection vers la même page après l'insertion
    
    return render_template('add_travail.html', exploitations=exploitations,salaries=salaries)

    


# route pour modifier travail
@app.route('/travaux/edit/<int:id>', methods=('GET', 'POST'))
def edit_travail(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Récupérer le salarié et les exploitations en utilisant une seule connexion
    travail = conn.execute('SELECT * FROM travaux_agricoles WHERE id_travail = ?', (id,)).fetchone()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()  # Récupérer toutes les exploitations
    salaries = conn.execute('SELECT * FROM salaries').fetchall()  # Récupérer toutes les salaries
    
    if request.method == 'POST':
        type_travail=request.form['type_travail']
        date_travail=request.form['date_travail']
        id_exploitation=request.form['id_exploitation']
        salarie_id=request.form['salarie_id']
        operation_culturale=request.form['operation_culturale']
        duree=request.form['duree']
        id_operation_sanitaire=request.form['id_operation_sanitaire']
        
        
        # Mettre à jour les informations du salarié
        conn.execute('''UPDATE travaux_agricoles 
                SET type_travail = ?, date_travail = ?, id_exploitation = ?, salarie_id = ?, 
                    operation_culturale = ?, duree = ?, id_operation_sanitaire = ? 
                WHERE id_travail = ?''', 
             (type_travail, date_travail, id_exploitation, salarie_id, operation_culturale, duree, id_operation_sanitaire, id))

        conn.commit()  # Confirmer les changements
        
        # Fermer la connexion après toutes les opérations
        conn.close()
        flash('travail modifié avec succès.')
        return redirect(url_for('travaux'))

    # Fermer la connexion après toutes les opérations de récupération si pas de mise à jour
    conn.close()
    
    return render_template('edit_travail.html', travail=travail, exploitations=exploitations,salaries=salaries)
# Route pour supprimer un travail

@app.route('/travaux/delete/<int:id>', methods=('GET', 'POST') )
def delete_travail(id):
    print('ok')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM travaux_agricoles WHERE id_travail = ?', (id,))
    conn.commit()
    conn.close()
    flash('Travail supprimé avec succès.')
    return redirect(url_for('travaux'))

# operations phytosanitaires.
@app.route('/operations_phytosanitaires')
def operations_phytosanitaires():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    operations_phytosanitaires = conn.execute(f'''
                    SELECT * FROM operations_phytosanitaires  
                    join exploitations on exploitations.id_exploitation=operations_phytosanitaires.id_exploitation
                    join salaries on salaries.id_salarie=operations_phytosanitaires.id_salarie
                    ''').fetchall()
    conn.close()
    
    return render_template('operations_phytosanitaires.html', operations_phytosanitaires=operations_phytosanitaires)

# Route pour supprimer un operation phytosanitaire

@app.route('/operations_phytosanitaires/delete/<int:id>', methods=('GET', 'POST') )
def delete_operation_phytosanitaire(id):
    print('ok')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM operations_phytosanitaires WHERE id_operation_sanitaire = ?', (id,))
    conn.commit()
    conn.close()
    flash('operation phytosanitaire supprimé avec succès.')
    return redirect(url_for('operations_phytosanitaires'))
# Route pour ajouter un travail
def entrainer_model_regression():
    conn = get_db_connection()
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

@app.route('/operations_phytosanitaires/add_operation', methods=('GET', 'POST'))
def add_operation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()  # Récupérer toutes les exploitations
    salaries=conn.execute('SELECT * FROM salaries').fetchall()  # Récupérer toutes les salaries
    conn.close()    
    if request.method == 'POST':
       
        maladie_visee=request.form['maladie_visee']
        stade_maladie=request.form['stade_maladie']
        methodes_traitement=request.form['methodes_traitement']
        observations=request.form['observations']
        date_traitement=request.form['date_traitement']
        id_exploitation=request.form['id_exploitation']
        id_salarie=request.form['id_salarie']
        # Ouverture de la connexion
        conn = get_db_connection()
        
        # Vérification si le salarié existe déjà
        verif = conn.execute(f'''SELECT * FROM operations_phytosanitaires
                              WHERE maladie_visee = ? and stade_maladie=? and methodes_traitement=?
                                and observations=? and date_traitement=? and id_exploitation=? and id_salarie=?
                             ''', (maladie_visee,stade_maladie,methodes_traitement,observations,date_traitement,id_exploitation,id_salarie, )).fetchone()
        print('ok')
        if verif:
            flash('opération phytosanitaire déjà existe.', 'error')
            conn.close()  # Fermer la connexion après la vérification
            return render_template('add_operation.html', exploitations=exploitations)
        else:
            # Insertion du salarié dans la base de données
            print(maladie_visee)
            print(stade_maladie)
            print(methodes_traitement)
            print(observations)
            etat=tester_modele(model, label_encoder_maladie, label_encoder_stade,
               label_encoder_methodes, label_encoder_observations,maladie_visee,stade_maladie,methodes_traitement,observations)
            
            conn.execute(
                'INSERT INTO operations_phytosanitaires (maladie_visee, stade_maladie, methodes_traitement, observations, date_traitement, id_exploitation, id_salarie, etat) VALUES (?,?, ?, ?, ?, ?, ?, ?)',
                (maladie_visee, stade_maladie, methodes_traitement, observations, date_traitement, id_exploitation, id_salarie, etat)
            )
            conn.commit()  # Enregistrer les modifications dans la base de données

            # Corrected flash message with proper string formatting
            

            
            flash(f'Opération sanitaire ajoutée avec succès. L\'état prédit est {etat}.', 'success')
            
            conn.close()  # Fermer la connexion après l'insertion
            
            return redirect(url_for('add_operation'))  # Redirection vers la même page après l'insertion
    
    return render_template('add_operation.html', exploitations=exploitations,salaries=salaries)

 # route pour modifier operations_phytosanitaires
@app.route('/operations_phytosanitaires/edit/<int:id>', methods=('GET', 'POST'))
def edit_operation(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Récupérer le salarié et les exploitations en utilisant une seule connexion
   
    operation = conn.execute('SELECT * FROM operations_phytosanitaires WHERE id_operation_sanitaire = ?', (id,)).fetchone()
    exploitations = conn.execute('SELECT * FROM exploitations').fetchall()  # Récupérer toutes les exploitations
    salaries = conn.execute('SELECT * FROM salaries').fetchall()  # Récupérer toutes les salaries
    
    if request.method == 'POST':
        maladie_visee=request.form['maladie_visee']
        stade_maladie=request.form['stade_maladie']
        methodes_traitement=request.form['methodes_traitement']
        observations=request.form['observations']
        date_traitement=request.form['date_traitement']
        id_exploitation=request.form['id_exploitation']
        id_salarie=request.form['id_salarie']
        
        
        # Mettre à jour les informations du salarié
        conn.execute('''UPDATE operations_phytosanitaires 
                SET maladie_visee = ?, stade_maladie = ?, methodes_traitement = ?, observations = ?, 
                    date_traitement = ?, id_exploitation = ?, id_salarie = ? 
                WHERE id_operation_sanitaire = ?''', 
             (maladie_visee, stade_maladie, methodes_traitement, observations, date_traitement, id_exploitation, id_salarie, id))

        conn.commit()  # Confirmer les changements
        
        # Fermer la connexion après toutes les opérations
        conn.close()
        flash('opération modifié avec succès.')
        return redirect(url_for('operations_phytosanitaires'))

    # Fermer la connexion après toutes les opérations de récupération si pas de mise à jour
    conn.close()
    
    return render_template('edit_operation.html', operation=operation, exploitations=exploitations,salaries=salaries)   
@app.route('/k-modes', methods=['GET', 'POST'])
def clustering_graph():
    # Connect to the SQLite database
    conn = get_db_connection()

    # Load the necessary data
    query = "SELECT type_travail FROM travaux_agricoles"
    df = pd.read_sql(query, conn)
    conn.close()

    # Ensure no missing values in 'type_travail'
    if df['type_travail'].isnull().any():
        df.dropna(subset=['type_travail'], inplace=True)

    # Prepare data for clustering
    X = df[['type_travail']]

    # Apply K-Modes clustering
    kmodes = KModes(n_clusters=4, init='Cao', n_init=5, verbose=0, random_state=42)
    df['cluster'] = kmodes.fit_predict(X)

    # Encode 'type_travail' for dissimilarity and silhouette score calculation
    label_encoder = LabelEncoder()
    X_encoded = label_encoder.fit_transform(df['type_travail']).reshape(-1, 1)
    dissimilarity_matrix = pairwise_distances(X_encoded, metric='hamming')
    silhouette_avg = silhouette_score(dissimilarity_matrix, df['cluster'], metric='precomputed')

    # Count the number of elements in each cluster
    cluster_counts = df['cluster'].value_counts().sort_index()

    # Generate bar chart for cluster distribution
    fig, ax = plt.subplots(figsize=(8, 6))
    cluster_counts.plot(kind='bar', color='skyblue', ax=ax)
    ax.set_title("Répartition des clusters")
    ax.set_xlabel("Clusters")
    ax.set_ylabel("Nombre d'éléments")

    # Add silhouette score to the chart
    ax.text(0.5, max(cluster_counts) - 1, f"Score silhouette: {silhouette_avg:.2f}", fontsize=12, color="red")

    # Save chart as a base64-encoded string
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    img.close()

    # Render the HTML template with the results
    return render_template('kmeans.html', graph_url=graph_url, cluster_counts=cluster_counts.to_dict())

@app.route('/synthese', methods=['GET', 'POST'])
def synthese():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    operation = []
    data = {}
    annee = None
    categorie = None
    template_name = 'synthese.html'  # Default template

    if request.method == 'POST':
        annee = request.form.get('annee')
        categorie = request.form.get('categorie')

        conn = get_db_connection()
        if categorie == "sanitaire":
            operation = conn.execute(
                'SELECT maladie_visee, stade_maladie, methodes_traitement, observations, id_exploitation, date_traitement, '
                'strftime("%Y", date_traitement) as year, strftime("%m", date_traitement) as month '
                'FROM operations_phytosanitaires WHERE strftime("%Y", date_traitement) = ?',
                (annee,)
            ).fetchall()

            maladie_count = {}
            months_set = set()

            for row in operation:
                month = int(row['month'])
                maladie = row['maladie_visee']
                months_set.add(month)

                if maladie not in maladie_count:
                    maladie_count[maladie] = [0] * 12
                maladie_count[maladie][month - 1] += 1

            months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc']
            months = [months[month - 1] for month in sorted(months_set)]

            data = {
                'months': months,
                'sales': [{'maladie': maladie, 'counts': counts} for maladie, counts in maladie_count.items()]
            }
            template_name = 'synthese.html'

        elif categorie == "travaux":
            operation = conn.execute(
                'SELECT type_travail, operation_culturale, id_exploitation, salarie_id, '
                'strftime("%H:%M:%S", Duree) as duree, id_operation_sanitaire, '
                'strftime("%d/%m/%Y", date_travail) as date, strftime("%m", date_travail) as month '
                'FROM travaux_agricoles WHERE strftime("%Y", date_travail) = ?',
                (annee,)
            ).fetchall()

            travail_count = {}
            months_set = set()

            for row in operation:
                month = int(row['month'])
                travail = row['type_travail']
                months_set.add(month)

                if travail not in travail_count:
                    travail_count[travail] = [0] * 12
                travail_count[travail][month - 1] += 1

            months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc']
            months = [months[month - 1] for month in sorted(months_set)]

            data = {
                'months': months,
                'sales': [{'travail': travail, 'counts': counts} for travail, counts in travail_count.items()]
            }
            template_name = 'synthese_travaux.html'

        elif categorie == "salaries":
            operation = conn.execute(
                'SELECT identifiant_sal, nom_salarie, prenom_salarie, date_embauche, '
                'strftime("%d/%m/%Y", date_embauche) as date_embauche, strftime("%m", date_embauche) as month, id_exploitation '
                'FROM salaries WHERE strftime("%Y", date_embauche) = ?',
                (annee,)
            ).fetchall()

            salaries_count = [0] * 12  # Initialise un tableau pour compter les salariés par mois

            for row in operation:
                month = int(row['month'])  # Obtenir le mois de la date d'embauche
                salaries_count[month - 1] += 1  # Incrémente le nombre de salariés pour le mois correspondant

            months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc']

            data = {
                'months': months,
                'counts': salaries_count  # Données prêtes pour le frontend
            }
            template_name = 'synthese_salaries.html'


        elif categorie == "chefs":
            operation = conn.execute(
                'SELECT prenom_chef, nom_chef, username_chef, id_exploitation '
                'FROM chefs_exploitation'
            ).fetchall()

            # Regrouper et compter les chefs
            chefs_count = {}
            for row in operation:
                chef = f"{row['prenom_chef']} {row['nom_chef']}"
                chefs_count[chef] = chefs_count.get(chef, 0) + 1

            # Préparer les données pour le graphique
            data = {
                'chefs': list(chefs_count.keys()),  # Liste des noms de chefs
                'counts': list(chefs_count.values())  # Fréquences des chefs
            }
            template_name = 'synthese_chefs.html'

        conn.close()

    # Render the chosen template
    return render_template(
        template_name,
        operation=operation,
        data=data,
        annee=annee,
        categorie=categorie
    )

if __name__ == '__main__':
    app.run(debug=True, port=5003)
