from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import urllib.parse

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

# Modelos do banco de dados
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)
    order = db.Column(db.Integer, default=0)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    is_organic = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WeeklyList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.Date, nullable=False)
    week_end = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('WeeklyProduct', backref='weekly_list', lazy=True)

class WeeklyProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weekly_list_id = db.Column(db.Integer, db.ForeignKey('weekly_list.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref='weekly_products')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(20))
    delivery_address = db.Column(db.String(500))
    delivery_fee = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    weekly_list_id = db.Column(db.Integer, db.ForeignKey('weekly_list.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='order_items')

# Funções auxiliares
def init_db():
    try:
        db.create_all()
        
        # Criar admin padrão se não existir
        if not Admin.query.first():
            admin = Admin(username='mario', password_hash=generate_password_hash('3943'))
            db.session.add(admin)
        
        # Criar categorias padrão se não existirem
        if not Category.query.first():
            categories = [
                {'name': 'FOLHAS', 'emoji': '🥗', 'order': 1},
                {'name': 'RAÍZES & LEGUMES', 'emoji': '🥔', 'order': 2},
                {'name': 'FRUTAS', 'emoji': '🍎', 'order': 3},
                {'name': 'ORIGEM ANIMAL', 'emoji': '🐔', 'order': 4},
                {'name': 'COGUMELOS', 'emoji': '🍄', 'order': 5},
                {'name': 'TEMPEROS', 'emoji': '🌶️', 'order': 6},
            ]
            
            for cat_data in categories:
                category = Category(**cat_data)
                db.session.add(category)
        
        # Adicionar produtos de exemplo
        if not Product.query.first():
            sample_products = [
                {'name': 'Alface Americana', 'price': 5.00, 'unit': 'un', 'is_organic': True, 'category': 'FOLHAS'},
                {'name': 'Couve', 'price': 5.00, 'unit': 'un', 'is_organic': True, 'category': 'FOLHAS'},
                {'name': 'Rúcula', 'price': 6.00, 'unit': 'un', 'is_organic': True, 'category': 'FOLHAS'},
                {'name': 'Batata Doce', 'price': 7.00, 'unit': 'kg', 'is_organic': True, 'category': 'RAÍZES & LEGUMES'},
                {'name': 'Tomate', 'price': 6.20, 'unit': 'kg', 'is_organic': False, 'category': 'RAÍZES & LEGUMES'},
                {'name': 'Abobrinha', 'price': 6.00, 'unit': 'un', 'is_organic': True, 'category': 'RAÍZES & LEGUMES'},
                {'name': 'Banana Prata', 'price': 7.00, 'unit': 'palma', 'is_organic': True, 'category': 'FRUTAS'},
                {'name': 'Limão Tahiti', 'price': 6.50, 'unit': 'kg', 'is_organic': True, 'category': 'FRUTAS'},
                {'name': 'Ovos Caipira', 'price': 17.00, 'unit': 'dúzia', 'is_organic': False, 'category': 'ORIGEM ANIMAL'},
                {'name': 'Mel Silvestre', 'price': 40.00, 'unit': '400g', 'is_organic': True, 'category': 'ORIGEM ANIMAL'},
            ]
            
            for product_data in sample_products:
                category = Category.query.filter_by(name=product_data['category']).first()
                if category:
                    product = Product(
                        name=product_data['name'],
                        price=product_data['price'],
                        unit=product_data['unit'],
                        is_organic=product_data['is_organic'],
                        category_id=category.id
                    )
                    db.session.add(product)
        
        db.session.commit()
        print("✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        db.session.rollback()

def is_admin_logged_in():
    return 'admin_id' in session

# Rotas principais
@app.route('/')
def index():
    try:
        # Buscar lista ativa da semana
        active_list = WeeklyList.query.filter_by(is_active=True, is_closed=False).first()
        
        if not active_list:
            return render_template('no_list.html')
        
        # Buscar produtos da semana agrupados por categoria
        categories = db.session.query(Category).join(WeeklyProduct).join(Product).filter(
            WeeklyProduct.weekly_list_id == active_list.id,
            Product.is_active == True
        ).order_by(Category.order).all()
        
        products_by_category = {}
        for category in categories:
            products = db.session.query(Product).join(WeeklyProduct).filter(
                WeeklyProduct.weekly_list_id == active_list.id,
                Product.category_id == category.id,
                Product.is_active == True
            ).order_by(Product.name).all()
            products_by_category[category] = products
        
        return render_template('index.html', 
                             products_by_category=products_by_category,
                             weekly_list=active_list)
    except Exception as e:
        print(f"❌ Erro na página inicial: {e}")
        return render_template('no_list.html')

# API para salvar pedidos
@app.route('/api/save-order', methods=['POST'])
def save_order():
    try:
        data = request.get_json()
        
        # Buscar lista ativa
        active_list = WeeklyList.query.filter_by(is_active=True, is_closed=False).first()
        if not active_list:
            return jsonify({'success': False, 'message': 'Nenhuma lista ativa encontrada'})
        
        # Criar pedido
        order = Order(
            customer_name=data['customer_name'],
            customer_phone=data.get('customer_phone', ''),
            delivery_address=data.get('delivery_address', ''),
            delivery_fee=data['delivery_fee'],
            total_amount=data['total_amount'],
            weekly_list_id=active_list.id
        )
        db.session.add(order)
        db.session.flush()
        
        # Criar itens do pedido
        for product_id, item_data in data['items'].items():
            order_item = OrderItem(
                order_id=order.id,
                product_id=int(product_id),
                quantity=item_data['quantity'],
                unit_price=item_data['price'],
                total_price=item_data['total']
            )
            db.session.add(order_item)
        
        db.session.commit()
        return jsonify({'success': True, 'order_id': order.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Rotas administrativas
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    try:
        # Estatísticas gerais
        total_products = Product.query.filter_by(is_active=True).count()
        active_list = WeeklyList.query.filter_by(is_active=True).first()
        total_orders = Order.query.count()
        
        recent_orders = []
        if active_list:
            recent_orders = Order.query.filter_by(weekly_list_id=active_list.id).order_by(Order.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             total_products=total_products,
                             active_list=active_list,
                             total_orders=total_orders,
                             recent_orders=recent_orders)
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        return render_template('admin/dashboard.html',
                             total_products=0,
                             active_list=None,
                             total_orders=0,
                             recent_orders=[])

@app.route('/admin/products')
def admin_products():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    products = Product.query.join(Category).order_by(Category.order, Product.name).all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/weekly-lists/create', methods=['GET', 'POST'])
def admin_create_weekly_list():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            # Desativar lista anterior
            WeeklyList.query.filter_by(is_active=True).update({'is_active': False})
            
            # Criar nova lista
            week_start = datetime.strptime(request.form['week_start'], '%Y-%m-%d').date()
            week_end = datetime.strptime(request.form['week_end'], '%Y-%m-%d').date()
            
            weekly_list = WeeklyList(
                week_start=week_start,
                week_end=week_end,
                is_active=True
            )
            db.session.add(weekly_list)
            db.session.flush()
            
            # Adicionar produtos selecionados
            selected_products = request.form.getlist('products')
            for product_id in selected_products:
                weekly_product = WeeklyProduct(
                    weekly_list_id=weekly_list.id,
                    product_id=int(product_id)
                )
                db.session.add(weekly_product)
            
            db.session.commit()
            flash('Lista semanal criada com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar lista: {e}', 'error')
    
    # Buscar produtos por categoria
    categories = Category.query.order_by(Category.order).all()
    products_by_category = {}
    for category in categories:
        products = Product.query.filter_by(category_id=category.id, is_active=True).order_by(Product.name).all()
        if products:
            products_by_category[category] = products
    
    return render_template('admin/create_weekly_list.html', 
                         products_by_category=products_by_category)

@app.route('/admin/reports')
def admin_reports():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    
    # Relatório da semana atual
    active_list = WeeklyList.query.filter_by(is_active=True).first()
    
    weekly_report = None
    if active_list:
        # Produtos mais vendidos
        product_sales = db.session.query(
            Product.name,
            Product.unit,
            db.func.sum(OrderItem.quantity).label('total_quantity'),
            db.func.sum(OrderItem.total_price).label('total_revenue')
        ).join(OrderItem).join(Order).filter(
            Order.weekly_list_id == active_list.id
        ).group_by(Product.id).order_by(db.func.sum(OrderItem.quantity).desc()).all()
        
        # Total de pedidos e receita
        total_orders = Order.query.filter_by(weekly_list_id=active_list.id).count()
        total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.weekly_list_id == active_list.id
        ).scalar() or 0
        
        weekly_report = {
            'list': active_list,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'product_sales': product_sales
        }
    
    return render_template('admin/reports.html', weekly_report=weekly_report)

# Rota de saúde para Railway
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = not os.environ.get('RAILWAY_ENVIRONMENT')
    
    with app.app_context():
        init_db()
    
    app.run(debug=debug, host='0.0.0.0', port=port)
else:
    # Para Railway (quando executado via gunicorn)
    with app.app_context():
        init_db()
