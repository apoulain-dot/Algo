from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cle_secrete_projet_univ'

DATA_FILE = 'data/produits.csv'

def initialiser_csv():
    """Crée le fichier CSV avec en-tête si il n'existe pas"""
    if not os.path.exists(DATA_FILE):
        os.makedirs('data', exist_ok=True)
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nom', 'prix', 'description', 'stock', 'date_ajout'])

def lire_produits():
    """Lit tous les produits du CSV"""
    initialiser_csv()
    produits = []
    try:
        with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['prix'] = float(row['prix'])
                row['stock'] = int(row['stock'])
                produits.append(row)
    except FileNotFoundError:
        pass
    return produits

def ecrire_produits(produits):
    """Écrit la liste complète des produits dans le CSV"""
    initialiser_csv()
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        if produits:
            fieldnames = produits[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(produits)

def generer_id():
    """Génère un ID unique pour un nouveau produit"""
    produits = lire_produits()
    return len(produits) + 1

@app.route('/')
def index():
    produits = lire_produits()
    return render_template('index.html', produits=produits)

if __name__ == '__main__':
    # Ajoute 3 produits de test au premier lancement
    initialiser_csv()
    produits = lire_produits()
    if not produits:
        produits_test = [
            {'id': '1', 'nom': 'Ordinateur Portable', 'prix': '899.99', 'description': 'i7 16Go RAM', 'stock': '5', 'date_ajout': datetime.now().strftime('%Y-%m-%d')},
            {'id': '2', 'nom': 'Souris sans fil', 'prix': '29.99', 'description': 'Batterie longue durée', 'stock': '25', 'date_ajout': datetime.now().strftime('%Y-%m-%d')},
            {'id': '3', 'nom': 'Clavier mécanique', 'prix': '79.99', 'description': 'RGB rétroéclairé', 'stock': '12', 'date_ajout': datetime.now().strftime('%Y-%m-%d')}
        ]
        ecrire_produits(produits_test)
    
    app.run(debug=True, port=5000)
