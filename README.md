# 🍃 Em Casa - Hortifruti Delivery

Sistema completo para gestão de vendas de produtos agroecológicos com integração WhatsApp.

## 📋 Funcionalidades

### Para Clientes
- ✅ Interface simples para seleção de produtos
- ✅ Carrinho de compras interativo
- ✅ Cálculo automático de taxa de entrega
- ✅ Envio direto para WhatsApp do agricultor
- ✅ Sem necessidade de cadastro ou login

### Para Administrador (Mario)
- ✅ Painel administrativo completo
- ✅ Gestão de produtos e categorias
- ✅ Criação de listas semanais
- ✅ Controle de pedidos (encerrar/ativar)
- ✅ Relatórios detalhados de vendas
- ✅ Lista de compras para organização

## 🚀 Como Usar

### Acesso dos Clientes
1. Acesse o link da semana
2. Selecione produtos e quantidades
3. Preencha seus dados
4. Clique em "Enviar via WhatsApp"
5. Confirme o pedido no WhatsApp

### Acesso Administrativo
1. Acesse `/admin/login`
2. **Usuário:** mario
3. **Senha:** 3943
4. Gerencie produtos e listas semanais

## 🛠️ Instalação Local

### Pré-requisitos
- Python 3.11+
- Git

### Passos
```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd em-casa-hortifruti

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale dependências
pip install -r requirements.txt

# 5. Execute a aplicação
python app.py
```

A aplicação estará disponível em: http://localhost:5000

## 🌐 Deploy no Railway

### 1. Preparar Repositório GitHub
```bash
# Inicializar git (se não feito)
git init
git add .
git commit -m "Initial commit"

# Conectar ao GitHub
git remote add origin <seu-repositorio-github>
git push -u origin main
```

### 2. Deploy no Railway
1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha o repositório `em-casa-hortifruti`
6. Railway detectará automaticamente que é uma aplicação Python
7. O deploy será feito automaticamente

### 3. Configurar Domínio
1. No painel do Railway, vá em "Settings"
2. Em "Domains", clique em "Generate Domain"
3. Copie o link gerado (ex: `https://em-casa-hortifruti-production.up.railway.app`)

## 📱 Configuração do WhatsApp

O número do WhatsApp está configurado como: **+55 (82) 99660-3943**

Para alterar, edite o arquivo `templates/index.html` na linha que contém:
```javascript
const whatsappNumber = '5582996603943';
```

## 🗂️ Estrutura do Projeto

```
em-casa-hortifruti/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── Procfile              # Configuração Railway
├── runtime.txt           # Versão Python
├── README.md             # Este arquivo
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos personalizados
│   └── js/
│       └── script.js     # JavaScript principal
└── templates/            # Templates HTML
    ├── base.html         # Template base
    ├── index.html        # Página principal (clientes)
    ├── no_list.html      # Página sem lista ativa
    └── admin/            # Templates administrativos
        ├── base.html     # Base admin
        ├── login.html    # Login admin
        ├── dashboard.html # Dashboard
        ├── products.html # Gestão produtos
        ├── reports.html  # Relatórios
        └── ...
```

## 🔧 Configurações Importantes

### Banco de Dados
- **Desenvolvimento:** SQLite (arquivo local)
- **Produção:** SQLite (gerenciado pelo Railway)
- **Backup:** Dados são persistidos automaticamente

### Segurança
- Senhas são criptografadas (hash)
- Sessões seguras com chave secreta
- Validação de dados de entrada

### Performance
- Assets otimizados (CSS/JS minificados)
- Consultas de banco otimizadas
- Cache de templates

## 📊 Como Funciona o Fluxo

1. **Mario cria lista semanal** no painel admin
2. **Lista fica ativa** para receber pedidos
3. **Clientes acessam** e fazem pedidos
4. **Pedidos são enviados** via WhatsApp para Mario
5. **Sistema salva** todos os pedidos no banco
6. **Mario pode gerar relatórios** e listas de compras
7. **Mario encerra** a lista quando necessário

## 🆘 Suporte

### Problemas Comuns

**Erro de banco de dados:**
- Verifique se o arquivo `hortifruti.db` tem permissões de escrita

**WhatsApp não abre:**
- Verifique se o número está correto no código
- Teste em dispositivos diferentes

**Login admin não funciona:**
- Usuário: `mario`
- Senha: `3943`
- Verifique se não há espaços extras

### Contato
Para suporte técnico, entre em contato através do GitHub Issues.

## 📄 Licença

Este projeto foi desenvolvido especificamente para Mario - Em Casa Hortifruti.

---

**Desenvolvido com ❤️ para facilitar a vida do agricultor e seus clientes!**
