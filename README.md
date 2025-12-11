# Marketplace - Plateforme de Vente pour Entreprises

Application web Python complète permettant aux entreprises de vendre leurs produits en ligne.

## 🚀 Fonctionnalités

### Pour les Entreprises
- ✅ Inscription et connexion sécurisées
- ✅ Vérification des mots de passe compromis via l'API Have I Been Pwned
- ✅ Ajout, modification et suppression de produits
- ✅ Gestion du stock
- ✅ Tableau de bord complet
- ✅ Visualisation des commandes
- ✅ Statistiques avec graphiques (Matplotlib/Seaborn)

### Pour les Clients
- ✅ Navigation des produits disponibles
- ✅ Recherche par nom et catégorie
- ✅ Système de commande simple
- ✅ Tri et filtrage des produits

## 📦 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner ou télécharger le projet**

2. **Installer les dépendances**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## 🎯 Lancement de l'Application

### Option 1 : Mode Web (Navigateur)

Lancez le serveur Flask classique :
\`\`\`bash
python app.py
\`\`\`

Puis accédez à l'application via votre navigateur : `http://localhost:5000`

### Option 2 : Mode Desktop (Application Native)

Lancez l'application dans une fenêtre desktop avec PyWebView :
\`\`\`bash
python desktop_app.py
\`\`\`

L'application s'ouvrira automatiquement dans une fenêtre native (sans navigateur visible).

**Avantages du mode desktop :**
- Interface comme une vraie application installée
- Pas besoin d'ouvrir un navigateur
- Expérience utilisateur optimale
- Démarrage automatique du serveur Flask en arrière-plan

## 🔐 Sécurité

- **Hachage des mots de passe** : Utilisation de Werkzeug pour un stockage sécurisé
- **API Have I Been Pwned** : Vérification automatique des mots de passe compromis lors de l'inscription
- **Sessions sécurisées** : Protection des routes avec décorateurs
- **Validation des données** : Contrôles côté serveur

## 📊 Base de données

L'application utilise SQLite3 avec trois tables principales :
- `users` : Informations des entreprises
- `products` : Catalogue des produits
- `orders` : Historique des commandes

La base de données est créée automatiquement au premier lancement.

## 🎨 Interface

- Design moderne avec Bootstrap 5
- Interface responsive (mobile-friendly)
- Icônes Bootstrap Icons
- Animations et transitions CSS
- Graphiques interactifs avec Matplotlib

## 📈 Statistiques

L'application génère automatiquement :
- Graphique des revenus par produit (bar chart)
- Répartition des produits par catégorie (pie chart)
- Métriques du tableau de bord

## 🛠️ Technologies utilisées

- **Backend** : Flask (Python 3)
- **Base de données** : SQLite3
- **Frontend** : HTML5, CSS3, Bootstrap 5
- **Visualisation** : Matplotlib, Seaborn
- **Sécurité** : Werkzeug, hashlib, requests (Have I Been Pwned API)
- **Desktop** : PyWebView 5.0.5 (pour l'application native)

## 📝 Utilisation

### Pour une entreprise :

1. **S'inscrire** avec le nom de l'entreprise, email et mot de passe
2. **Se connecter** au tableau de bord
3. **Ajouter des produits** avec nom, description, prix, stock et catégorie
4. **Gérer les produits** (modifier, supprimer)
5. **Consulter les commandes** reçues
6. **Voir les statistiques** de vente

### Pour un client :

1. **Parcourir** les produits sur la page d'accueil
2. **Rechercher** des produits spécifiques
3. **Passer une commande** en remplissant le formulaire
4. Recevoir une confirmation

## 💡 Conseils

- **Pour un usage personnel/local** : Utilisez `desktop_app.py` pour une meilleure expérience
- **Pour un déploiement serveur** : Utilisez `app.py` et configurez avec Gunicorn/uWSGI
- **Pour le développement** : Utilisez `app.py` en mode debug

## 🔄 Évolutions possibles

- Système de paiement (Stripe, PayPal)
- Notifications email
- Upload d'images pour les produits
- Système d'avis et de notes
- Dashboard administrateur
- Export des données en CSV/PDF
- API REST pour intégrations tierces

## 📄 Licence

Projet éducatif - Libre d'utilisation et de modification

## 👨‍💻 Support

Pour toute question ou problème, consultez la documentation Flask : https://flask.palletsprojects.com/
