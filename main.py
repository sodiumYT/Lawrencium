from flask import Flask, render_template_string, request, session, redirect, url_for
import datetime
import sqlite3
import hashlib
from mnemonic import Mnemonic  # Импортируем библиотеку для генерации сид-фразы

app = Flask(__name__)
app.secret_key = 'idk_but_sod1um_is_cool'

transactions = []

mnemo = Mnemonic("english")  # Инициализируем объект для генерации сид-фраз

def hash_phrase(phrase):
    """Хэширует сид-фразу с помощью SHA256"""
    return hashlib.sha256(phrase.encode()).hexdigest()

def get_user(public_key):
    """Получает информацию о пользователе из базы данных"""
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE public_key = ?", (public_key,))
    user = cur.fetchone()
    con.close()
    return user

def create_user(public_key, balance=0.0):
    """Создаёт нового пользователя в базе данных"""
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    cur.execute("INSERT INTO users (public_key, balance) VALUES (?, ?)", (public_key, balance))
    con.commit()
    con.close()

def update_balance(public_key, amount):
    """Обновляет баланс пользователя в базе данных"""
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    cur.execute("UPDATE users SET balance = ? WHERE public_key = ?", (amount, public_key))
    con.commit()
    con.close()

@app.route("/register")
def register_page():
    """Страница регистрации"""
    return """
<html>
    <head>
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        <div class="main">
            <h1>Register</h1>
            <form method="POST" action="/register">
                <button type="submit">Generate Seed Phrase & Register</button>
            </form>
            <p><a href="/login" style="color: #FFC168;">Login</a></p>
        </div>
    </body>
</html>"""

@app.route("/register", methods=["POST"])
def register():
    """Обрабатывает регистрацию нового пользователя"""
    # Генерация новой сид-фразы
    phrase = mnemo.generate(strength=128)  # 12-словая сид-фраза
    public_key = hash_phrase(phrase)
    if not get_user(public_key):
        create_user(public_key)
        session['public_key'] = public_key
        session['seed_phrase'] = phrase  # Храним сид-фразу в сессии для отображения
        return redirect(url_for('show_seed'))
    return "Registration failed or user already exists"

@app.route("/show_seed")
def show_seed():
    """Отображение сгенерированной сид-фразы для пользователя после регистрации"""
    if 'seed_phrase' in session:
        phrase = session['seed_phrase']
        return f"""
<html>
    <head>
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        <div class="main">
            <h1>Save your seed phrase</h1>
            <p>Your seed phrase: <strong>{phrase}</strong></p>
            <p>Make sure to save this phrase securely. You will need it to access your account.</p>
            <a href="/">Continue</a>
        </div>
    </body>
</html>"""
    return redirect(url_for('register'))

@app.route("/login")
def login_page():
    """Страница входа в систему"""
    return """
<html>
    <head>
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        <div class="main">
            <h1>Login</h1>
            <form method="POST" action="/login">
                <input type="text" name="phrase" placeholder="Enter your seed phrase" required>
                <button type="submit">Login</button>
            </form>
            <p><a href="/register" style="color: #FFC168;">Register</a></p>
        </div>
    </body>
</html>"""

@app.route("/login", methods=["POST"])
def login():
    """Обрабатывает вход в систему"""
    phrase = request.form.get("phrase")
    if phrase:
        public_key = hash_phrase(phrase)
        if get_user(public_key):
            session['public_key'] = public_key
            return redirect(url_for('index'))
    return "Login failed"

@app.route("/logout")
def logout():
    """Выход из системы"""
    session.pop('public_key', None)
    return redirect(url_for('login_page'))

@app.route("/add")
def addFunds():
    """Добавляет средства на баланс пользователя"""
    if 'public_key' not in session:
        return redirect(url_for('login_page'))
    
    try:
        amount = float(request.args.get('amount'))
        public_key = session['public_key']
        user = get_user(public_key)
        if user:
            balance = user[1] + amount
            update_balance(public_key, balance)
    except (ValueError, TypeError):
        pass
    return redirect("/")

@app.route("/send")
def sendFunds():
    """Отправляет средства другому пользователю"""
    if 'public_key' not in session:
        return redirect(url_for('login_page'))

    try:
        recipient_key = request.args.get('public_key')
        amount = float(request.args.get('amount'))
        sender_key = session['public_key']
        if amount <= get_user(sender_key)[1]:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            transactions.append(f"<div class='transaction'><strong>To:</strong> {recipient_key}<br><strong>Amount:</strong> {amount} LWC<br><strong>Date:</strong> {timestamp}</div><br>-----------------<br><br>")
            sender_balance = get_user(sender_key)[1] - amount
            update_balance(sender_key, sender_balance)
            recipient_user = get_user(recipient_key)
            if recipient_user:
                recipient_balance = recipient_user[1] + amount
                update_balance(recipient_key, recipient_balance)
    except (ValueError, TypeError):
        pass
    return redirect("/")

@app.route("/")
def index():
    """Отображает главную страницу с балансом и транзакциями"""
    if 'public_key' not in session:
        return redirect(url_for('login_page'))

    public_key = session['public_key']
    user = get_user(public_key)
    if user:
        balance = user[1]
    
    transactions_html = "<div class='transaction-list'>" + "".join(transactions) + "</div>" if transactions else "No transactions yet."
    
    return f"""
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lawrencium Wallet</title>
        <link rel="icon" href="/static/logo.ico">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        <div class="main">
            <img src="/static/logo.png" alt="Wallet Logo">
            <h2>{balance} LWC</h2>
            <div class="actions">
                <div class="icon-item" onclick="showReceive()">
                    <div class="icon"><i class="fas fa-arrow-down"></i></div>
                    <div class="icon-text">Receive</div>
                </div>
                <div class="icon-item" onclick="showSendForm()">
                    <div class="icon"><i class="fas fa-arrow-up"></i></div>
                    <div class="icon-text">Send</div>
                </div>
            </div>
            <div class="transactions">{transactions_html}</div>
            <a href="/logout">Logout</a>
        </div>

        <div id="sendForm" class="send-form">
            <h3>Send LWC</h3>
            <p>Make sure you send funds to the correct address. Otherwise, the funds may be lost!</p>
            <form action="/send" method="GET">
                <input type="text" name="public_key" placeholder="Public Key" required>
                <input type="number" step="0.01" name="amount" placeholder="Amount" required>
                <button type="submit">Send</button>
            </form>
            <button onclick="closeSendForm()">Cancel</button>
        </div>

        <div id="receiveInfo" class="receive-info">
            <h3>Receive LWC</h3>
            <p>Send LWC to this address to receive them.</p>
            <input type="text" id="publicAddress" value="{public_key}" readonly>
            <button onclick="copyAddress()">Copy</button>
            <button onclick="closeReceiveInfo()">Close</button>
        </div>

        <script>
            function showSendForm() {{
                document.getElementById('sendForm').classList.add('show');
                document.getElementById('receiveInfo').classList.remove('show');
            }}

            function closeSendForm() {{
                document.getElementById('sendForm').classList.remove('show');
            }}

            function showReceive() {{
                document.getElementById('receiveInfo').classList.add('show');
                document.getElementById('sendForm').classList.remove('show');
            }}

            function closeReceiveInfo() {{
                document.getElementById('receiveInfo').classList.remove('show');
            }}

            function copyAddress() {{
                const copyText = document.getElementById('publicAddress');
                copyText.select();
                copyText.setSelectionRange(0, 99999);
                navigator.clipboard.writeText(copyText.value);
            }}
    </script>
</body>
</html>"""

if __name__ == '__main__':
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            public_key TEXT PRIMARY KEY,
            balance FLOAT NOT NULL
        )
    ''')
    con.commit()
    con.close()
    app.run(debug=True)