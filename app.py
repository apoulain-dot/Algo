import csv
import os
import hashlib
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import webview
import bcrypt

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_a_changer'

# Chemins des fichiers CSV
USERS_FILE = './data/users.csv'
PRODUCTS_FILE = './data/products.csv'

# Initialisation des fichiers CSV
def init_csv_files():
    os.makedirs('./data', exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nom', 'email', 'mdp', 'role', 'created_at', 'nom_entreprise'])
    
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'nom', 'description', 'prix', 'quantite', 'id_entreprise'])

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
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['email'] == email:
                return row
    return None

def create_user(nom, email, password, nom_entreprise):
    user_id = get_next_id(USERS_FILE)
    hashed_pwd = hash_password(password)
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(USERS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([user_id, nom, email, hashed_pwd, 'user', created_at, nom_entreprise])
    return user_id

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

# Template HTML avec la nouvelle interface
AUTH_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Gestion de Produits - Authentification</title>
    <link href="https://fonts.googleapis.com/css2?family=Jost:wght@500&display=swap" rel="stylesheet">
    <style>
        body{
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: 'Jost', sans-serif;
            background: linear-gradient(to bottom, #0f0c29, #302b63, #24243e);
        }
        .main{
            width: 400px;
            height: 650px;
            background: red;
            overflow: hidden;
            background: url("https://doc-08-2c-docs.googleusercontent.com/docs/securesc/68c90smiglihng9534mvqmq1946dmis5/fo0picsp1nhiucmc0l25s29respgpr4j/1631524275000/03522360960922298374/03522360960922298374/1Sx0jhdpEpnNIydS4rnN4kHSJtU1EyWka?e=view&authuser=0&nonce=gcrocepgbb17m&user=03522360960922298374&hash=tfhgbs86ka6divo3llbvp93mg4csvb38") no-repeat center/ cover;
            border-radius: 10px;
            box-shadow: 5px 20px 50px #000;
        }
        #chk{
            display: none;
        }
        .signup{
            position: relative;
            width:100%;
            height: 100%;
        }
        label{
            color: #fff;
            font-size: 2.3em;
            justify-content: center;
            display: flex;
            margin: 40px;
            font-weight: bold;
            cursor: pointer;
            transition: .5s ease-in-out;
        }
        input{
            width: 60%;
            height: 10px;
            background: #e0dede;
            justify-content: center;
            display: flex;
            margin: 15px auto;
            padding: 12px;
            border: none;
            outline: none;
            border-radius: 5px;
            font-size: 14px;
        }
        button{
            width: 60%;
            height: 40px;
            margin: 10px auto;
            justify-content: center;
            display: block;
            color: #fff;
            background: #573b8a;
            font-size: 1em;
            font-weight: bold;
            margin-top: 20px;
            outline: none;
            border: none;
            border-radius: 5px;
            transition: .2s ease-in;
            cursor: pointer;
        }
        button:hover{
            background: #6d44b8;
        }
        .login{
            height: 460px;
            background: #eee;
            border-radius: 60% / 10%;
            transform: translateY(-180px);
            transition: .8s ease-in-out;
        }
        .login label{
            color: #573b8a;
            transform: scale(.6);
        }
        #chk:checked ~ .login{
            transform: translateY(-600px);
        }
        #chk:checked ~ .login label{
            transform: scale(1);	
        }
        #chk:checked ~ .signup label{
            transform: scale(.6);
        }
        .error-message{
            color: #ff4444;
            text-align: center;
            margin: 10px;
            font-size: 14px;
            background: rgba(255,255,255,0.9);
            padding: 8px;
            border-radius: 5px;
        }
        .success-message{
            color: #44ff44;
            text-align: center;
            margin: 10px;
            font-size: 14px;
            background: rgba(255,255,255,0.9);
            padding: 8px;
            border-radius: 5px;
        }
        .password-strength {
            width: 60%;
            margin: 5px auto 15px;
            height: 5px;
            background: #ddd;
            border-radius: 3px;
            overflow: hidden;
        }
        .password-strength-bar {
            height: 100%;
            width: 0%;
            transition: all 0.3s ease;
            border-radius: 3px;
        }
        .strength-text {
            text-align: center;
            font-size: 12px;
            margin-top: 5px;
            color: #fff;
        }
        .signup .strength-text {
            color: #fff;
        }
        .login .strength-text {
            color: #573b8a;
        }
    </style>
</head>
<body>
    <div class="main">  	
        <input type="checkbox" id="chk" aria-hidden="true">
        
        <div class="signup">
            <form method="POST" action="/register" onsubmit="return validateSignup()">
                <label for="chk" aria-hidden="true">Sign up</label>
                {% if register_error %}
                <div class="error-message">{{ register_error }}</div>
                {% endif %}
                <input type="text" name="nom" id="signup-nom" placeholder="Nom complet" required>
                <input type="email" name="email" id="signup-email" placeholder="Email" required>
                <input type="text" name="nom_entreprise" id="signup-entreprise" placeholder="Nom de l'entreprise" required>
                <input type="password" name="password" id="signup-password" placeholder="Mot de passe" required onkeyup="checkPasswordStrength()">
                <div class="password-strength">
                    <div class="password-strength-bar" id="strength-bar"></div>
                </div>
                <div class="strength-text" id="strength-text"></div>
                <input type="password" name="confirm_password" id="signup-confirm" placeholder="Confirmer le mot de passe" required>
                <button type="submit">Sign up</button>
            </form>
        </div>
        
        <div class="login">
            <form method="POST" action="/login">
                <label for="chk" aria-hidden="true">Login</label>
                {% if login_error %}
                <div class="error-message">{{ login_error }}</div>
                {% endif %}
                {% if success %}
                <div class="success-message">{{ success }}</div>
                {% endif %}
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
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
            
            // Critères de force
            if (password.length >= 8) strength += 25;
            if (password.length >= 12) strength += 10;
            if (/[a-z]/.test(password)) strength += 15;
            if (/[A-Z]/.test(password)) strength += 15;
            if (/[0-9]/.test(password)) strength += 15;
            if (/[^a-zA-Z0-9]/.test(password)) strength += 20;
            
            // Définir le texte et la couleur
            if (strength < 30) {
                text = 'Très faible';
                color = '#ff4444';
            } else if (strength < 50) {
                text = 'Faible';
                color = '#ff8844';
            } else if (strength < 70) {
                text = 'Moyen';
                color = '#ffbb44';
            } else if (strength < 90) {
                text = 'Bon';
                color = '#88cc44';
            } else {
                text = 'Excellent';
                color = '#44cc44';
            }
            
            strengthBar.style.width = strength + '%';
            strengthBar.style.backgroundColor = color;
            strengthText.textContent = text;
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
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(to bottom, #0f0c29, #302b63, #24243e);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 24px; }
        .header .user-info {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        .logout-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
        }
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .products-section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .products-section h2 {
            margin-bottom: 20px;
            color: #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f9f9f9;
            font-weight: 600;
            color: #666;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state h3 {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📦 {{ user.nom_entreprise }}</h1>
        <div class="user-info">
            <span>Bonjour, {{ user.nom }}</span>
            <a href="{{ url_for('logout') }}" class="logout-btn">Déconnexion</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h3>Total Produits</h3>
                <div class="value">{{ products|length }}</div>
            </div>
            <div class="stat-card">
                <h3>Stock Total</h3>
                <div class="value">{{ total_quantity }}</div>
            </div>
            <div class="stat-card">
                <h3>Valeur Stock</h3>
                <div class="value">{{ "%.2f"|format(total_value) }} €</div>
            </div>
        </div>
        
        <div class="products-section">
            <h2>Vos Produits</h2>
            {% if products %}
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nom</th>
                        <th>Description</th>
                        <th>Prix</th>
                        <th>Quantité</th>
                    </tr>
                </thead>
                <tbody>
                    {% for product in products %}
                    <tr>
                        <td>{{ product.id }}</td>
                        <td>{{ product.nom }}</td>
                        <td>{{ product.description }}</td>
                        <td>{{ product.prix }} €</td>
                        <td>{{ product.quantite }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <h3>Aucun produit</h3>
                <p>Vous n'avez pas encore de produits dans votre stock.</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

# Routes
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
        session['user_id'] = user['id']
        session['user_nom'] = user['nom']
        session['nom_entreprise'] = user['nom_entreprise']
        return redirect(url_for('dashboard'))
    else:
        return render_template_string(AUTH_TEMPLATE, login_error='Email ou mot de passe incorrect', 
                                       register_error=None, success=None)

@app.route('/register', methods=['POST'])
def register():
    nom = request.form['nom']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    nom_entreprise = request.form['nom_entreprise']
    
    # Validation
    if password != confirm_password:
        return render_template_string(AUTH_TEMPLATE, register_error='Les mots de passe ne correspondent pas', 
                                       login_error=None, success=None)
    
    if len(password) < 8:
        return render_template_string(AUTH_TEMPLATE, register_error='Le mot de passe doit contenir au moins 8 caractères', 
                                       login_error=None, success=None)
    
    if get_user_by_email(email):
        return render_template_string(AUTH_TEMPLATE, register_error='Cet email est déjà utilisé', 
                                       login_error=None, success=None)
    
    create_user(nom, email, password, nom_entreprise)
    return render_template_string(AUTH_TEMPLATE, success='Inscription réussie ! Vous pouvez maintenant vous connecter.', 
                                   login_error=None, register_error=None)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user = {
        'id': session['user_id'],
        'nom': session['user_nom'],
        'nom_entreprise': session['nom_entreprise']
    }
    
    products = get_products_by_entreprise(user['id'])
    
    total_quantity = sum(int(p['quantite']) for p in products) if products else 0
    total_value = sum(float(p['prix']) * int(p['quantite']) for p in products) if products else 0
    
    return render_template_string(DASHBOARD_TEMPLATE, user=user, products=products, 
                                   total_quantity=total_quantity, total_value=total_value)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Fonction principale pour lancer l'app avec Webview
def start_app():
    init_csv_files()
    window = webview.create_window('Gestion de Produits', app, width=1200, height=800)
    webview.start()

if __name__ == '__main__':
    # Pour développement : lancer Flask directement
    # app.run(debug=True, port=5000)
    
    # Pour production : lancer avec Webview
    init_csv_files()
    start_app()