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

AUTH_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - Gestionnaire de Stock</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-primary: #e85d04;
            --color-secondary: #dc2f02;
            --color-accent: #f48c06;
            --color-dark: #03071e;
            --color-gray: #370617;
            --color-light: #faa307;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #03071e 0%, #370617 50%, #6a040f 100%);
            padding: 20px;
            position: relative;
            overflow: hidden;
        }
        
        body::before {
            content: '';
            position: absolute;
            width: 150%;
            height: 150%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(232, 93, 4, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(220, 47, 2, 0.15) 0%, transparent 50%);
            animation: drift 30s ease-in-out infinite alternate;
        }
        
        @keyframes drift {
            0% { transform: translate(-2%, -2%) rotate(0deg); }
            100% { transform: translate(2%, 2%) rotate(5deg); }
        }
        
        .container {
            position: relative;
            max-width: 900px;
            width: 100%;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 
                0 30px 90px rgba(0, 0, 0, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            overflow: hidden;
            animation: fadeIn 0.8s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .form-wrapper {
            display: grid;
            grid-template-columns: 1fr 1fr;
            min-height: 600px;
        }
        
        .form-section {
            padding: 50px 40px;
            display: flex;
            flex-direction: column;
            transition: all 0.4s ease;
        }
        
        .form-section.login {
            background: linear-gradient(135deg, rgba(232, 93, 4, 0.1) 0%, rgba(220, 47, 2, 0.05) 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .form-section.register {
            background: linear-gradient(135deg, rgba(220, 47, 2, 0.05) 0%, rgba(232, 93, 4, 0.1) 100%);
        }
        
        h1 {
            font-family: 'DM Serif Display', serif;
            font-size: 42px;
            color: var(--color-light);
            margin-bottom: 10px;
            font-weight: 400;
            letter-spacing: -1px;
        }
        
        .subtitle {
            color: rgba(255, 255, 255, 0.6);
            font-size: 16px;
            margin-bottom: 35px;
            font-weight: 300;
        }
        
        .input-group {
            margin-bottom: 20px;
            animation: slideUp 0.5s ease-out backwards;
        }
        
        .input-group:nth-child(2) { animation-delay: 0.1s; }
        .input-group:nth-child(3) { animation-delay: 0.2s; }
        .input-group:nth-child(4) { animation-delay: 0.3s; }
        .input-group:nth-child(5) { animation-delay: 0.4s; }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        label {
            display: block;
            color: rgba(255, 255, 255, 0.8);
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: white;
            font-size: 15px;
            font-family: 'Outfit', sans-serif;
            transition: all 0.3s ease;
        }
        
        input:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--color-accent);
            box-shadow: 0 0 0 3px rgba(244, 140, 6, 0.1);
        }
        
        input::placeholder {
            color: rgba(255, 255, 255, 0.3);
        }
        
        .password-strength {
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }
        
        .password-strength-bar {
            height: 100%;
            width: 0%;
            transition: all 0.3s ease;
            border-radius: 2px;
        }
        
        .strength-text {
            font-size: 12px;
            margin-top: 6px;
            color: rgba(255, 255, 255, 0.6);
            font-weight: 500;
        }
        
        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 25px;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }
        
        button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s ease;
        }
        
        button:hover::before {
            left: 100%;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(232, 93, 4, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .message {
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
            font-weight: 500;
            animation: shake 0.5s ease;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }
        
        .error-message {
            background: rgba(220, 47, 2, 0.2);
            border: 1px solid rgba(220, 47, 2, 0.4);
            color: #ffccd5;
        }
        
        .success-message {
            background: rgba(102, 187, 106, 0.2);
            border: 1px solid rgba(102, 187, 106, 0.4);
            color: #c8e6c9;
        }
        
        @media (max-width: 768px) {
            .form-wrapper {
                grid-template-columns: 1fr;
            }
            
            .form-section.login {
                border-right: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            h1 {
                font-size: 32px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-wrapper">
            <div class="form-section login">
                <h1>Connexion</h1>
                <p class="subtitle">Accédez à votre espace</p>
                
                {% if login_error %}
                <div class="message error-message">{{ login_error }}</div>
                {% endif %}
                {% if success %}
                <div class="message success-message">{{ success }}</div>
                {% endif %}
                
                <form method="POST" action="/login">
                    <div class="input-group">
                        <label for="login-email">Email</label>
                        <input type="email" id="login-email" name="email" placeholder="votre@email.com" required>
                    </div>
                    
                    <div class="input-group">
                        <label for="login-password">Mot de passe</label>
                        <input type="password" id="login-password" name="password" placeholder="••••••••" required>
                    </div>
                    
                    <button type="submit">Se connecter</button>
                </form>
            </div>
            
            <div class="form-section register">
                <h1>Inscription</h1>
                <p class="subtitle">Créez votre compte</p>
                
                {% if register_error %}
                <div class="message error-message">{{ register_error }}</div>
                {% endif %}
                
                <form method="POST" action="/register" onsubmit="return validateSignup()">
                    <div class="input-group">
                        <label for="signup-nom">Nom complet</label>
                        <input type="text" id="signup-nom" name="nom" placeholder="Jean Dupont" required>
                    </div>
                    
                    <div class="input-group">
                        <label for="signup-email">Email</label>
                        <input type="email" id="signup-email" name="email" placeholder="jean@exemple.com" required>
                    </div>
                    
                    <div class="input-group">
                        <label for="signup-entreprise">Entreprise</label>
                        <input type="text" id="signup-entreprise" name="nom_entreprise" placeholder="Ma Société" required>
                    </div>
                    
                    <div class="input-group">
                        <label for="signup-password">Mot de passe</label>
                        <input type="password" id="signup-password" name="password" placeholder="••••••••" required onkeyup="checkPasswordStrength()">
                        <div class="password-strength">
                            <div class="password-strength-bar" id="strength-bar"></div>
                        </div>
                        <div class="strength-text" id="strength-text"></div>
                    </div>
                    
                    <div class="input-group">
                        <label for="signup-confirm">Confirmer le mot de passe</label>
                        <input type="password" id="signup-confirm" name="confirm_password" placeholder="••••••••" required>
                    </div>
                    
                    <button type="submit">Créer mon compte</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function checkPasswordStrength() {
            const password = document.getElementById('signup-password').value;
            const strengthBar = document.getElementById('strength-bar');
            const strengthText = document.getElementById('strength-text');
            
            let strength = 0;
            let text = '';
            let color = '';
            
            if (password.length === 0) {
                strengthBar.style.width = '0%';
                strengthText.textContent = '';
                return;
            }
            
            if (password.length >= 8) strength += 25;
            if (password.length >= 12) strength += 10;
            if (/[a-z]/.test(password)) strength += 15;
            if (/[A-Z]/.test(password)) strength += 15;
            if (/[0-9]/.test(password)) strength += 15;
            if (/[^a-zA-Z0-9]/.test(password)) strength += 20;
            
            if (strength < 30) {
                text = 'Très faible';
                color = '#dc2f02';
            } else if (strength < 50) {
                text = 'Faible';
                color = '#e85d04';
            } else if (strength < 70) {
                text = 'Moyen';
                color = '#f48c06';
            } else if (strength < 90) {
                text = 'Bon';
                color = '#faa307';
            } else {
                text = 'Excellent';
                color = '#66bb6a';
            }
            
            strengthBar.style.width = strength + '%';
            strengthBar.style.backgroundColor = color;
            strengthText.textContent = text;
            strengthText.style.color = color;
        }
        
        function validateSignup() {
            const password = document.getElementById('signup-password').value;
            const confirm = document.getElementById('signup-confirm').value;
            
            if (password !== confirm) {
                alert('Les mots de passe ne correspondent pas !');
                return false;
            }
            
            if (password.length < 8) {
                alert('Le mot de passe doit contenir au moins 8 caractères !');
                return false;
            }
            
            return true;
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
    <title>Dashboard - {{ user.nom_entreprise }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-primary: #e85d04;
            --color-secondary: #dc2f02;
            --color-accent: #f48c06;
            --color-dark: #03071e;
            --color-gray: #370617;
            --color-light: #faa307;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, #03071e 0%, #370617 50%, #6a040f 100%);
            min-height: 100vh;
            color: white;
        }
        
        .navbar {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            font-family: 'DM Serif Display', serif;
            font-size: 28px;
            color: var(--color-light);
            font-weight: 400;
        }
        
        .user-section {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .user-name {
            color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
        }
        
        .logout-btn {
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: white;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .logout-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
        }
        
        .header {
            margin-bottom: 40px;
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .header h1 {
            font-family: 'DM Serif Display', serif;
            font-size: 48px;
            margin-bottom: 10px;
            font-weight: 400;
        }
        
        .header p {
            color: rgba(255, 255, 255, 0.6);
            font-size: 18px;
        }
        
        .actions {
            display: flex;
            gap: 15px;
            margin-bottom: 40px;
            animation: fadeInUp 0.6s ease-out 0.1s backwards;
        }
        
        .btn {
            padding: 14px 28px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-block;
            border: none;
            cursor: pointer;
            font-size: 15px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(232, 93, 4, 0.4);
        }
        
        .btn-outline {
            background: transparent;
            border: 2px solid rgba(255, 255, 255, 0.2);
            color: white;
        }
        
        .btn-outline:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--color-accent);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: fadeInUp 0.6s ease-out backwards;
        }
        
        .stat-card:nth-child(1) { animation-delay: 0.2s; }
        .stat-card:nth-child(2) { animation-delay: 0.3s; }
        .stat-card:nth-child(3) { animation-delay: 0.4s; }
        
        .stat-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--color-accent);
        }
        
        .stat-label {
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        .stat-value {
            font-size: 48px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--color-light) 0%, var(--color-accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
        }
        
        .products-section {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 35px;
            animation: fadeInUp 0.6s ease-out 0.5s backwards;
        }
        
        .section-title {
            font-family: 'DM Serif Display', serif;
            font-size: 32px;
            margin-bottom: 25px;
            font-weight: 400;
        }
        
        .products-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 10px;
        }
        
        .products-table thead th {
            text-align: left;
            padding: 15px 20px;
            color: rgba(255, 255, 255, 0.6);
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .products-table tbody tr {
            background: rgba(255, 255, 255, 0.03);
            transition: all 0.3s ease;
        }
        
        .products-table tbody tr:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: scale(1.02);
        }
        
        .products-table tbody td {
            padding: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .products-table tbody td:first-child {
            border-left: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px 0 0 12px;
        }
        
        .products-table tbody td:last-child {
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 0 12px 12px 0;
        }
        
        .product-image {
            width: 60px;
            height: 60px;
            object-fit: cover;
            border-radius: 12px;
            border: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .product-image-placeholder {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 24px;
        }
        
        .empty-state {
            text-align: center;
            padding: 80px 20px;
            color: rgba(255, 255, 255, 0.4);
        }
        
        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
        
        .empty-state h3 {
            font-size: 24px;
            margin-bottom: 10px;
            color: rgba(255, 255, 255, 0.6);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 32px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .products-table {
                font-size: 14px;
            }
            
            .navbar {
                padding: 15px 20px;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">{{ user.nom_entreprise }}</div>
        <div class="user-section">
            <span class="user-name">{{ user.nom }}</span>
            <a href="{{ url_for('logout') }}" class="logout-btn">Déconnexion</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="header">
            <h1>Tableau de bord</h1>
            <p>Vue d'ensemble de votre inventaire</p>
        </div>
        
        <div class="actions">
            <a href="{{ url_for('product_add') }}" class="btn btn-primary">+ Créer un produit</a>
            <a href="{{ url_for('product_list') }}" class="btn btn-outline">Voir tous les produits</a>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Produits</div>
                <div class="stat-value">{{ products|length }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Stock Total</div>
                <div class="stat-value">{{ total_quantity }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Valeur Stock</div>
                <div class="stat-value">{{ "%.0f"|format(total_value) }}€</div>
            </div>
        </div>
        
        <div class="products-section">
            <h2 class="section-title">Derniers produits</h2>
            {% if products %}
            <table class="products-table">
                <thead>
                    <tr>
                        <th>Image</th>
                        <th>Nom</th>
                        <th>Description</th>
                        <th>Prix</th>
                        <th>Quantité</th>
                    </tr>
                </thead>
                <tbody>
                    {% for product in products[:5] %}
                    <tr>
                        <td>
                            {% if product.image_url %}
                                <img src="{{ product.image_url }}" alt="{{ product.nom }}" class="product-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                <div class="product-image-placeholder" style="display:none;">
                                    {{ product.nom[0]|upper }}
                                </div>
                            {% else %}
                                <div class="product-image-placeholder">
                                    {{ product.nom[0]|upper }}
                                </div>
                            {% endif %}
                        </td>
                        <td><strong>{{ product.nom }}</strong></td>
                        <td>{{ product.description }}</td>
                        <td><strong>{{ product.prix }}€</strong></td>
                        <td>{{ product.quantite }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                </svg>
                <h3>Aucun produit</h3>
                <p>Commencez par créer votre premier produit</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

PRODUCT_LIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Produits - {{ user.nom_entreprise }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-primary: #e85d04;
            --color-secondary: #dc2f02;
            --color-accent: #f48c06;
            --color-dark: #03071e;
            --color-gray: #370617;
            --color-light: #faa307;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, #03071e 0%, #370617 50%, #6a040f 100%);
            min-height: 100vh;
            color: white;
        }
        
        .navbar {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            font-family: 'DM Serif Display', serif;
            font-size: 28px;
            color: var(--color-light);
            font-weight: 400;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .nav-links a {
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .nav-links a.active,
        .nav-links a:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .header h1 {
            font-family: 'DM Serif Display', serif;
            font-size: 48px;
            font-weight: 400;
        }
        
        .search-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            animation: fadeInUp 0.6s ease-out 0.1s backwards;
        }
        
        .search-bar input {
            flex: 1;
            padding: 14px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: white;
            font-family: 'Outfit', sans-serif;
            font-size: 15px;
            transition: all 0.3s ease;
        }
        
        .search-bar input:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--color-accent);
        }
        
        .search-bar input::placeholder {
            color: rgba(255, 255, 255, 0.3);
        }
        
        .btn {
            padding: 14px 28px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-block;
            border: none;
            cursor: pointer;
            font-size: 15px;
            font-family: 'Outfit', sans-serif;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(232, 93, 4, 0.4);
        }
        
        .btn-outline {
            background: transparent;
            border: 2px solid rgba(255, 255, 255, 0.2);
            color: white;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .product-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: fadeInUp 0.6s ease-out backwards;
        }
        
        .product-card:hover {
            transform: translateY(-10px);
            border-color: var(--color-accent);
        }
        
        .product-image-container {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        
        .product-image-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .product-placeholder {
            font-size: 64px;
            font-weight: 700;
            color: white;
        }
        
        .product-content {
            padding: 25px;
        }
        
        .product-name {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .product-description {
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
            margin-bottom: 15px;
            line-height: 1.6;
        }
        
        .product-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .product-price {
            font-size: 24px;
            font-weight: 700;
            color: var(--color-light);
        }
        
        .product-quantity {
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
        }
        
        .product-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .btn-small {
            padding: 8px 16px;
            font-size: 13px;
            border-radius: 8px;
        }
        
        .btn-danger {
            background: rgba(220, 47, 2, 0.2);
            border: 1px solid rgba(220, 47, 2, 0.4);
            color: #ffccd5;
        }
        
        .btn-danger:hover {
            background: rgba(220, 47, 2, 0.3);
            transform: translateY(-2px);
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin-top: 40px;
        }
        
        .pagination a {
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: white;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .pagination a:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
        }
        
        .pagination .current {
            color: rgba(255, 255, 255, 0.6);
        }
        
        .empty-state {
            text-align: center;
            padding: 100px 20px;
            color: rgba(255, 255, 255, 0.4);
        }
        
        .empty-state h3 {
            font-size: 28px;
            margin-bottom: 15px;
            color: rgba(255, 255, 255, 0.6);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 32px;
            }
            
            .products-grid {
                grid-template-columns: 1fr;
            }
            
            .navbar {
                padding: 15px 20px;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">{{ user.nom_entreprise }}</div>
        <div class="nav-links">
            <a href="{{ url_for('dashboard') }}">Dashboard</a>
            <a href="{{ url_for('product_list') }}" class="active">Produits</a>
            <a href="{{ url_for('logout') }}">Déconnexion</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="header">
            <h1>Mes Produits</h1>
            <a href="{{ url_for('product_add') }}" class="btn btn-primary">+ Ajouter un produit</a>
        </div>
        
        <form method="get" class="search-bar">
            <input type="text" name="q" placeholder="Rechercher un produit..." value="{{ q or '' }}">
            <button type="submit" class="btn btn-outline">Rechercher</button>
        </form>
        
        {% if products %}
        <div class="products-grid">
            {% for p in products %}
            <div class="product-card">
                <div class="product-image-container">
                    {% if p.image_url %}
                        <img src="{{ p.image_url }}" alt="{{ p.nom }}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <div class="product-placeholder" style="display:none;">
                            {{ p.nom[0]|upper }}
                        </div>
                    {% else %}
                        <div class="product-placeholder">
                            {{ p.nom[0]|upper }}
                        </div>
                    {% endif %}
                </div>
                <div class="product-content">
                    <h3 class="product-name">{{ p.nom }}</h3>
                    <p class="product-description">{{ p.description if p.description else 'Aucune description' }}</p>
                    <div class="product-footer">
                        <div class="product-price">{{ p.prix }}€</div>
                        <div class="product-quantity">Stock: {{ p.quantite }}</div>
                    </div>
                    <div class="product-actions">
                        <a href="{{ url_for('product_edit', product_id=p.id) }}" class="btn btn-outline btn-small">Modifier</a>
                        <form method="post" action="{{ url_for('product_delete', product_id=p.id) }}" onsubmit="return confirm('Supprimer ce produit ?');" style="display: inline;">
                            <button type="submit" class="btn btn-danger btn-small">Supprimer</button>
                        </form>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="pagination">
            {% if page > 1 %}
                <a href="{{ url_for('product_list', page=page-1, q=q) }}">&larr; Précédent</a>
            {% endif %}
            <span class="current">Page {{ page }} / {{ total_pages }}</span>
            {% if page < total_pages %}
                <a href="{{ url_for('product_list', page=page+1, q=q) }}">Suivant &rarr;</a>
            {% endif %}
        </div>
        {% else %}
        <div class="empty-state">
            <h3>Aucun produit trouvé</h3>
            <p>Créez votre premier produit pour commencer</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

PRODUCT_FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if product %}Modifier{% else %}Ajouter{% endif %} un produit - {{ user.nom_entreprise }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-primary: #e85d04;
            --color-secondary: #dc2f02;
            --color-accent: #f48c06;
            --color-dark: #03071e;
            --color-gray: #370617;
            --color-light: #faa307;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, #03071e 0%, #370617 50%, #6a040f 100%);
            min-height: 100vh;
            color: white;
        }
        
        .navbar {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            font-family: 'DM Serif Display', serif;
            font-size: 28px;
            color: var(--color-light);
            font-weight: 400;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .nav-links a {
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .nav-links a.active,
        .nav-links a:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
        }
        
        .form-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px;
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        h1 {
            font-family: 'DM Serif Display', serif;
            font-size: 42px;
            margin-bottom: 10px;
            font-weight: 400;
        }
        
        .subtitle {
            color: rgba(255, 255, 255, 0.6);
            margin-bottom: 35px;
            font-size: 16px;
        }
        
        .input-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            color: rgba(255, 255, 255, 0.8);
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        input[type="text"],
        input[type="number"],
        input[type="url"] {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: white;
            font-size: 15px;
            font-family: 'Outfit', sans-serif;
            transition: all 0.3s ease;
        }
        
        input:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--color-accent);
            box-shadow: 0 0 0 3px rgba(244, 140, 6, 0.1);
        }
        
        input::placeholder {
            color: rgba(255, 255, 255, 0.3);
        }
        
        .help-text {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 6px;
        }
        
        .image-preview {
            margin-top: 15px;
            max-width: 300px;
            max-height: 300px;
            border-radius: 16px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            display: none;
            object-fit: cover;
        }
        
        .form-actions {
            display: flex;
            gap: 15px;
            margin-top: 35px;
        }
        
        .btn {
            padding: 14px 28px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-block;
            border: none;
            cursor: pointer;
            font-size: 15px;
            font-family: 'Outfit', sans-serif;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
            color: white;
            flex: 1;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(232, 93, 4, 0.4);
        }
        
        .btn-outline {
            background: transparent;
            border: 2px solid rgba(255, 255, 255, 0.2);
            color: white;
        }
        
        .btn-outline:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 32px;
            }
            
            .form-card {
                padding: 25px;
            }
            
            .navbar {
                padding: 15px 20px;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">{{ user.nom_entreprise }}</div>
        <div class="nav-links">
            <a href="{{ url_for('dashboard') }}">Dashboard</a>
            <a href="{{ url_for('product_list') }}" class="active">Produits</a>
            <a href="{{ url_for('logout') }}">Déconnexion</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="form-card">
            <h1>{% if product %}Modifier{% else %}Nouveau{% endif %} Produit</h1>
            <p class="subtitle">{% if product %}Modifiez les informations de votre produit{% else %}Ajoutez un nouveau produit à votre inventaire{% endif %}</p>
            
            <form method="post">
                <div class="input-group">
                    <label for="nom">Nom du produit *</label>
                    <input type="text" id="nom" name="nom" value="{{ product.nom if product else '' }}" placeholder="Ex: MacBook Pro 16 pouces" required>
                </div>
                
                <div class="input-group">
                    <label for="description">Description</label>
                    <input type="text" id="description" name="description" value="{{ product.description if product else '' }}" placeholder="Décrivez votre produit...">
                </div>
                
                <div class="input-group">
                    <label for="image_url">URL de l'image</label>
                    <input type="url" id="image_url" name="image_url" value="{{ product.image_url if product else '' }}" 
                           placeholder="https://exemple.com/image.jpg" oninput="previewImage()">
                    <div class="help-text">Collez l'URL d'une image (Unsplash, Imgur, etc.)</div>
                    <img id="preview" class="image-preview" alt="Aperçu">
                </div>
                
                <div class="input-group">
                    <label for="prix">Prix (€) *</label>
                    <input type="number" step="0.01" id="prix" name="prix" value="{{ product.prix if product else '0.00' }}" placeholder="0.00" required>
                </div>
                
                <div class="input-group">
                    <label for="quantite">Quantité en stock *</label>
                    <input type="number" id="quantite" name="quantite" value="{{ product.quantite if product else '0' }}" placeholder="0" required>
                </div>
                
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">{% if product %}Enregistrer les modifications{% else %}Créer le produit{% endif %}</button>
                    <a href="{{ url_for('product_list') }}" class="btn btn-outline">Annuler</a>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function previewImage() {
            const url = document.getElementById('image_url').value;
            const preview = document.getElementById('preview');
            
            if (url) {
                preview.src = url;
                preview.style.display = 'block';
                preview.onerror = function() {
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
        # Vérifier si c'est un nouvel utilisateur ou ancien
        if 'id_entreprise' in user and user['id_entreprise']:
            # Nouveau format avec id_entreprise
            entreprise = get_entreprise_by_id(user['id_entreprise'])
            session['id_entreprise'] = user['id_entreprise']
            session['nom_entreprise'] = entreprise['nom'] if entreprise else 'Entreprise inconnue'
        else:
            # Ancien format - créer l'entreprise
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

    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': session['nom_entreprise'],
        'id_entreprise': session['id_entreprise']
    }

    all_products = get_products_by_entreprise(user['id_entreprise'])

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

    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': session['nom_entreprise'],
        'id_entreprise': session['id_entreprise']
    }

    if request.method == 'POST':
        nom = request.form['nom']
        description = request.form.get('description', '')
        prix = request.form['prix']
        quantite = request.form['quantite']
        image_url = request.form.get('image_url', '')

        add_product(nom, description, prix, quantite, user['id_entreprise'], image_url)
        return redirect(url_for('product_list'))

    return render_template_string(PRODUCT_FORM_TEMPLATE, user=user, product=None)


@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': session['nom_entreprise'],
        'id_entreprise': session['id_entreprise']
    }

    product = get_product_by_id(product_id, user['id_entreprise'])
    if not product:
        return "Produit introuvable ou non autorisé", 404

    if request.method == 'POST':
        nom = request.form['nom']
        description = request.form.get('description', '')
        prix = request.form['prix']
        quantite = request.form['quantite']
        image_url = request.form.get('image_url', '')

        update_product(product_id, user['id_entreprise'], nom, description, prix, quantite, image_url)
        return redirect(url_for('product_list'))

    return render_template_string(PRODUCT_FORM_TEMPLATE, user=user, product=product)


@app.route('/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    entreprise_id = session['id_entreprise']
    delete_product(product_id, entreprise_id)
    return redirect(url_for('product_list'))


# ---------- Lancement Webview / dev ----------

def start_app():
    init_csv_files()
    window = webview.create_window('Gestion de Produits', app, width=1200, height=800)
    webview.start()


if __name__ == '__main__':
    init_csv_files()
    app.run(debug=False)
    start_app()