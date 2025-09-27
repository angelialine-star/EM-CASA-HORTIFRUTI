from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'em-casa-hortifruti-railway-secret-key-2024')

# Configuração do banco de dados
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hortifruti.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelos básicos
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)
    order = db.Column(db.Integer, default=0)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    is_organic = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_db():
    try:
        db.create_all()
        if not Admin.query.first():
            admin = Admin(username='mario', password_hash=generate_password_hash('3943'))
            db.session.add(admin)
            db.session.commit()
        print("✅ Banco inicializado!")
    except Exception as e:
        print(f"❌ Erro: {e}")

@app.route('/')
def index():
    return '''
    <html>
    <head><title>Em Casa - Hortifruti</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🍃 Em Casa - Hortifruti Delivery</h1>
        <p>Sistema funcionando!</p>
        <a href="/admin/login">Área Administrativa</a>
    </body>
    </html>
    '''

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            return redirect('/admin/dashboard')
        else:
            return '''
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2>❌ Login incorreto!</h2>
                <a href="/admin/login">Tentar novamente</a>
            </body>
            </html>
            '''
    
    return '''
    <html>
    <head><title>Login Admin</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h2>🔐 Login Administrativo</h2>
        <form method="POST" style="display: inline-block;">
            <p><input type="text" name="username" placeholder="Usuário" required></p>
            <p><input type="password" name="password" placeholder="Senha" required></p>
            <p><button type="submit">Entrar</button></p>
        </form>
        <p><small>Usuário: mario | Senha: 3943</small></p>
    </body>
    </html>
    '''

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    return '''
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <h1>✅ Painel Administrativo Funcionando!</h1>
        <p>Login realizado com sucesso!</p>
        <p><a href="/admin/logout">Sair</a></p>
        <p><a href="/">Voltar para o site</a></p>
    </body>
    </html>
    '''

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect('/')

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    with app.app_context():
        init_db()
    app.run(debug=False, host='0.0.0.0', port=port)
else:
    with app.app_context():
        init_db()
