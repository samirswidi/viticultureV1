import matplotlib.pyplot as plt

# Données de l'exemple
categories = ['Morte', 'Vivante']
values = [24, 7]

# Création du graphique en barres
plt.figure(figsize=(10, 6))
bars = plt.bar(categories, values, color=['#ff9999', '#66b3ff'])

# Ajouter des étiquettes et un titre
plt.xlabel('Catégories')
plt.ylabel('Valeurs')


# Ajouter des étiquettes de valeur au-dessus de chaque barre
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, yval + 1,  # Position de l'étiquette
             f'{yval}', ha='center', va='bottom', fontsize=12, fontweight='bold')

# Afficher des informations supplémentaires
plt.text(-0.1, max(values) + 5, 'Répartition des états de l\'exemple\n(76 morts, 27 vivants)',
         fontsize=10, ha='left', color='gray')

# Afficher le graphique
plt.show()
