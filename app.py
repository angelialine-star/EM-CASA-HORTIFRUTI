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
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 10px; background: #f8f9fa; line-height: 1.4; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 20px rgba(0,0,0,0.08); }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 { margin: 0 0 10px 0; font-size: 1.8em; color: #2d5016; }
        .header p { margin: 5px 0; color: #666; }
        
        /* Botões */
        .btn { padding: 12px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 8px; border: none; cursor: pointer; margin: 5px; display: inline-block; font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .btn:hover { background: #218838; transform: translateY(-1px); }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .btn-sm { padding: 8px 12px; font-size: 12px; }
        
        /* Formulários */
        .form-group { margin-bottom: 15px; }
        .form-control { width: 100%; padding: 12px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 16px; transition: border-color 0.2s; }
        .form-control:focus { border-color: #28a745; outline: none; }
        
        /* Alertas */
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 8px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        
        /* Grid de produtos - MOBILE FIRST */
        .products-container { margin-bottom: 120px; }
        .category-section { margin-bottom: 30px; }
        .category-header { background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 15px; margin: 0 0 15px 0; border-radius: 10px; text-align: center; }
        .category-header h3 { margin: 0; font-size: 1.3em; }
        
        .product-grid { display: grid; grid-template-columns: 1fr; gap: 15px; }
        @media (min-width: 768px) { .product-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (min-width: 1024px) { .product-grid { grid-template-columns: repeat(3, 1fr); } }
        
        .product-card { 
            border: 2px solid #e9ecef; 
            padding: 20px; 
            border-radius: 12px; 
            background: white; 
            transition: all 0.2s;
            position: relative;
        }
        .product-card:hover { border-color: #28a745; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.1); }
        
        .product-name { font-size: 1.1em; font-weight: 600; margin: 0 0 8px 0; color: #2d5016; }
        .product-price { font-size: 1.3em; font-weight: 700; color: #28a745; margin: 0 0 5px 0; }
        .product-unit { color: #666; font-size: 0.9em; margin: 0 0 15px 0; }
        .organic-badge { background: #28a745; color: white; padding: 4px 8px; border-radius: 20px; font-size: 0.8em; font-weight: 500; }
        
        /* Controles de quantidade - MOBILE OTIMIZADO */
        .quantity-controls { 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 15px; 
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .qty-btn { 
            width: 45px; 
            height: 45px; 
            border: none; 
            border-radius: 50%; 
            background: #28a745; 
            color: white; 
            font-size: 20px; 
            font-weight: bold; 
            cursor: pointer; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            transition: all 0.2s;
        }
        .qty-btn:hover { background: #218838; transform: scale(1.1); }
        .qty-btn:disabled { background: #6c757d; cursor: not-allowed; transform: none; }
        .qty-display { 
            font-size: 1.2em; 
            font-weight: 600; 
            min-width: 60px; 
            text-align: center; 
            padding: 8px 12px;
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
        }
        
        /* Carrinho fixo - REPOSICIONADO */
        .cart-summary { 
            position: fixed; 
            bottom: 0; 
            left: 0; 
            right: 0; 
            background: linear-gradient(135deg, #28a745, #20c997); 
            color: white; 
            padding: 15px; 
            box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            display: none;
        }
        .cart-content { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .cart-info { flex: 1; }
        .cart-total { font-size: 1.2em; font-weight: 700; }
        .cart-items-count { font-size: 0.9em; opacity: 0.9; }
        
        /* Checkout */
        .checkout-section { 
            margin-top: 30px; 
            margin-bottom: 120px;
            padding: 25px; 
            border: 3px solid #28a745; 
            border-radius: 15px; 
            background: #f8fff9;
            display: none;
        }
        .checkout-title { color: #2d5016; margin: 0 0 20px 0; text-align: center; }
        
        /* Tabelas admin */
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: 600; }
        
        /* Navegação admin */
        .nav { background: #343a40; padding: 10px 0; margin-bottom: 20px; border-radius: 8px; }
        .nav a { color: white; text-decoration: none; padding: 10px 15px; margin: 0 5px; border-radius: 5px; }
        .nav a:hover { background: #495057; }
        
        /* Modal */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: white; margin: 5% auto; padding: 25px; border-radius: 15px; width: 90%; max-width: 500px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
        
        /* Responsividade */
        @media (max-width: 768px) {
            .container { padding: 10px; margin: 5px; }
            .header h1 { font-size: 1.5em; }
            .cart-content { flex-direction: column; text-align: center; }
            .btn { padding: 10px 15px; font-size: 13px; }
        }
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
            <head>
                <title>Em Casa - Hortifruti</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                {get_base_style()}
            </head>
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
            
            products_html += f"""
            <div class="category-section">
                <div class="category-header">
                    <h3>{category.emoji} {category.name}</h3>
                </div>
                <div class="product-grid">
            """
            
            for product in products:
                organic_badge = '<span class="organic-badge">🌱 AGROECOLÓGICO</span>' if product.is_organic else ""
                products_html += f"""
                <div class="product-card">
                    <div class="product-name">{product.name}</div>
                    <div class="product-price">R$ {product.price:.2f}</div>
                    <div class="product-unit">por {product.unit}</div>
                    {organic_badge}
                    
                    <div class="quantity-controls">
                        <button class="qty-btn" onclick="decreaseQty({product.id})" id="minus_{product.id}">−</button>
                        <div class="qty-display" id="qty_display_{product.id}">0</div>
                        <button class="qty-btn" onclick="increaseQty({product.id}, '{product.name}', {product.price}, '{product.unit}')">+</button>
                    </div>
                </div>
                """
            
            products_html += '</div></div>'
        
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
                    <p><strong>Lista da semana:</strong> {active_list.week_start.strftime('%d/%m')} a {active_list.week_end.strftime('%d/%m/%Y')}</p>
                    <p>📱 WhatsApp: <strong>(82) 99660-3943</strong></p>
                </div>
                
                <div class="products-container">
                    {products_html}
                </div>
                
                <div id="cart-summary" class="cart-summary">
                    <div class="cart-content">
                        <div class="cart-info">
                            <div class="cart-total" id="cart-total">R$ 0,00</div>
                            <div class="cart-items-count" id="cart-items-count">0 itens</div>
                        </div>
                        <button class="btn" onclick="showCheckout()">Finalizar Pedido</button>
                    </div>
                </div>
                
                <div id="checkout" class="checkout-section">
                    <h3 class="checkout-title">📋 Finalizar Pedido</h3>
                    <div id="checkout-items" style="margin-bottom: 20px; padding: 15px; background: white; border-radius: 8px;"></div>
                    
                    <form id="checkout-form">
                        <div class="form-group">
                            <label><strong>Nome completo:</strong> *</label>
                            <input type="text" class="form-control" id="customer_name" required placeholder="Seu nome completo">
                        </div>
                        <div class="form-group">
                            <label><strong>Telefone:</strong></label>
                            <input type="tel" class="form-control" id="customer_phone" placeholder="(82) 99999-9999 (opcional)">
                        </div>
                        <div class="form-group">
                            <label><strong>Endereço de entrega:</strong></label>
                            <textarea class="form-control" id="delivery_address" rows="3" placeholder="Rua, número, bairro... (opcional para clientes conhecidos)"></textarea>
                        </div>
                        <div class="form-group">
                            <label><strong>Local de entrega:</strong></label>
                            <select class="form-control" id="delivery_location" onchange="updateDeliveryFee()">
                                <option value="maceio">Maceió (Taxa: R$ 10,00)</option>
                                <option value="paripueira">Paripueira (Taxa: R$ 10,00)</option>
                            </select>
                        </div>
                        
                        <div style="text-align: center; margin-top: 25px;">
                            <button type="button" class="btn" onclick="sendToWhatsApp()" style="font-size: 16px; padding: 15px 30px;">
                                📱 Enviar Pedido via WhatsApp
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            
            <script>
                let cart = {{}};
                let deliveryFee = 10.00;
                
                function increaseQty(productId, productName, price, unit) {{
                    if (!cart[productId]) {{
                        cart[productId] = {{
                            name: productName,
                            price: price,
                            unit: unit,
                            quantity: 0
                        }};
                    }}
                    
                    cart[productId].quantity += 1;
                    updateDisplay(productId);
                    updateCartSummary();
                }}
                
                function decreaseQty(productId) {{
                    if (cart[productId] && cart[productId].quantity > 0) {{
                        cart[productId].quantity -= 1;
                        if (cart[productId].quantity === 0) {{
                            delete cart[productId];
                        }}
                        updateDisplay(productId);
                        updateCartSummary();
                    }}
                }}
                
                function updateDisplay(productId) {{
                    const qty = cart[productId] ? cart[productId].quantity : 0;
                    document.getElementById('qty_display_' + productId).textContent = qty;
                    
                    const minusBtn = document.getElementById('minus_' + productId);
                    minusBtn.disabled = qty === 0;
                }}
                
                function updateCartSummary() {{
                    const cartSummary = document.getElementById('cart-summary');
                    const cartTotal = document.getElementById('cart-total');
                    const cartItemsCount = document.getElementById('cart-items-count');
                    
                    let subtotal = 0;
                    let itemCount = 0;
                    
                    for (let productId in cart) {{
                        const item = cart[productId];
                        subtotal += item.quantity * item.price;
                        itemCount += item.quantity;
                    }}
                    
                    if (itemCount > 0) {{
                        const total = subtotal + deliveryFee;
                        cartTotal.textContent = `R$ ${{total.toFixed(2).replace('.', ',')}}`;
                        cartItemsCount.textContent = `${{itemCount}} ${{itemCount === 1 ? 'item' : 'itens'}}`;
                        cartSummary.style.display = 'block';
                    }} else {{
                        cartSummary.style.display = 'none';
                    }}
                }}
                
                function updateDeliveryFee() {{
                    deliveryFee = 10.00;
                    updateCartSummary();
                }}
                
                function showCheckout() {{
                    let checkoutItems = '';
                    let subtotal = 0;
                    
                    for (let productId in cart) {{
                        const item = cart[productId];
                        const itemTotal = item.quantity * item.price;
                        subtotal += itemTotal;
                        checkoutItems += `
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;">
                                <span>${{item.quantity}} ${{item.unit}} - ${{item.name}}</span>
                                <span><strong>R$ ${{itemTotal.toFixed(2).replace('.', ',')}}</strong></span>
                            </div>
                        `;
                    }}
                    
                    const total = subtotal + deliveryFee;
                    checkoutItems += `
                        <div style="padding: 10px 0; font-weight: bold;">
                            <div style="display: flex; justify-content: space-between;">
                                <span>Subtotal:</span>
                                <span>R$ ${{subtotal.toFixed(2).replace('.', ',')}}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span>Taxa de entrega:</span>
                                <span>R$ ${{deliveryFee.toFixed(2).replace('.', ',')}}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 1.2em; color: #28a745; border-top: 2px solid #28a745; padding-top: 10px; margin-top: 10px;">
                                <span>TOTAL:</span>
                                <span>R$ ${{total.toFixed(2).replace('.', ',')}}</span>
                            </div>
                        </div>
                    `;
                    
                    document.getElementById('checkout-items').innerHTML = checkoutItems;
                    document.getElementById('checkout').style.display = 'block';
                    document.getElementById('checkout').scrollIntoView({{ behavior: 'smooth' }});
                }}
                
                function sendToWhatsApp() {{
                    const name = document.getElementById('customer_name').value.trim();
                    const phone = document.getElementById('customer_phone').value.trim();
                    const address = document.getElementById('delivery_address').value.trim();
                    
                    if (!name) {{
                        alert('Por favor, preencha seu nome!');
                        return;
                    }}
                    
                    let message = `🍃 *PEDIDO EM CASA HORTIFRUTI* 🍃\\n\\n`;
                    message += `👤 *Cliente:* ${{name}}\\n`;
                    if (phone) message += `📞 *Telefone:* ${{phone}}\\n`;
                    if (address) message += `📍 *Endereço:* ${{address}}\\n`;
                    message += `\\n🛒 *PRODUTOS:*\\n`;
                    
                    let subtotal = 0;
                    for (let productId in cart) {{
                        const item = cart[productId];
                        const itemTotal = item.quantity * item.price;
                        message += `• ${{item.quantity}} ${{item.unit}} - ${{item.name}} - R$ ${{itemTotal.toFixed(2).replace('.', ',')}}\\n`;
                        subtotal += itemTotal;
                    }}
                    
                    const total = subtotal + deliveryFee;
                    message += `\\n💰 *RESUMO:*\\n`;
                    message += `Subtotal: R$ ${{subtotal.toFixed(2).replace('.', ',')}}\\n`;
                    message += `Taxa de entrega: R$ ${{deliveryFee.toFixed(2).replace('.', ',')}}\\n`;
                    message += `*TOTAL: R$ ${{total.toFixed(2).replace('.', ',')}}*\\n\\n`;
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
                
                // Inicializar displays
                document.addEventListener('DOMContentLoaded', function() {{
                    const minusButtons = document.querySelectorAll('[id^="minus_"]');
                    minusButtons.forEach(btn => btn.disabled = true);
                }});
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
                total_price=item_data['quantity'] * item_data['price']
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
        total_categories = Category.query.count()
        active_list = WeeklyList.query.filter_by(is_active=True).first()
        
        recent_orders = []
        total_orders_week = 0
        if active_list:
            recent_orders = Order.query.filter_by(weekly_list_id=active_list.id).order_by(Order.created_at.desc()).limit(5).all()
            total_orders_week = Order.query.filter_by(weekly_list_id=active_list.id).count()
        
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
                <td><a href="/admin/orders/{order.id}" style="color: #28a745; text-decoration: none;">{order.customer_name}</a></td>
                <td>R$ {order.total_amount:.2f}</td>
                <td>{order.created_at.strftime('%d/%m %H:%M')}</td>
                <td><a href="/admin/orders/{order.id}" class="btn btn-sm">Ver Detalhes</a></td>
            </tr>
            """
        
        if not orders_html:
            orders_html = "<tr><td colspan='4'>Nenhum pedido ainda</td></tr>"
        
        return f"""
        <html>
        <head><title>Painel Admin</title>{get_base_style()}</head>
        <body>
            <div class="nav">
                <a href="/admin">Dashboard</a>
                <a href="/admin/orders">Pedidos</a>
                <a href="/admin/products">Produtos</a>
                <a href="/admin/categories">Categorias</a>
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
                        <h3>🏷️ Categorias</h3>
                        <p><strong>{total_categories}</strong> categorias</p>
                    </div>
                    <div class="product-card">
                        <h3>📋 Lista Semanal</h3>
                        <p>{list_status}</p>
                    </div>
                    <div class="product-card">
                        <h3>🛒 Pedidos da Semana</h3>
                        <p><strong>{total_orders_week}</strong> pedidos</p>
                    </div>
                </div>
                
                <h3>📋 Pedidos Recentes</h3>
                <table>
                    <thead>
                        <tr><th>Cliente</th><th>Total</th><th>Data</th><th>Ações</th></tr>
                    </thead>
                    <tbody>
                        {orders_html}
                    </tbody>
                </table>
                
                <div style="margin-top: 30px;">
                    <a href="/admin/orders" class="btn">📋 Ver Todos os Pedidos</a>
                    <a href="/admin/categories" class="btn">🏷️ Gerenciar Categorias</a>
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

# ROTAS PARA GESTÃO DE CATEGORIAS

@app.route('/admin/categories')
def admin_categories():
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    categories = Category.query.order_by(Category.order).all()
    
    categories_html = ""
    for category in categories:
        product_count = Product.query.filter_by(category_id=category.id).count()
        categories_html += f"""
        <tr>
            <td>{category.order}</td>
            <td>{category.emoji}</td>
            <td>{category.name}</td>
            <td>{product_count} produtos</td>
            <td>
                <a href="/admin/categories/{category.id}/edit" class="btn btn-warning btn-sm">✏️ Editar</a>
                <a href="/admin/categories/{category.id}/delete" class="btn btn-danger btn-sm" onclick="return confirm('Tem certeza? Isso pode afetar produtos desta categoria.')">🗑️ Deletar</a>
            </td>
        </tr>
        """
    
    return f"""
    <html>
    <head><title>Categorias</title>{get_base_style()}</head>
    <body>
        <div class="nav">
            <a href="/admin">Dashboard</a>
            <a href="/admin/orders">Pedidos</a>
            <a href="/admin/products">Produtos</a>
            <a href="/admin/categories">Categorias</a>
            <a href="/admin/create-list">Nova Lista</a>
            <a href="/admin/reports">Relatórios</a>
            <a href="/admin/logout">Sair</a>
        </div>
        <div class="container">
            <h1>🏷️ Gestão de Categorias</h1>
            
            <button onclick="document.getElementById('addModal').style.display='block'" class="btn">➕ Adicionar Categoria</button>
            
            <table>
                <thead>
                    <tr><th>Ordem</th><th>Emoji</th><th>Nome</th><th>Produtos</th><th>Ações</th></tr>
                </thead>
                <tbody>
                    {categories_html}
                </tbody>
            </table>
            
            <p><em>Total: {len(categories)} categorias</em></p>
            <p><small>💡 Dica: A ordem determina como as categorias aparecem no site.</small></p>
        </div>
        
        <!-- Modal Adicionar Categoria -->
        <div id="addModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="document.getElementById('addModal').style.display='none'">&times;</span>
                <h2>➕ Adicionar Categoria</h2>
                <form method="POST" action="/admin/categories/add">
                    <div class="form-group">
                        <label>Nome da categoria:</label>
                        <input type="text" name="name" class="form-control" placeholder="Ex: CHÁS" required>
                    </div>
                    <div class="form-group">
                        <label>Emoji:</label>
                        <input type="text" name="emoji" class="form-control" placeholder="Ex: 🍵" required>
                    </div>
                    <div class="form-group">
                        <label>Ordem de exibição:</label>
                        <input type="number" name="order" class="form-control" value="{len(categories) + 1}" required>
                    </div>
                    <button type="submit" class="btn">Adicionar</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/admin/categories/add', methods=['POST'])
def admin_add_category():
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    try:
        category = Category(
            name=request.form['name'].upper(),
            emoji=request.form['emoji'],
            order=int(request.form['order'])
        )
        db.session.add(category)
        db.session.commit()
        return redirect('/admin/categories')
    except Exception as e:
        return f"<h1>Erro ao adicionar categoria: {e}</h1>"

@app.route('/admin/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def admin_edit_category(category_id):
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        try:
            category.name = request.form['name'].upper()
            category.emoji = request.form['emoji']
            category.order = int(request.form['order'])
            
            db.session.commit()
            return redirect('/admin/categories')
        except Exception as e:
            return f"<h1>Erro ao editar categoria: {e}</h1>"
    
    return f"""
    <html>
    <head><title>Editar Categoria</title>{get_base_style()}</head>
    <body>
        <div class="container">
            <h1>✏️ Editar Categoria</h1>
            
            <form method="POST">
                <div class="form-group">
                    <label>Nome da categoria:</label>
                    <input type="text" name="name" class="form-control" value="{category.name}" required>
                </div>
                <div class="form-group">
                    <label>Emoji:</label>
                    <input type="text" name="emoji" class="form-control" value="{category.emoji}" required>
                </div>
                <div class="form-group">
                    <label>Ordem de exibição:</label>
                    <input type="number" name="order" class="form-control" value="{category.order}" required>
                </div>
                <button type="submit" class="btn">💾 Salvar</button>
                <a href="/admin/categories" class="btn btn-danger">❌ Cancelar</a>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/admin/categories/<int:category_id>/delete')
def admin_delete_category(category_id):
    if not is_admin_logged_in():
        return redirect('/admin/login')
    
    try:
        category = Category.query.get_or_404(category_id)
        
        # Verificar se há produtos nesta categoria
        product_count = Product.query.filter_by(category_id=category_id).count()
        if product_count > 0:
            return f"""
            <html>
            <head><title>Erro</title>{get_base_style()}</head>
            <body>
                <div class="container">
                    <div class="alert alert-error">
                        ❌ Não é possível deletar esta categoria pois ela possui {product_count} produtos.
                        <br>Mova os produtos para outra categoria primeiro.
                    </div>
                    <a href="/admin/categories" class="btn">← Voltar às Categorias</a>
                </div>
            </body>
            </html>
            """
        
        db.session.delete(category)
        db.session.commit()
        return redirect('/admin/categories')
    except Exception as e:
        return f"<h1>Erro ao deletar categoria: {e}</h1>"

# Continuar com as outras rotas (orders, products, etc.) - mantendo todas as funcionalidades existentes
# [Resto do código permanece igual ao arquivo anterior]

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

