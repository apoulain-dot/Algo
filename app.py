import csv
import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session
import webview
import bcrypt

app = Flask(__name__)
# Génère une clé aléatoire ou utilise une variable d'environnement
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# Chemins des fichiers CSV
USERS_FILE = './data/users.csv'
PRODUCTS_FILE = './data/products.csv'
ENTREPRISES_FILE = './data/entreprises.csv'


# ---------- Utils CSV / Auth ----------

def init_csv_files():
    os.makedirs('./data', exist_ok=True)
    
    # Fichier entreprises
    if not os.path.exists(ENTREPRISES_FILE):
        with open(ENTREPRISES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nom', 'created_at'])
    
    # Fichier users
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nom', 'email', 'mdp', 'role', 'created_at', 'id_entreprise'])

    # Fichier products avec image_url
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nom', 'description', 'prix', 'quantite', 'id_entreprise', 'image_url'])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(14)).decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def get_next_id(filename):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return 1
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        ids = [int(row['id']) for row in reader if row['id']]
        return max(ids) + 1 if ids else 1


def get_user_by_email(email):
    if not os.path.exists(USERS_FILE):
        return None
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['email'] == email:
                return row
    return None


# ---------- Fonctions Entreprises ----------

def get_entreprise_by_nom(nom):
    """Récupère une entreprise par son nom"""
    if not os.path.exists(ENTREPRISES_FILE):
        return None
    with open(ENTREPRISES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['nom'].lower() == nom.lower():
                return row
    return None


def get_entreprise_by_id(entreprise_id):
    """Récupère une entreprise par son ID"""
    if not os.path.exists(ENTREPRISES_FILE):
        return None
    with open(ENTREPRISES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == str(entreprise_id):
                return row
    return None


def create_entreprise(nom):
    """Crée une nouvelle entreprise et retourne son ID"""
    entreprise_id = get_next_id(ENTREPRISES_FILE)
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(ENTREPRISES_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([entreprise_id, nom, created_at])
    
    return entreprise_id


def get_all_entreprises():
    """Récupère toutes les entreprises"""
    entreprises = []
    if not os.path.exists(ENTREPRISES_FILE):
        return entreprises
    with open(ENTREPRISES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entreprises.append(row)
    return entreprises


# ---------- Utilisateurs ----------

def create_user(nom, email, password, nom_entreprise):
    """Crée un utilisateur et l'associe à une entreprise"""
    user_id = get_next_id(USERS_FILE)
    hashed_pwd = hash_password(password)
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Vérifier si l'entreprise existe
    entreprise = get_entreprise_by_nom(nom_entreprise)
    
    if entreprise:
        id_entreprise = entreprise['id']
    else:
        id_entreprise = create_entreprise(nom_entreprise)
    
    with open(USERS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([user_id, nom, email, hashed_pwd, 'user', created_at, id_entreprise])
    
    return user_id


# ---------- Produits (CSV) ----------

def get_products_by_entreprise(id_entreprise):
    products = []
    if not os.path.exists(PRODUCTS_FILE):
        return products
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id_entreprise'] == str(id_entreprise):
                products.append(row)
    return products


def get_product_by_id(product_id, entreprise_id):
    """Retourne un produit par id, en vérifiant qu'il appartient bien à l'entreprise."""
    if not os.path.exists(PRODUCTS_FILE):
        return None
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == str(product_id) and row['id_entreprise'] == str(entreprise_id):
                return row
    return None


def write_all_products(products):
    """Réécrit tout le fichier produits (pour update/delete)."""
    with open(PRODUCTS_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'nom', 'description', 'prix', 'quantite', 'id_entreprise', 'image_url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            writer.writerow(p)


def add_product(nom, description, prix, quantite, id_entreprise, image_url=''):
    product_id = get_next_id(PRODUCTS_FILE)
    with open(PRODUCTS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([product_id, nom, description, prix, quantite, id_entreprise, image_url])
    return product_id


def update_product(product_id, entreprise_id, nom, description, prix, quantite, image_url=''):
    products = []
    if not os.path.exists(PRODUCTS_FILE):
        return False

    updated = False
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == str(product_id) and row['id_entreprise'] == str(entreprise_id):
                row['nom'] = nom
                row['description'] = description
                row['prix'] = prix
                row['quantite'] = quantite
                row['image_url'] = image_url
                updated = True
            products.append(row)

    if updated:
        write_all_products(products)

    return updated


def delete_product(product_id, entreprise_id):
    products = []
    deleted = False
    if not os.path.exists(PRODUCTS_FILE):
        return False

    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == str(product_id) and row['id_entreprise'] == str(entreprise_id):
                deleted = True
                continue
            products.append(row)

    if deleted:
        write_all_products(products)

    return deleted


# ---------- Templates ----------

# ---------- Templates ----------

AUTH_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - Gestion de Stock</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-dark: #1e40af;
            --primary-light: #3b82f6;
            --accent: #06b6d4;
            --bg-main: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Manrope', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 100%);
            padding: 20px;
            position: relative;
        }
        
        body::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(6, 182, 212, 0.08) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .container {
            width: 100%;
            max-width: 440px;
            position: relative;
            z-index: 1;
            animation: slideUp 0.6s ease-out;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .logo {
            text-align: center;
            margin-bottom: 32px;
        }
        
        .logo-icon {
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
            box-shadow: var(--shadow-lg);
        }
        
        .logo-icon svg {
            width: 28px;
            height: 28px;
            stroke: white;
            stroke-width: 2.5;
            fill: none;
        }
        
        .logo h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.5px;
            margin-bottom: 8px;
        }
        
        .logo p {
            font-size: 15px;
            color: var(--text-secondary);
            font-weight: 400;
        }
        
        .auth-card {
            background: var(--bg-card);
            border-radius: 20px;
            padding: 40px;
            box-shadow: var(--shadow-lg), 0 0 0 1px rgba(0, 0, 0, 0.05);
            border: 1px solid var(--border);
        }
        
        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 32px;
            background: var(--bg-main);
            padding: 4px;
            border-radius: 12px;
        }
        
        .tab {
            flex: 1;
            padding: 10px 20px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.3s ease;
            font-family: 'Manrope', sans-serif;
        }
        
        .tab.active {
            background: white;
            color: var(--primary);
            box-shadow: var(--shadow-sm);
        }
        
        .tab:hover:not(.active) {
            color: var(--text-primary);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.4s ease-out;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-primary);
            font-size: 14px;
            font-weight: 600;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 1.5px solid var(--border);
            border-radius: 10px;
            font-size: 15px;
            font-family: 'Manrope', sans-serif;
            color: var(--text-primary);
            background: white;
            transition: all 0.2s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: var(--primary-light);
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        }
        
        .form-group input::placeholder {
            color: var(--text-secondary);
            opacity: 0.6;
        }
        
        .submit-btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Manrope', sans-serif;
            box-shadow: var(--shadow-md);
            margin-top: 8px;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .submit-btn:active {
            transform: translateY(0);
        }
        
        .alert {
            padding: 14px 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideDown 0.4s ease-out;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .alert-error {
            background: #fef2f2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        
        .alert-success {
            background: #f0fdf4;
            color: #166534;
            border: 1px solid #bbf7d0;
        }
        
        .alert::before {
            content: '';
            width: 4px;
            height: 100%;
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            border-radius: 10px 0 0 10px;
        }
        
        .alert-error::before {
            background: #dc2626;
        }
        
        .alert-success::before {
            background: #16a34a;
        }
        
        @media (max-width: 480px) {
            .auth-card {
                padding: 28px;
            }
            
            .logo h1 {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <div class="logo-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 4h4v3h-4V4zm10 16H4V9h16v11z"/>
                    <path d="M9 13h6v2H9z"/>
                </svg>
            </div>
            <h1>Gestion de Stock</h1>
            <p>Plateforme professionnelle de gestion</p>
        </div>
        
        <div class="auth-card">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('login')">Connexion</button>
                <button class="tab" onclick="switchTab('register')">Inscription</button>
            </div>
            
            <!-- Login Form -->
            <div id="login-tab" class="tab-content active">
                {% if login_error %}
                <div class="alert alert-error">{{ login_error }}</div>
                {% endif %}
                
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" placeholder="vous@exemple.com" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Mot de passe</label>
                        <input type="password" name="password" placeholder="••••••••" required>
                    </div>
                    
                    <button type="submit" class="submit-btn">Se connecter</button>
                </form>
            </div>
            
            <!-- Register Form -->
            <div id="register-tab" class="tab-content">
                {% if register_error %}
                <div class="alert alert-error">{{ register_error }}</div>
                {% endif %}
                {% if success %}
                <div class="alert alert-success">{{ success }}</div>
                {% endif %}
                
                <form method="POST" action="/register">
                    <div class="form-group">
                        <label>Nom complet</label>
                        <input type="text" name="nom" placeholder="Jean Dupont" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" placeholder="vous@exemple.com" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Nom de l'entreprise</label>
                        <input type="text" name="nom_entreprise" placeholder="Mon Entreprise" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Mot de passe</label>
                        <input type="password" name="password" placeholder="Minimum 8 caractères" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Confirmer le mot de passe</label>
                        <input type="password" name="confirm_password" placeholder="Répéter le mot de passe" required>
                    </div>
                    
                    <button type="submit" class="submit-btn">Créer un compte</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tab) {
            // Update tabs
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            // Update content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(tab + '-tab').classList.add('active');
        }
    </script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tableau de bord - Gestion de Stock</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-dark: #1e40af;
            --primary-light: #3b82f6;
            --accent: #06b6d4;
            --bg-main: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --success: #16a34a;
            --warning: #f59e0b;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Manrope', sans-serif;
            background: var(--bg-main);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .navbar {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .navbar-logo {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .navbar-logo svg {
            width: 20px;
            height: 20px;
            stroke: white;
            stroke-width: 2.5;
            fill: none;
        }
        
        .navbar-title {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .navbar-right {
            display: flex;
            align-items: center;
            gap: 24px;
        }
        
        .navbar-user {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .navbar-user-info {
            text-align: right;
        }
        
        .navbar-user-name {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .navbar-user-company {
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        .navbar-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent) 0%, var(--primary-light) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            color: white;
            font-size: 16px;
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: var(--bg-main);
            border: 1.5px solid var(--border);
            border-radius: 8px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .logout-btn:hover {
            background: white;
            color: var(--text-primary);
            border-color: var(--text-secondary);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px;
        }
        
        .page-header {
            margin-bottom: 32px;
        }
        
        .page-title {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .page-subtitle {
            font-size: 16px;
            color: var(--text-secondary);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .stat-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
        }
        
        .stat-icon svg {
            width: 24px;
            height: 24px;
            stroke-width: 2.5;
            fill: none;
        }
        
        .stat-icon.blue {
            background: rgba(59, 130, 246, 0.1);
        }
        
        .stat-icon.blue svg {
            stroke: var(--primary-light);
        }
        
        .stat-icon.green {
            background: rgba(22, 163, 74, 0.1);
        }
        
        .stat-icon.green svg {
            stroke: var(--success);
        }
        
        .stat-icon.cyan {
            background: rgba(6, 182, 212, 0.1);
        }
        
        .stat-icon.cyan svg {
            stroke: var(--accent);
        }
        
        .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -1px;
        }
        
        .quick-actions {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 32px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 24px;
        }
        
        .actions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
        }
        
        .action-card {
            padding: 20px;
            background: var(--bg-main);
            border: 1.5px solid var(--border);
            border-radius: 12px;
            text-decoration: none;
            color: var(--text-primary);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .action-card:hover {
            background: white;
            border-color: var(--primary-light);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .action-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        
        .action-icon svg {
            width: 22px;
            height: 22px;
            stroke: white;
            stroke-width: 2.5;
            fill: none;
        }
        
        .action-content {
            flex: 1;
        }
        
        .action-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .action-description {
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .navbar {
                padding: 12px 20px;
            }
            
            .navbar-right {
                gap: 12px;
            }
            
            .navbar-user-info {
                display: none;
            }
            
            .page-title {
                font-size: 28px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }

        .nav-link {
    padding: 8px 16px;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.nav-link:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}
    </style>
</head>
<body>
    <nav class="navbar">
<<<<<<< HEAD
    <div class="navbar-brand">
        <div class="navbar-logo">
            <svg viewBox="0 0 24 24">
                <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 4h4v3h-4V4zm10 16H4V9h16v11z"/>
            </svg>
=======
        <div class="navbar-brand">
            <div class="navbar-logo">
                <svg viewBox="0 0 24 24">
                    <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 4h4v3h-4V4zm10 16H4V9h16v11z"/>
                </svg>
            </div>
            <span class="navbar-title">Gestion de Stock</span>
        </div>
        
        <div class="navbar-right">
            <div class="navbar-user">
                <div class="navbar-user-info">
                    <div class="navbar-user-name">{{ user.nom }}</div>
                    <div class="navbar-user-company">{{ user.nom_entreprise }}</div>
                </div>
                <div class="navbar-avatar">{{ user.nom[0]|upper }}</div>
            </div>
            <a href="/logout" class="logout-btn">Déconnexion</a>
>>>>>>> da3806ed3828d8d4c6f0b418f4a9914e8f3e1efd
        </div>
        <span class="navbar-title">Gestion de Stock</span>
    </div>
    
    <div class="navbar-right">
        {% if user.role == 'admin' %}
        <a href="/admin/entreprises" class="nav-link" style="background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%); color: white; border: none;">
            ← Retour aux entreprises
        </a>
        {% endif %}
        <div class="navbar-user">
            <div class="navbar-user-info">
                <div class="navbar-user-name">{{ user.nom }}</div>
                <div class="navbar-user-company">{{ user.nom_entreprise }}</div>
            </div>
            <div class="navbar-avatar">{{ user.nom[0]|upper }}</div>
        </div>
        <a href="/logout" class="logout-btn">Déconnexion</a>
    </div>
</nav>
    
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">Tableau de bord</h1>
            <p class="page-subtitle">Vue d'ensemble de votre inventaire</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon blue">
                    <svg viewBox="0 0 24 24">
                        <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 4h4v3h-4V4zm10 16H4V9h16v11z"/>
                    </svg>
                </div>
                <div class="stat-label">Total des produits</div>
                <div class="stat-value">{{ products|length }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon green">
                    <svg viewBox="0 0 24 24">
                        <path d="M4 4h16v2H4V4zm0 4h16v2H4V8zm0 4h16v2H4v-2zm0 4h16v2H4v-2zm0 4h16v2H4v-2z"/>
                    </svg>
                </div>
                <div class="stat-label">Quantité totale</div>
                <div class="stat-value">{{ total_quantity }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon cyan">
                    <svg viewBox="0 0 24 24">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                        <path d="M12.5 7H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
                    </svg>
                </div>
                <div class="stat-label">Valeur totale</div>
                <div class="stat-value">{{ "%.2f"|format(total_value) }} €</div>
            </div>
        </div>
        
        <div class="quick-actions">
            <h2 class="section-title">Actions rapides</h2>
            <div class="actions-grid">
                <a href="/products" class="action-card">
                    <div class="action-icon">
                        <svg viewBox="0 0 24 24">
                            <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
                        </svg>
                    </div>
                    <div class="action-content">
                        <div class="action-title">Voir tous les produits</div>
                        <div class="action-description">Gérer votre inventaire</div>
                    </div>
                </a>
                
                <a href="/products/add" class="action-card">
                    <div class="action-icon">
                        <svg viewBox="0 0 24 24">
                            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                        </svg>
                    </div>
                    <div class="action-content">
                        <div class="action-title">Ajouter un produit</div>
                        <div class="action-description">Créer une nouvelle entrée</div>
                    </div>
                </a>
            </div>
        </div>
    </div>
</body>
</html>
'''

PRODUCT_LIST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Produits - Gestion de Stock</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-dark: #1e40af;
            --primary-light: #3b82f6;
            --accent: #06b6d4;
            --bg-main: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --danger: #dc2626;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Manrope', sans-serif;
            background: var(--bg-main);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .navbar {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .navbar-logo {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .navbar-logo svg {
            width: 20px;
            height: 20px;
            stroke: white;
            stroke-width: 2.5;
            fill: none;
        }
        
        .navbar-title {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .navbar-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .nav-link {
            padding: 8px 16px;
            background: var(--bg-main);
            border: 1.5px solid var(--border);
            border-radius: 8px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .nav-link:hover {
            background: white;
            color: var(--text-primary);
            border-color: var(--text-secondary);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px;
        }
        
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            flex-wrap: wrap;
            gap: 16px;
        }
        
        .page-title {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.5px;
        }
        
        .btn-primary {
            padding: 12px 24px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-md);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .btn-primary svg {
            width: 18px;
            height: 18px;
            stroke: white;
            stroke-width: 2.5;
            fill: none;
        }
        
        .search-bar {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
            margin-bottom: 24px;
        }
        
        .search-form {
            display: flex;
            gap: 12px;
        }
        
        .search-input {
            flex: 1;
            padding: 12px 16px;
            border: 1.5px solid var(--border);
            border-radius: 10px;
            font-size: 15px;
            font-family: 'Manrope', sans-serif;
            color: var(--text-primary);
            background: white;
            transition: all 0.2s ease;
        }
        
        .search-input:focus {
            outline: none;
            border-color: var(--primary-light);
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        }
        
        .search-btn {
            padding: 12px 24px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .search-btn:hover {
            transform: translateY(-1px);
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .product-card {
            background: var(--bg-card);
            border-radius: 16px;
            border: 1px solid var(--border);
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-sm);
        }
        
        .product-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }
        
        .product-image {
            width: 100%;
            height: 200px;
            background: var(--bg-main);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        
        .product-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .product-image-placeholder {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .product-image-placeholder svg {
            width: 40px;
            height: 40px;
            stroke: white;
            stroke-width: 2;
            fill: none;
        }
        
        .product-content {
            padding: 20px;
        }
        
        .product-name {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .product-description {
            font-size: 14px;
            color: var(--text-secondary);
            margin-bottom: 16px;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .product-info {
            display: flex;
            gap: 16px;
            margin-bottom: 16px;
            padding: 12px;
            background: var(--bg-main);
            border-radius: 10px;
        }
        
        .product-info-item {
            flex: 1;
        }
        
        .product-info-label {
            font-size: 12px;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .product-info-value {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .product-actions {
            display: flex;
            gap: 8px;
        }
        
        .btn-edit {
            flex: 1;
            padding: 10px;
            background: var(--bg-main);
            border: 1.5px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            text-align: center;
            transition: all 0.2s ease;
        }
        
        .btn-edit:hover {
            background: white;
            border-color: var(--primary-light);
            color: var(--primary-light);
        }
        
        .btn-delete {
            padding: 10px 16px;
            background: var(--bg-main);
            border: 1.5px solid var(--border);
            border-radius: 8px;
            color: var(--danger);
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .btn-delete:hover {
            background: #fee;
            border-color: var(--danger);
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            margin-top: 32px;
        }
        
        .pagination a,
        .pagination span {
            padding: 10px 16px;
            background: var(--bg-card);
            border: 1.5px solid var(--border);
            border-radius: 8px;
            text-decoration: none;
            color: var(--text-primary);
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .pagination a:hover {
            background: white;
            border-color: var(--primary-light);
            color: var(--primary-light);
        }
        
        .pagination span.current {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border-color: var(--primary);
        }
        
        .empty-state {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 64px 32px;
            text-align: center;
            border: 1px solid var(--border);
        }
        
        .empty-icon {
            width: 80px;
            height: 80px;
            background: var(--bg-main);
            border-radius: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
        }
        
        .empty-icon svg {
            width: 40px;
            height: 40px;
            stroke: var(--text-secondary);
            stroke-width: 2;
            fill: none;
        }
        
        .empty-title {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .empty-text {
            font-size: 16px;
            color: var(--text-secondary);
            margin-bottom: 24px;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .navbar {
                padding: 12px 20px;
            }
            
            .page-header {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .products-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-brand">
            <div class="navbar-logo">
                <svg viewBox="0 0 24 24">
                    <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 4h4v3h-4V4zm10 16H4V9h16v11z"/>
                </svg>
            </div>
            <span class="navbar-title">Gestion de Stock</span>
        </div>
        
        <div class="navbar-right">
            <a href="/dashboard" class="nav-link">Tableau de bord</a>
            <a href="/logout" class="nav-link">Déconnexion</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">Produits</h1>
            <a href="/products/add" class="btn-primary">
                <svg viewBox="0 0 24 24">
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
                Nouveau produit
            </a>
        </div>
        
        <div class="search-bar">
            <form method="GET" action="/products" class="search-form">
                <input 
                    type="text" 
                    name="q" 
                    class="search-input" 
                    placeholder="Rechercher un produit..."
                    value="{{ q }}">
                <button type="submit" class="search-btn">Rechercher</button>
            </form>
        </div>
        
        {% if products %}
        <div class="products-grid">
            {% for p in products %}
            <div class="product-card">
                <div class="product-image">
                    {% if p.image_url %}
                    <img src="{{ p.image_url }}" alt="{{ p.nom }}">
                    {% else %}
                    <div class="product-image-placeholder">
                        <svg viewBox="0 0 24 24">
                            <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 4h4v3h-4V4zm10 16H4V9h16v11z"/>
                        </svg>
                    </div>
                    {% endif %}
                </div>
                
                <div class="product-content">
                    <h3 class="product-name">{{ p.nom }}</h3>
                    <p class="product-description">{{ p.description or 'Aucune description' }}</p>
                    
                    <div class="product-info">
                        <div class="product-info-item">
                            <div class="product-info-label">Prix</div>
                            <div class="product-info-value">{{ p.prix }} €</div>
                        </div>
                        <div class="product-info-item">
                            <div class="product-info-label">Quantité</div>
                            <div class="product-info-value">{{ p.quantite }}</div>
                        </div>
                    </div>
                    
                    <div class="product-actions">
                        <a href="/products/{{ p.id }}/edit" class="btn-edit">Modifier</a>
                        <form method="POST" action="/products/{{ p.id }}/delete" style="display: inline;">
                            <button type="submit" class="btn-delete" onclick="return confirm('Êtes-vous sûr de vouloir supprimer ce produit ?')">
                                Supprimer
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if total_pages > 1 %}
        <div class="pagination">
            {% if page > 1 %}
            <a href="?page={{ page - 1 }}{% if q %}&q={{ q }}{% endif %}">Précédent</a>
            {% endif %}
            
            {% for p in range(1, total_pages + 1) %}
                {% if p == page %}
                <span class="current">{{ p }}</span>
                {% else %}
                <a href="?page={{ p }}{% if q %}&q={{ q }}{% endif %}">{{ p }}</a>
                {% endif %}
            {% endfor %}
            
            {% if page < total_pages %}
            <a href="?page={{ page + 1 }}{% if q %}&q={{ q }}{% endif %}">Suivant</a>
            {% endif %}
        </div>
        {% endif %}
        
        {% else %}
        <div class="empty-state">
            <div class="empty-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 4h4v3h-4V4zm10 16H4V9h16v11z"/>
                </svg>
            </div>
            <h2 class="empty-title">Aucun produit trouvé</h2>
            <p class="empty-text">Commencez par ajouter votre premier produit</p>
            <a href="/products/add" class="btn-primary">
                <svg viewBox="0 0 24 24">
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
                Ajouter un produit
            </a>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

PRODUCT_FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if product %}Modifier{% else %}Ajouter{% endif %} un produit - Gestion de Stock</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-dark: #1e40af;
            --primary-light: #3b82f6;
            --accent: #06b6d4;
            --bg-main: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Manrope', sans-serif;
            background: var(--bg-main);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .navbar {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .navbar-logo {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .navbar-logo svg {
            width: 20px;
            height: 20px;
            stroke: white;
            stroke-width: 2.5;
            fill: none;
        }
        
        .navbar-title {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .navbar-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .nav-link {
            padding: 8px 16px;
            background: var(--bg-main);
            border: 1.5px solid var(--border);
            border-radius: 8px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .nav-link:hover {
            background: white;
            color: var(--text-primary);
            border-color: var(--text-secondary);
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 32px;
        }
        
        .page-header {
            margin-bottom: 32px;
        }
        
        .page-title {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .page-subtitle {
            font-size: 16px;
            color: var(--text-secondary);
        }
        
        .form-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 32px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-primary);
            font-size: 14px;
            font-weight: 600;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 12px 16px;
            border: 1.5px solid var(--border);
            border-radius: 10px;
            font-size: 15px;
            font-family: 'Manrope', sans-serif;
            color: var(--text-primary);
            background: white;
            transition: all 0.2s ease;
        }
        
        .form-group textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: var(--primary-light);
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
        }
        
        .form-group input::placeholder,
        .form-group textarea::placeholder {
            color: var(--text-secondary);
            opacity: 0.6;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        
        .image-preview {
            margin-top: 16px;
            border-radius: 12px;
            overflow: hidden;
            display: none;
            border: 1px solid var(--border);
        }
        
        .image-preview img {
            width: 100%;
            max-height: 300px;
            object-fit: cover;
        }
        
        .form-actions {
            display: flex;
            gap: 12px;
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
        }
        
        .btn-primary {
            flex: 1;
            padding: 14px 24px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Manrope', sans-serif;
            box-shadow: var(--shadow-md);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .btn-secondary {
            padding: 14px 24px;
            background: var(--bg-main);
            border: 1.5px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            text-decoration: none;
            font-size: 16px;
            font-weight: 600;
            text-align: center;
            transition: all 0.2s ease;
        }
        
        .btn-secondary:hover {
            background: white;
            border-color: var(--text-secondary);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .navbar {
                padding: 12px 20px;
            }
            
            .form-card {
                padding: 24px;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .form-actions {
                flex-direction: column-reverse;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-brand">
            <div class="navbar-logo">
                <svg viewBox="0 0 24 24">
                    <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 4h4v3h-4V4zm10 16H4V9h16v11z"/>
                </svg>
            </div>
            <span class="navbar-title">Gestion de Stock</span>
        </div>
        
        <div class="navbar-right">
            <a href="/dashboard" class="nav-link">Tableau de bord</a>
            <a href="/products" class="nav-link">Produits</a>
            <a href="/logout" class="nav-link">Déconnexion</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">{% if product %}Modifier le produit{% else %}Nouveau produit{% endif %}</h1>
            <p class="page-subtitle">{% if product %}Modifiez les informations du produit{% else %}Ajoutez un nouveau produit à votre inventaire{% endif %}</p>
        </div>
        
        <div class="form-card">
            <form method="POST">
                <div class="form-group">
                    <label>Nom du produit</label>
                    <input type="text" name="nom" placeholder="Ex: Ordinateur portable Dell" 
                           value="{{ product.nom if product else '' }}" required>
                </div>
                
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" 
                              placeholder="Décrivez votre produit...">{{ product.description if product else '' }}</textarea>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label>Prix (€)</label>
                        <input type="number" name="prix" step="0.01" placeholder="0.00" 
                               value="{{ product.prix if product else '' }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Quantité</label>
                        <input type="number" name="quantite" placeholder="0" 
                               value="{{ product.quantite if product else '' }}" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>URL de l'image (optionnel)</label>
                    <input type="url" name="image_url" id="image_url" 
                           placeholder="https://exemple.com/image.jpg"
                           value="{{ product.image_url if product else '' }}"
                           onchange="previewImage()">
                    <div id="preview" class="image-preview">
                        <img id="preview-img" src="" alt="Aperçu">
                    </div>
                </div>
                
                <div class="form-actions">
                    <a href="/products" class="btn-secondary">Annuler</a>
                    <button type="submit" class="btn-primary">
                        {% if product %}Enregistrer les modifications{% else %}Ajouter le produit{% endif %}
                    </button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function previewImage() {
            const url = document.getElementById('image_url').value;
            const preview = document.getElementById('preview');
            const img = document.getElementById('preview-img');
            
            if (url) {
                img.src = url;
                preview.style.display = 'block';
                
                img.onerror = function() {
                    preview.style.display = 'none';
                };
            } else {
                preview.style.display = 'none';
            }
        }
        
        window.onload = function() {
            previewImage();
        };
    </script>
</body>
</html>
"""
ADMIN_ENTREPRISES_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Administration - Entreprises</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-dark: #1e40af;
            --primary-light: #3b82f6;
            --accent: #06b6d4;
            --bg-main: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --admin-badge: #8b5cf6;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Manrope', sans-serif;
            background: var(--bg-main);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .navbar {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .navbar-logo {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--admin-badge) 0%, #a78bfa 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .navbar-logo svg {
            width: 20px;
            height: 20px;
            stroke: white;
            stroke-width: 2.5;
            fill: none;
        }
        
        .navbar-title {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .admin-badge {
            display: inline-block;
            padding: 4px 12px;
            background: linear-gradient(135deg, var(--admin-badge) 0%, #a78bfa 100%);
            border-radius: 20px;
            font-size: 12px;
            margin-left: 8px;
            font-weight: 600;
            color: white;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .navbar-right {
            display: flex;
            align-items: center;
            gap: 24px;
        }
        
        .navbar-user {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .navbar-user-name {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: var(--bg-main);
            border: 1.5px solid var(--border);
            border-radius: 8px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .logout-btn:hover {
            background: white;
            color: var(--text-primary);
            border-color: var(--text-secondary);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px;
        }
        
        .page-header {
            margin-bottom: 32px;
        }
        
        .page-title {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .page-subtitle {
            font-size: 16px;
            color: var(--text-secondary);
        }
        
        .entreprises-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 24px;
        }
        
        .entreprise-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 28px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
            transition: all 0.3s ease;
        }
        
        .entreprise-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
            border-color: var(--primary-light);
        }
        
        .entreprise-header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }
        
        .entreprise-icon {
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 700;
            color: white;
            flex-shrink: 0;
        }
        
        .entreprise-info {
            flex: 1;
        }
        
        .entreprise-name {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        
        .entreprise-id {
            font-size: 13px;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .entreprise-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .stat-item {
            padding: 12px;
            background: var(--bg-main);
            border-radius: 10px;
        }
        
        .stat-label {
            font-size: 12px;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .stat-value {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .btn-access {
            width: 100%;
            padding: 12px 20px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-sm);
        }
        
        .btn-access:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .empty-state {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 64px 32px;
            text-align: center;
            border: 1px solid var(--border);
        }
        
        .empty-icon {
            width: 80px;
            height: 80px;
            background: var(--bg-main);
            border-radius: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
        }
        
        .empty-icon svg {
            width: 40px;
            height: 40px;
            stroke: var(--text-secondary);
            stroke-width: 2;
            fill: none;
        }
        
        .empty-title {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .empty-text {
            font-size: 16px;
            color: var(--text-secondary);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .navbar {
                padding: 12px 20px;
            }
            
            .entreprises-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-brand">
            <div class="navbar-logo">
                <svg viewBox="0 0 24 24">
                    <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                </svg>
            </div>
            <span class="navbar-title">Admin Panel<span class="admin-badge">Administrateur</span></span>
        </div>
        
        <div class="navbar-right">
            <div class="navbar-user">
                <span class="navbar-user-name">{{ user.nom }}</span>
            </div>
            <a href="/logout" class="logout-btn">Déconnexion</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">Gestion des Entreprises</h1>
            <p class="page-subtitle">Accédez aux tableaux de bord des entreprises</p>
        </div>
        
        {% if entreprises %}
        <div class="entreprises-grid">
            {% for entreprise in entreprises %}
            <div class="entreprise-card">
                <div class="entreprise-header">
                    <div class="entreprise-icon">{{ entreprise.nom[0]|upper }}</div>
                    <div class="entreprise-info">
                        <div class="entreprise-name">{{ entreprise.nom }}</div>
                        <div class="entreprise-id">ID: {{ entreprise.id }}</div>
                    </div>
                </div>
                
                <div class="entreprise-stats">
                    <div class="stat-item">
                        <div class="stat-label">Produits</div>
                        <div class="stat-value">{{ entreprise.nb_products }}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Créée le</div>
                        <div class="stat-value">{{ entreprise.created_at[:10] }}</div>
                    </div>
                </div>
                
                <a href="/admin/entreprise/{{ entreprise.id }}" class="btn-access">
                    Accéder au dashboard
                </a>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-state">
            <div class="empty-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M20 7h-4V4c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2z"/>
                </svg>
            </div>
            <h2 class="empty-title">Aucune entreprise</h2>
            <p class="empty-text">Il n'y a pas encore d'entreprise enregistrée</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

# ---------- Routes Auth / Index ----------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(AUTH_TEMPLATE, login_error=None, register_error=None, success=None)


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = get_user_by_email(email)
    if user and check_password(password, user['mdp']):
        if 'id_entreprise' in user and user['id_entreprise']:
            entreprise = get_entreprise_by_id(user['id_entreprise'])
            session['id_entreprise'] = user['id_entreprise']
            session['nom_entreprise'] = entreprise['nom'] if entreprise else 'Entreprise inconnue'
        else:
            nom_entreprise = user.get('nom_entreprise', 'Mon Entreprise')
            entreprise = get_entreprise_by_nom(nom_entreprise)
            
            if entreprise:
                id_entreprise = entreprise['id']
            else:
                id_entreprise = create_entreprise(nom_entreprise)
            
            session['id_entreprise'] = id_entreprise
            session['nom_entreprise'] = nom_entreprise
        
        session['user_id'] = user['id']
        session['user_nom'] = user['nom']
        session['user_role'] = user.get('role', 'user')  
        
        # Rediriger vers admin ou dashboard selon le rôle
        if session['user_role'] == 'admin':
            return redirect(url_for('admin_entreprises'))
        else:
            return redirect(url_for('dashboard'))
    else:
        return render_template_string(
            AUTH_TEMPLATE,
            login_error='Email ou mot de passe incorrect',
            register_error=None,
            success=None
        )


@app.route('/register', methods=['POST'])
def register():
    nom = request.form['nom']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    nom_entreprise = request.form['nom_entreprise']

    if password != confirm_password:
        return render_template_string(
            AUTH_TEMPLATE,
            register_error='Les mots de passe ne correspondent pas',
            login_error=None,
            success=None
        )

    if len(password) < 8:
        return render_template_string(
            AUTH_TEMPLATE,
            register_error='Le mot de passe doit contenir au moins 8 caractères',
            login_error=None,
            success=None
        )

    if get_user_by_email(email):
        return render_template_string(
            AUTH_TEMPLATE,
            register_error='Cet email est déjà utilisé',
            login_error=None,
            success=None
        )

    create_user(nom, email, password, nom_entreprise)
    return render_template_string(
        AUTH_TEMPLATE,
        success='Inscription réussie ! Vous pouvez maintenant vous connecter.',
        login_error=None,
        register_error=None
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ---------- Dashboard ----------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Si admin, rediriger vers la liste des entreprises
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin_entreprises'))

    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': session['nom_entreprise'],
        'id_entreprise': session['id_entreprise']
    }

    products = get_products_by_entreprise(user['id_entreprise'])

    total_quantity = sum(int(p['quantite']) for p in products) if products else 0
    total_value = sum(float(p['prix']) * int(p['quantite']) for p in products) if products else 0

    return render_template_string(
        DASHBOARD_TEMPLATE,
        user=user,
        products=products,
        total_quantity=total_quantity,
        total_value=total_value
    )


# ---------- Produits : liste / CRUD / recherche / pagination ----------

@app.route('/products')
def product_list():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    if session.get('user_role') == 'admin' and 'admin_viewing_entreprise' in session:
        entreprise_id = session['admin_viewing_entreprise']
        nom_entreprise = session['admin_viewing_entreprise_nom']
    else:
        entreprise_id = session['id_entreprise']
        nom_entreprise = session['nom_entreprise']

    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': nom_entreprise,
        'id_entreprise': entreprise_id
    }

    all_products = get_products_by_entreprise(entreprise_id)

    q = request.args.get('q', '').strip()
    if q:
        all_products = [p for p in all_products if q.lower() in p['nom'].lower()]

    page = request.args.get('page', 1, type=int)
    per_page = 10
    total = len(all_products)
    total_pages = max((total - 1) // per_page + 1, 1)
    start = (page - 1) * per_page
    end = start + per_page
    products_page = all_products[start:end]

    return render_template_string(
        PRODUCT_LIST_TEMPLATE,
        user=user,
        products=products_page,
        page=page,
        total_pages=total_pages,
        q=q
    )


@app.route('/products/add', methods=['GET', 'POST'])
def product_add():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    if session.get('user_role') == 'admin' and 'admin_viewing_entreprise' in session:
        entreprise_id = session['admin_viewing_entreprise']
        nom_entreprise = session['admin_viewing_entreprise_nom']
    else:
        entreprise_id = session['id_entreprise']
        nom_entreprise = session['nom_entreprise']

    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': nom_entreprise,
        'id_entreprise': entreprise_id
    }

    if request.method == 'POST':
        nom = request.form['nom']
        description = request.form.get('description', '')
        prix = request.form['prix']
        quantite = request.form['quantite']
        image_url = request.form.get('image_url', '')

        add_product(nom, description, prix, quantite, entreprise_id, image_url)
        return redirect(url_for('product_list'))

    return render_template_string(PRODUCT_FORM_TEMPLATE, user=user, product=None)


@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    # Déterminer quelle entreprise utiliser
    if session.get('user_role') == 'admin' and 'admin_viewing_entreprise' in session:
        entreprise_id = session['admin_viewing_entreprise']
        nom_entreprise = session['admin_viewing_entreprise_nom']
    else:
        entreprise_id = session['id_entreprise']
        nom_entreprise = session['nom_entreprise']

    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': nom_entreprise,
        'id_entreprise': entreprise_id
    }

    product = get_product_by_id(product_id, entreprise_id)
    if not product:
        return "Produit introuvable ou non autorisé", 404

    if request.method == 'POST':
        nom = request.form['nom']
        description = request.form.get('description', '')
        prix = request.form['prix']
        quantite = request.form['quantite']
        image_url = request.form.get('image_url', '')

        update_product(product_id, entreprise_id, nom, description, prix, quantite, image_url)
        return redirect(url_for('product_list'))

    return render_template_string(PRODUCT_FORM_TEMPLATE, user=user, product=product)


@app.route('/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    # Déterminer quelle entreprise utiliser
    if session.get('user_role') == 'admin' and 'admin_viewing_entreprise' in session:
        entreprise_id = session['admin_viewing_entreprise']
    else:
        entreprise_id = session['id_entreprise']

    delete_product(product_id, entreprise_id)
    return redirect(url_for('product_list'))

# ---------- Routes Admin ----------

@app.route('/admin/entreprises')
def admin_entreprises():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    
    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'role': session['user_role']
    }
    
    entreprises = get_all_entreprises()
    
    # Ajouter le nombre de produits pour chaque entreprise
    for entreprise in entreprises:
        products = get_products_by_entreprise(entreprise['id'])
        entreprise['nb_products'] = len(products)
    
    return render_template_string(
        ADMIN_ENTREPRISES_TEMPLATE,
        user=user,
        entreprises=entreprises
    )


@app.route('/admin/entreprise/<int:entreprise_id>')
def admin_view_entreprise(entreprise_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    
    entreprise = get_entreprise_by_id(entreprise_id)
    if not entreprise:
        return "Entreprise introuvable", 404
    
    # Sauvegarder l'entreprise actuelle dans la session pour l'admin
    session['admin_viewing_entreprise'] = entreprise_id
    session['admin_viewing_entreprise_nom'] = entreprise['nom']
    
    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': entreprise['nom'],
        'id_entreprise': entreprise_id,
        'role': 'admin'
    }
    
    products = get_products_by_entreprise(entreprise_id)
    total_quantity = sum(int(p['quantite']) for p in products) if products else 0
    total_value = sum(float(p['prix']) * int(p['quantite']) for p in products) if products else 0
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        user=user,
        products=products,
        total_quantity=total_quantity,
        total_value=total_value
    )

# ---------- Lancement Webview / dev ----------

def start_app():
    init_csv_files()
    window = webview.create_window('Gestion de Produits', app, width=1200, height=800)
    webview.start()


if __name__ == '__main__':
    init_csv_files()
    app.run(debug=False)
    start_app()