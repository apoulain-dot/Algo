
---

# Marketplace – Plateforme de Vente

Une application web en Python qui permet aux entreprises de vendre leurs produits en ligne et aux clients de passer des commandes.

##  Fonctionnalités

### Entreprises

* Inscription / connexion sécurisée
* Gestion des produits : ajout, modification, suppression
* Gestion du stock
* Tableau de bord et statistiques (graphiques)
* Visualisation des commandes

### Clients

* Consultation des produits
* Recherche et filtres
* Passage de commande simple

##  Installation

### Prérequis

* Python 3.8+
* pip installé

### Étapes

1. Télécharger ou cloner le projet
2. Installer les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

##  Lancer l’application

### Mode Web (navigateur)

```bash
python app.py
```

Ouvrir : `http://localhost:5000`

### Mode Application Desktop

```bash
python desktop_app.py
```

→ L’application s’ouvre dans une fenêtre native (grâce à PyWebView).

##  Sécurité

* Mots de passe hachés SHA
* Salt 
* Vérification de sécurité via Have I Been Pwned
* Sessions sécurisées
* Validation des données

##  Base de données

SQLite3 avec 3 tables :

* `users` (entreprises)
* `products`
* `orders`

La base est créée automatiquement au premier lancement.

##  Interface

* Bootstrap 5
* Design responsive
* Graphiques Matplotlib / Seaborn

##  Statistiques

* Revenus par produit
* Répartition des catégories
* Infos du tableau de bord

##  Technologies

* **Backend** : Flask
* **BDD** : SQLite3
* **Frontend** : HTML/CSS/Bootstrap
* **Graphiques** : Matplotlib, Seaborn
* **Desktop** : PyWebView

##  Utilisation

### Entreprises

1. S’inscrire
2. Se connecter
3. Ajouter et gérer les produits
4. Consulter les commandes
5. Voir les statistiques

### Clients

1. Parcourir les produits
2. Rechercher / filtrer
3. Passer une commande

##  Améliorations possibles

* Paiement en ligne
* Envoi d’emails
* Upload d’images
* Avis clients
* Export CSV/PDF
* API REST


