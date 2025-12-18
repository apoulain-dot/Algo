🛒 Marketplace – Plateforme de Vente pour Entreprises

Marketplace est une application web développée en Python permettant aux entreprises de vendre leurs produits en ligne et aux clients de passer des commandes simplement et en toute sécurité.
Le projet intègre une approche DevSecOps afin de garantir la qualité, la sécurité et la fiabilité du code.

🚀 Fonctionnalités

🏢 Côté Entreprises

Inscription et connexion sécurisées

Gestion complète des produits (ajout, modification, suppression)

Suivi et gestion du stock

Tableau de bord avec statistiques et graphiques

Consultation et gestion des commandes clients

🔐 Sécurité

La sécurité est au cœur du projet :

Mots de passe hachés avec SHA et Salt

Vérification des mots de passe via Have I Been Pwned

Intégration d’outils DevSecOps :

SemGrep : analyse statique du code

Gitleaks : détection de secrets exposés

Trivy : analyse de vulnérabilités

Pipelines automatisés via GitHub Actions

🛠️ Technologies Utilisées

Python 

Flask (backend web)

PyWebView (version desktop)

GitHub Actions (CI/CD & sécurité)

SemGrep, Gitleaks, Trivy

📁 Structure du Projet
.
├── .github/workflows   # Pipelines DevSecOps (CI/CD)
├── data                # Données & ressources
├── app.py              # Application web principale
├── desktop_app.py      # Version desktop (PyWebView)
├── requirements.txt    # Dépendances Python
└── README.md

⚙️ Installation
Prérequis

Python 3.8 ou supérieur

pip installé

Étapes d’installation

Cloner le dépôt :

git clone https://github.com/GabGuardia-hub/GabGuardia-hub.git


Accéder au dossier du projet :

cd GabGuardia-hub


Installer les dépendances :

pip install -r requirements.txt

▶️ Lancer l’Application
🌐 Mode Web (Navigateur)
python app.py


Puis ouvrir :

http://localhost:5000

🖥️ Mode Application Desktop
python desktop_app.py


➡️ L’application s’ouvre dans une fenêtre native grâce à PyWebView.

✅ Objectifs du Projet

Offrir une marketplace simple et efficace

Mettre en pratique les principes DevSecOps

Sécuriser le code dès le développement

Automatiser les contrôles de qualité et de sécurité
