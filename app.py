from flask import Flask, request, redirect, url_for, flash, session, jsonify
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
                {'name': 'Salsinha', 'price': 5.00, 'unit': 'maço', 'is_organic': True, 'category': 'FOLHAS'},
                {'name': 'Coentro', 'price': 5.00, 'unit': 'maço', 'is_organic': True, 'category': 'FOLHAS'},
                {'name': 'Batata Doce', 'price': 7.00, 'unit': 'kg', 'is_organic': True, 'category': 'RAÍZES & LEGUMES'},
                {'name': 'Tomate', 'price': 6.20, 'unit': 'kg', 'is_organic': False, 'category': 'RAÍZES & LEGUMES'},
                {'name': 'Abobrinha', 'price': 6.00, 'unit': 'un', 'is_organic': True, 'category': 'RAÍZES & LEGUMES'},
                {'name': 'Berinjela', 'price': 4.00, 'unit': 'un', 'is_organic': True, 'category': 'RAÍZES & LEGUMES'},
                {'name': 'Pepino', 'price': 4.00, 'unit': 'un', 'is_organic': True, 'category': 'RAÍZES & LEGUMES'},
                {'name': 'Banana Prata', 'price': 7.00, 'unit': 'palma', 'is_organic': True, 'category': 'FRUTAS'},
                {'name': 'Limão Tahiti', 'price': 6.50, 'unit': 'kg', 'is_organic': True, 'category': 'FRUTAS'},
                {'name': 'Laranja Pera', 'price': 7.20, 'unit': 'kg', 'is_organic': True, 'category': 'FRUTAS'},
                {'name': 'Ovos Caipira', 'price': 17.00, 'unit': 'dúzia', 'is_organic': False, 'category': 'ORIGEM ANIMAL'},
                {'name': 'Mel Silvestre', 'price': 40.00, 'unit': '400g', 'is_organic': True, 'category': 'ORIGEM ANIMAL'},
                {'name': 'Pimenta de Cheiro', 'price': 6.00, 'unit': '100g', 'is_organic': False, 'category': 'TEMPEROS'},
                {'name': 'Orégano', 'price': 8.00, 'unit': '100g', 'is_organic': False, 'category': 'TEMPEROS'},
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

# Templates HTML embutidos
def get_base_style():
    return """
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .btn { padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; margin: 5px; display: inline-block; }
        .btn:hover { background: #218838; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .form-group { margin-bottom: 15px; }
        .form-control { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .product-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: white; }
        .category-header { background: #007bff; color: white; padding: 10px; margin: 20px 0 10px 0; border-radius: 5px; }
        .cart { position: fixed; bottom: 20px; right: 20px; background: #28a745; color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); max-width: 300px; }
        .quantity-input { width: 60px; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .nav { background: #343a40; padding: 10px 0; margin-bottom: 20px; }
        .nav a { color: white; text-decoration: none; padding: 10px 15px; margin: 0 5px; }
        .nav a:hover { background: #495057; border-radius: 5px; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: white; margin: 15% auto; padding: 20px; border-radius: 10px; width: 80%; max-width: 500px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
    </style>
    """

# Rotas principais
@app.route('/')
def index():
    try:
        # Buscar lista ativa da semana
        active_list = WeeklyList.query.filter_by(is_active=True, is_closed=False).first()
        
        if not active_list:
            return f"""
            <html>
            <head><title>Em Casa - Hortifruti</title>{get_base_style()}</head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🍃 Em Casa - Hortifruti Delivery</h1>
                        <p>Lista da semana não disponível no momento.</p>
                        <p>Entre em contato pelo WhatsApp: <strong>+55 (82) 99660-3943</strong></p>
                        <a href="/admin/login" class="btn">Área Administrativa</a>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Buscar produtos da semana - CONSULTA CORRIGIDA
        weekly_products = db.session.query(WeeklyProduct).filter_by(weekly_list_id=active_list.id).all()
        
        # Agrupar produtos por categoria
        products_by_category = {}
        for wp in weekly_products:
            product = wp.product
            if product.is_active:
                category = product.category
                if category not in products_by_category:
                    products_by_category[category] = []
                products_by_category[category].append(product)
        
        # Ordenar categorias
        sorted_categories = sorted(products_by_category.keys(), key=lambda x: x.order)
        
        products_html = ""
        for category in sorted_categories:
            products = sorted(products_by_category[category], key=lambda x: x.name)
            
            products_html += f'<div class="category-header"><h3>{category.emoji} {category.name}</h3></div>'
            products_html += '<div class="product-grid">'
            
            for product in products:
                organic_badge = "🌱 ORGÂNICO" if product.is_organic else ""
                products_html += f"""
                <div class="product-card">
                    <h4>{product.name} {organic_badge}</h4>
                    <p><strong>R$ {product.price:.2f}</strong> / {product.unit}</p>
                    <div class="form-group">
                        <label>Quantidade:</label>
                        <input type="number" class="quantity-input" id="qty_{product.id}" min="0" step="0.5" value="0" onchange="updateCart({product.id}, '{product.name}', {product.price}, '{product.unit}')">
                    </div>
                </div>
                """
            
            products_html += '</div>'
        
        return f"""
        <html>
        <head>
            <title>Em Casa - Hortifruti</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            {get_base_style()}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍃 Em Casa - Hortifruti Delivery</h1>
                    <p>Lista da semana: {active_list.week_start.strftime('%d/%m')} a {active_list.week_end.strftime('%d/%m/%Y')}</p>
                </div>
                
                {products_html}
                
                <div id="cart" class="cart" style="display: none;">
                    <h4>🛒 Carrinho</h4>
                    <div id="cart-items"></div>
                    <div id="cart-total"></div>
                    <button class="btn" onclick="showCheckout()">Finalizar Pedido</button>
                </div>
                
                <div id="checkout" style="display: none; margin-top: 30px; padding: 20px; border: 2px solid #28a745; border-radius: 10px;">
                    <h3>📋 Finalizar Pedido</h3>
                    <form id="checkout-form">
                        <div class="form-group">
                            <label>Nome completo:</label>
                            <input type="text" class="form-control" id="customer_name" required>
                        </div>
                        <div class="form-group">
                            <label>Telefone:</label>
                            <input type="tel" class="form-control" id="customer_phone">
                        </div>
                        <div class="form-group">
                            <label>Endereço de entrega:</label>
                            <textarea class="form-control" id="delivery_address" rows="3" required></textarea>
                        </div>
                        <div class="form-group">
                            <label>Local de entrega:</label>
                            <select class="form-control" id="delivery_location" onchange="updateDeliveryFee()">
                                <option value="maceio">Maceió (Taxa: R$ 10,00)</option>
                                <option value="paripueira">Paripueira (Taxa: R$ 10,00)</option>
                            </select>
                        </div>
                        <button type="button" class="btn" onclick="sendToWhatsApp()">📱 Enviar via WhatsApp</button>
                    </form>
                </div>
            </div>
            
            <script>
                let cart = {{}};
                let deliveryFee = 10.00;
                
                function updateCart(productId, productName, price, unit) {{
                    const qty = parseFloat(document.getElementById('qty_' + productId).value) || 0;
                    
                    if (qty > 0) {{
                        cart[productId] = {{
                            name: productName,
                            price: price,
                            unit: unit,
                            quantity: qty,
                            total: qty * price
                        }};
                    }} else {{
                        delete cart[productId];
                    }}
                    
                    updateCartDisplay();
                }}
                
                function updateCartDisplay() {{
                    const cartDiv = document.getElementById('cart');
                    const cartItems = document.getElementById('cart-items');
                    const cartTotal = document.getElementById('cart-total');
                    
                    if (Object.keys(cart).length === 0) {{
                        cartDiv.style.display = 'none';
                        return;
                    }}
                    
                    cartDiv.style.display = 'block';
                    
                    let itemsHtml = '';
                    let subtotal = 0;
                    
                    for (let productId in cart) {{
                        const item = cart[productId];
                        itemsHtml += `<div>${{item.quantity}} ${{item.unit}} - ${{item.name}} - R$ ${{item.total.toFixed(2)}}</div>`;
                        subtotal += item.total;
                    }}
                    
                    const total = subtotal + deliveryFee;
                    
                    cartItems.innerHTML = itemsHtml;
                    cartTotal.innerHTML = `
                        <div><strong>Subtotal: R$ ${{subtotal.toFixed(2)}}</strong></div>
                        <div>Taxa de entrega: R$ ${{deliveryFee.toFixed(2)}}</div>
                        <div><strong>Total: R$ ${{total.toFixed(2)}}</strong></div>
                    `;
                }}
                
                function updateDeliveryFee() {{
                    deliveryFee = 10.00;
                    updateCartDisplay();
                }}
                
                function showCheckout() {{
                    document.getElementById('checkout').style.display = 'block';
                    document.getElementById('checkout').scrollIntoView({{ behavior: 'smooth' }});
                }}
                
                function sendToWhatsApp() {{
                    const name = document.getElementById('customer_name').value;
                    const phone = document.getElementById('customer_phone').value;
                    const address = document.getElementById('delivery_address').value;
                    
                    if (!name || !address) {{
                        alert('Por favor, preencha nome e endereço!');
                        return;
                    }}
                    
                    let message = `🍃 *PEDIDO EM CASA HORTIFRUTI* 🍃\\n\\n`;
                    message += `👤 *Cliente:* ${{name}}\\n`;
                    if (phone) message += `📞 *Telefone:* ${{phone}}\\n`;
                    message += `📍 *Endereço:* ${{address}}\\n\\n`;
                    message += `🛒 *PRODUTOS:*\\n`;
                    
                    let subtotal = 0;
                    for (let productId in cart) {{
                        const item = cart[productId];
                        message += `• ${{item.quantity}} ${{item.unit}} - ${{item.name}} - R$ ${{item.total.toFixed(2)}}\\n`;
                        subtotal += item.total;
                    }}
                    
                    const total = subtotal + deliveryFee;
                    message += `\\n💰 *RESUMO:*\\n`;
                    message += `Subtotal: R$ ${{subtotal.toFixed(2)}}\\n`;
                    message += `Taxa de entrega: R$ ${{deliveryFee.toFixed(2)}}\\n`;
                    message += `*TOTAL: R$ ${{total.toFixed(2)}}*\\n\\n`;
                    message += `Obrigado pela preferência! 🌱`;
                    
                    // Salvar pedido no banco
                    const orderData = {{
                        customer_name: name,
                        customer_phone: phone,
                        delivery_address: address,
                        delivery_fee: deliveryFee,
                        total_amount: total,
                        items: cart
                    }};
                    
                    fetch('/api/save-order', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(orderData)
                    }});
                    
                    // Enviar para WhatsApp
                    const whatsappNumber = '5582996603943';
                    const whatsappUrl = `https://wa.me/${{whatsappNumber}}?text=${{encodeURIComponent(message)}}`;
                    window.open(whatsappUrl, '_blank');
                }}
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"❌ Erro na página inicial: {e}")
        return f"<h1>Erro: {e}</h1><p><a href='/admin/login'>Área Administrativa</a></p>"

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
            return redirect('/admin')
        else:
            error_msg = '<div class="alert alert-error">❌ Usuário ou senha incorretos!</div>'
    else:
        error_msg = ''
    
    return f"""
    <html>
    <head><title>Login Admin</title>{get_base_style()}</head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🔐 Login Administrativo</h2>
            </div>
            {error_msg}
            <form method="POST">
                <div class="form-group">
                    <label>Usuário:</label>
                    <input type="text" name="username" class="form-control" required>
                </div>
                <div class="form-group">
                    <label>Senha:</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn">Entrar</button>
            </form>
            <p><small>Usuário: mario | Senha: 3943</small></p>
        </div>
    </body>
    </html>
    """

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect('/')

@app.route('/admin')
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    try:
        # Estatísticas gerais
        total_products = Product.query.filter_by(is_active=True).count()
        active_list = WeeklyList.query.filter_by(is_active=True).first()
        total_orders = Order.query.count()
        
        recent_orders = []
        if active_list:
            recent_orders = Order.query.filter_by(weekly_list_id=active_list.id).order_by(Order.created_at.desc()).limit(5).all()
        
        # Status da lista
        list_status = "Nenhuma lista ativa"
        if active_list:
            if active_list.is_closed:
                list_status = f"Lista encerrada ({active_list.week_start.strftime('%d/%m')} a {active_list.week_end.strftime('%d/%m')})"
            else:
                list_status = f"Lista ativa ({active_list.week_start.strftime('%d/%m')} a {active_list.week_end.strftime('%d/%m')})"
        
        # Pedidos recentes HTML
        orders_html = ""
        for order in recent_orders:
            orders_html += f"""
            <tr>
                <td>{order.customer_name}</td>
                <td>R$ {order.total_amount:.2f}</td>
                <td>{order.created_at.strftime('%d/%m %H:%M')}</td>
            </tr>
            """
        
        if not orders_html:
            orders_html = "<tr><td colspan='3'>Nenhum pedido ainda</td></tr>"
        
        return f"""
        <html>
        <head><title>Painel Admin</title>{get_base_style()}</head>
        <body>
            <div class="nav">
                <a href="/admin">Dashboard</a>
                <a href="/admin/products">Produtos</a>
                <a href="/admin/create-list">Nova Lista</a>
                <a href="/admin/reports">Relatórios</a>
                <a href="/admin/logout">Sair</a>
            </div>
            <div class="container">
                <div class="header">
                    <h1>📊 Painel Administrativo</h1>
                </div>
                
                <div class="product-grid">
                    <div class="product-card">
                        <h3>📦 Produtos</h3>
                        <p><strong>{total_products}</strong> produtos ativos</p>
                    </div>
                    <div class="product-card">
                        <h3>📋 Lista Semanal</h3>
                        <p>{list_status}</p>
                    </div>
                    <div class="product-card">
                        <h3>🛒 Pedidos</h3>
                        <p><strong>{total_orders}</strong> pedidos total</p>
                    </div>
                </div>
                
                <h3>📋 Pedidos Recentes</h3>
                <table>
                    <thead>
                        <tr><th>Cliente</th><th>Total</th><th>Data</th></tr>
                    </thead>
                    <tbody>
                        {orders_html}
                    </tbody>
                </table>
                
                <div style="margin-top: 30px;">
                    <a href="/admin/create-list" class="btn">➕ Nova Lista Semanal</a>
                    <a href="/admin/reports" class="btn">📊 Ver Relatórios</a>
                    <a href="/" class="btn">🌐 Ver Site</a>
                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"<h1>Erro: {e}</h1>"

@app.route('/admin/products')
def admin_products():
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    products = Product.query.join(Category).order_by(Category.order, Product.name).all()
    
    products_html = ""
    for product in products:
        status = "✅ Ativo" if product.is_active else "❌ Inativo"
        organic = "🌱" if product.is_organic else ""
        products_html += f"""
        <tr>
            <td>{product.category.emoji} {product.category.name}</td>
            <td>{product.name} {organic}</td>
            <td>R$ {product.price:.2f}</td>
            <td>{product.unit}</td>
            <td>{status}</td>
            <td>
                <a href="/admin/products/{product.id}/edit" class="btn btn-warning">✏️ Editar</a>
                <a href="/admin/products/{product.id}/delete" class="btn btn-danger" onclick="return confirm('Tem certeza?')">🗑️ Deletar</a>
            </td>
        </tr>
        """
    
    # Opções de categoria para novo produto
    categories = Category.query.order_by(Category.order).all()
    category_options = ""
    for cat in categories:
        category_options += f'<option value="{cat.id}">{cat.emoji} {cat.name}</option>'
    
    return f"""
    <html>
    <head><title>Produtos</title>{get_base_style()}</head>
    <body>
        <div class="nav">
            <a href="/admin">Dashboard</a>
            <a href="/admin/products">Produtos</a>
            <a href="/admin/create-list">Nova Lista</a>
            <a href="/admin/reports">Relatórios</a>
            <a href="/admin/logout">Sair</a>
        </div>
        <div class="container">
            <h1>📦 Gestão de Produtos</h1>
            
            <button onclick="document.getElementById('addModal').style.display='block'" class="btn">➕ Adicionar Produto</button>
            
            <table>
                <thead>
                    <tr><th>Categoria</th><th>Produto</th><th>Preço</th><th>Unidade</th><th>Status</th><th>Ações</th></tr>
                </thead>
                <tbody>
                    {products_html}
                </tbody>
            </table>
            
            <p><em>Total: {len(products)} produtos cadastrados</em></p>
        </div>
        
        <!-- Modal Adicionar Produto -->
        <div id="addModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="document.getElementById('addModal').style.display='none'">&times;</span>
                <h2>➕ Adicionar Produto</h2>
                <form method="POST" action="/admin/products/add">
                    <div class="form-group">
                        <label>Nome do produto:</label>
                        <input type="text" name="name" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label>Preço:</label>
                        <input type="number" name="price" class="form-control" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Unidade:</label>
                        <input type="text" name="unit" class="form-control" placeholder="kg, un, maço, etc." required>
                    </div>
                    <div class="form-group">
                        <label>Categoria:</label>
                        <select name="category_id" class="form-control" required>
                            {category_options}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="is_organic" value="1"> 🌱 Produto orgânico
                        </label>
                    </div>
                    <button type="submit" class="btn">Adicionar</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/admin/products/add', methods=['POST'])
def admin_add_product():
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    try:
        product = Product(
            name=request.form['name'],
            price=float(request.form['price']),
            unit=request.form['unit'],
            is_organic=bool(request.form.get('is_organic')),
            category_id=int(request.form['category_id'])
        )
        db.session.add(product)
        db.session.commit()
        return redirect('/admin/products')
    except Exception as e:
        return f"<h1>Erro ao adicionar produto: {e}</h1>"

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.price = float(request.form['price'])
            product.unit = request.form['unit']
            product.is_organic = bool(request.form.get('is_organic'))
            product.category_id = int(request.form['category_id'])
            product.is_active = bool(request.form.get('is_active'))
            
            db.session.commit()
            return redirect('/admin/products')
        except Exception as e:
            return f"<h1>Erro ao editar produto: {e}</h1>"
    
    # Opções de categoria
    categories = Category.query.order_by(Category.order).all()
    category_options = ""
    for cat in categories:
        selected = "selected" if cat.id == product.category_id else ""
        category_options += f'<option value="{cat.id}" {selected}>{cat.emoji} {cat.name}</option>'
    
    organic_checked = "checked" if product.is_organic else ""
    active_checked = "checked" if product.is_active else ""
    
    return f"""
    <html>
    <head><title>Editar Produto</title>{get_base_style()}</head>
    <body>
        <div class="container">
            <h1>✏️ Editar Produto</h1>
            
            <form method="POST">
                <div class="form-group">
                    <label>Nome do produto:</label>
                    <input type="text" name="name" class="form-control" value="{product.name}" required>
                </div>
                <div class="form-group">
                    <label>Preço:</label>
                    <input type="number" name="price" class="form-control" step="0.01" value="{product.price}" required>
                </div>
                <div class="form-group">
                    <label>Unidade:</label>
                    <input type="text" name="unit" class="form-control" value="{product.unit}" required>
                </div>
                <div class="form-group">
                    <label>Categoria:</label>
                    <select name="category_id" class="form-control" required>
                        {category_options}
                    </select>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="is_organic" value="1" {organic_checked}> 🌱 Produto orgânico
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="is_active" value="1" {active_checked}> ✅ Produto ativo
                    </label>
                </div>
                <button type="submit" class="btn">💾 Salvar</button>
                <a href="/admin/products" class="btn btn-danger">❌ Cancelar</a>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/admin/products/<int:product_id>/delete')
def admin_delete_product(product_id):
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return redirect('/admin/products')
    except Exception as e:
        return f"<h1>Erro ao deletar produto: {e}</h1>"

@app.route('/admin/create-list', methods=['GET', 'POST'])
def admin_create_weekly_list():
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
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
            
            return f"""
            <html>
            <head><title>Lista Criada</title>{get_base_style()}</head>
            <body>
                <div class="container">
                    <div class="alert alert-success">
                        ✅ Lista semanal criada com sucesso!
                    </div>
                    <a href="/admin" class="btn">Voltar ao Dashboard</a>
                    <a href="/" class="btn">Ver Site</a>
                </div>
            </body>
            </html>
            """
            
        except Exception as e:
            return f"<h1>Erro ao criar lista: {e}</h1>"
    
    # Buscar produtos por categoria
    categories = Category.query.order_by(Category.order).all()
    
    products_html = ""
    for category in categories:
        products = Product.query.filter_by(category_id=category.id, is_active=True).order_by(Product.name).all()
        if products:
            products_html += f'<h4>{category.emoji} {category.name}</h4>'
            for product in products:
                organic = "🌱" if product.is_organic else ""
                products_html += f"""
                <label style="display: block; margin: 5px 0;">
                    <input type="checkbox" name="products" value="{product.id}">
                    {product.name} {organic} - R$ {product.price:.2f}/{product.unit}
                </label>
                """
    
    return f"""
    <html>
    <head><title>Nova Lista</title>{get_base_style()}</head>
    <body>
        <div class="nav">
            <a href="/admin">Dashboard</a>
            <a href="/admin/products">Produtos</a>
            <a href="/admin/create-list">Nova Lista</a>
            <a href="/admin/reports">Relatórios</a>
            <a href="/admin/logout">Sair</a>
        </div>
        <div class="container">
            <h1>📋 Nova Lista Semanal</h1>
            
            <form method="POST">
                <div class="form-group">
                    <label>Data de início:</label>
                    <input type="date" name="week_start" class="form-control" required>
                </div>
                <div class="form-group">
                    <label>Data de fim:</label>
                    <input type="date" name="week_end" class="form-control" required>
                </div>
                
                <h3>Selecionar Produtos:</h3>
                <button type="button" onclick="selectAll()" class="btn">Selecionar Todos</button>
                <button type="button" onclick="selectNone()" class="btn">Desmarcar Todos</button>
                
                <div style="margin: 20px 0;">
                    {products_html}
                </div>
                
                <button type="submit" class="btn">✅ Criar Lista Semanal</button>
            </form>
            
            <script>
                function selectAll() {{
                    const checkboxes = document.querySelectorAll('input[name="products"]');
                    checkboxes.forEach(cb => cb.checked = true);
                }}
                
                function selectNone() {{
                    const checkboxes = document.querySelectorAll('input[name="products"]');
                    checkboxes.forEach(cb => cb.checked = false);
                }}
            </script>
        </div>
    </body>
    </html>
    """

@app.route('/admin/reports')
def admin_reports():
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    # Relatório da semana atual
    active_list = WeeklyList.query.filter_by(is_active=True).first()
    
    if not active_list:
        return f"""
        <html>
        <head><title>Relatórios</title>{get_base_style()}</head>
        <body>
            <div class="nav">
                <a href="/admin">Dashboard</a>
                <a href="/admin/products">Produtos</a>
                <a href="/admin/create-list">Nova Lista</a>
                <a href="/admin/reports">Relatórios</a>
                <a href="/admin/logout">Sair</a>
            </div>
            <div class="container">
                <h1>📊 Relatórios</h1>
                <p>Nenhuma lista ativa para gerar relatórios.</p>
                <a href="/admin/create-list" class="btn">Criar Lista Semanal</a>
            </div>
        </body>
        </html>
        """
    
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
    
    # HTML dos produtos vendidos
    sales_html = ""
    for sale in product_sales:
        sales_html += f"""
        <tr>
            <td>{sale.name}</td>
            <td>{sale.total_quantity} {sale.unit}</td>
            <td>R$ {sale.total_revenue:.2f}</td>
        </tr>
        """
    
    if not sales_html:
        sales_html = "<tr><td colspan='3'>Nenhum pedido ainda</td></tr>"
    
    return f"""
    <html>
    <head><title>Relatórios</title>{get_base_style()}</head>
    <body>
        <div class="nav">
            <a href="/admin">Dashboard</a>
            <a href="/admin/products">Produtos</a>
            <a href="/admin/create-list">Nova Lista</a>
            <a href="/admin/reports">Relatórios</a>
            <a href="/admin/logout">Sair</a>
        </div>
        <div class="container">
            <h1>📊 Relatórios da Semana</h1>
            <p><strong>Período:</strong> {active_list.week_start.strftime('%d/%m')} a {active_list.week_end.strftime('%d/%m/%Y')}</p>
            
            <div class="product-grid">
                <div class="product-card">
                    <h3>🛒 Total de Pedidos</h3>
                    <p><strong>{total_orders}</strong></p>
                </div>
                <div class="product-card">
                    <h3>💰 Receita Total</h3>
                    <p><strong>R$ {total_revenue:.2f}</strong></p>
                </div>
            </div>
            
            <h3>📦 Produtos Mais Vendidos</h3>
            <table>
                <thead>
                    <tr><th>Produto</th><th>Quantidade</th><th>Receita</th></tr>
                </thead>
                <tbody>
                    {sales_html}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

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

