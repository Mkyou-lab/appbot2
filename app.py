import os
import json
import random
import secrets
import threading
import asyncio
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

app = Flask(__name__)
app.secret_key = 'mk_sniper_permanent_secret_key_07043'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

USERS_FILE = 'users.json'
KEYS_FILE = 'access_keys.json'
CONTENT_FILE = 'content.json'
ADMIN_EMAIL = "kabirolamide07043@gmail.com"

# Safely load JSON files
def load_data(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            if not text:
                return []
            data = json.loads(text)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[WARN] Error loading {filepath}: {e}")
        return []

def save_data(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Error saving {filepath}: {e}")

# Inject 'user' variable into ALL templates globally to prevent UndefinedError
@app.context_processor
def inject_user():
    current_user = None
    if 'user' in session:
        users = load_data(USERS_FILE)
        current_user = next((u for u in users if u.get('email') == session['user'].get('email')), session['user'])
    return dict(user=current_user)

# Print any crash errors directly to the screen for easy fixing
@app.errorhandler(500)
def internal_error(e):
    tb = traceback.format_exc()
    return f"<div style='background:#111;color:#ff5555;padding:20px;'><pre>{tb}</pre></div>", 500

# Auto-Create Admin Account on Startup
def sync_admin():
    admin_password = os.environ.get("ADMIN_PASSWORD", "AdminPass123!")
    users = load_data(USERS_FILE)
    admin = next((u for u in users if u.get('email') == ADMIN_EMAIL), None)
    if not admin:
        users.append({
            "username": "MK_OWNER",
            "email": ADMIN_EMAIL,
            "password": generate_password_hash(admin_password),
            "subscribed": True,
            "expiry_date": (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d"),
            "telegram_id": None
        })
        save_data(USERS_FILE, users)

sync_admin()

@app.before_request
def make_session_permanent():
    session.permanent = True

# ----------------- TELEGRAM BOT LOGIC -----------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8890005372:AAHrbrMdHc6KqiyV30KoDNwPf5-IzcngQpQ")
bot_started = False

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = (f"🎯 *MK SNIPER BOT v47.0*\n\nYour Telegram ID: `{user_id}`\n\n"
            f"Send a valid access key starting with `MK-` to unlock VIP Signals.")
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')

async def handle_key_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = str(update.effective_user.id)
    
    if text.startswith("MK-"):
        keys = load_data(KEYS_FILE)
        key_obj = next((k for k in keys if k.get('key') == text and not k.get('used', False)), None)
        
        if key_obj:
            days = int(key_obj.get('duration', 30))
            key_obj['used'] = True
            save_data(KEYS_FILE, keys)
            
            users = load_data(USERS_FILE)
            expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            
            user_found = False
            for u in users:
                if str(u.get('telegram_id')) == user_id:
                    u['subscribed'] = True
                    u['expiry_date'] = expiry
                    user_found = True
                    break
            
            if not user_found:
                users.append({
                    "username": f"TG_User_{user_id}",
                    "email": f"tg_{user_id}@mksniper.com",
                    "password": generate_password_hash("telegram"),
                    "subscribed": True,
                    "expiry_date": expiry,
                    "telegram_id": user_id
                })
            save_data(USERS_FILE, users)
            await update.message.reply_text(f"✅ Key Activated Successfully!\nDuration: {days} Days.")
        else:
            await update.message.reply_text("❌ Invalid or already redeemed key.")

def run_tg_bot():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start_cmd))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_key_msg))
        application.run_polling(stop_signals=None)
    except Exception as e:
        print(f"[ERROR] Bot crash: {e}")

@app.before_request
def start_bot_thread():
    global bot_started
    if not bot_started and TELEGRAM_BOT_TOKEN:
        bot_started = True
        threading.Thread(target=run_tg_bot, daemon=True).start()

# ----------------- WEB ROUTES -----------------
@app.route('/')
def index():
    if 'user' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        users = load_data(USERS_FILE)
        user = next((u for u in users if u.get('email', '').lower() == email), None)
        
        if user and check_password_hash(user.get('password', ''), password):
            session['user'] = user
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    users = load_data(USERS_FILE)
    if any(u.get('email', '').lower() == email for u in users):
        return render_template('login.html', error="Email is already in use.")
    
    new_user = {
        "username": username,
        "email": email,
        "password": generate_password_hash(password),
        "subscribed": False,
        "expiry_date": None,
        "telegram_id": None
    }
    users.append(new_user)
    save_data(USERS_FILE, users)
    session['user'] = new_user
    print(f"[NEW REGISTRATION] User: {username}, Email: {email}") # Log for admin
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    content = load_data(CONTENT_FILE)
    return render_template('dashboard.html', content=content)

@app.route('/signals')
def signals():
    if 'user' not in session: return redirect(url_for('login'))
    users = load_data(USERS_FILE)
    current_user = next((u for u in users if u.get('email') == session['user'].get('email')), session['user'])
    if not current_user.get('subscribed', False):
        return redirect(url_for('dashboard'))
    return render_template('signals.html')

@app.route('/admin')
def admin_panel():
    if 'user' not in session or session['user'].get('email') != ADMIN_EMAIL:
        return redirect(url_for('login'))
    users = load_data(USERS_FILE)
    keys = load_data(KEYS_FILE)
    content = load_data(CONTENT_FILE)
    
    stats = {
        "total_users": len(users),
        "active_keys": len([k for k in keys if not k.get('used', False)]),
        "videos": len(content)
    }
    return render_template('admin.html', users=users, keys=keys, stats=stats)

@app.route('/admin/generate_key', methods=['POST'])
def generate_key():
    if 'user' not in session or session['user'].get('email') != ADMIN_EMAIL: return "Unauthorized", 403
    duration = int(request.form.get('duration', 30))
    keys = load_data(KEYS_FILE)
    keys.append({
        "key": f"MK-{secrets.token_hex(4).upper()}",
        "duration": duration,
        "used": False
    })
    save_data(KEYS_FILE, keys)
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    if 'user' not in session or session['user'].get('email') != ADMIN_EMAIL: return "Unauthorized", 403
    email = request.form.get('email')
    users = [u for u in load_data(USERS_FILE) if u.get('email') != email]
    save_data(USERS_FILE, users)
    return redirect(url_for('admin_panel'))

@app.route('/api/redeem_key', methods=['POST'])
def redeem_key():
    if 'user' not in session: return jsonify({"success": False, "message": "Not logged in"})
    key_input = request.json.get('key', '').strip()
    keys = load_data(KEYS_FILE)
    key_obj = next((k for k in keys if k.get('key') == key_input and not k.get('used', False)), None)
    
    if key_obj:
        key_obj['used'] = True
        save_data(KEYS_FILE, keys)
        users = load_data(USERS_FILE)
        for u in users:
            if u.get('email') == session['user'].get('email'):
                u['subscribed'] = True
                u['expiry_date'] = (datetime.now() + timedelta(days=int(key_obj.get('duration', 30)))).strftime("%Y-%m-%d")
                session['user'] = u
                break
        save_data(USERS_FILE, users)
        return jsonify({"success": True, "message": "Key redeemed!"})
    return jsonify({"success": False, "message": "Invalid key."})

@app.route('/api/generate_signal', methods=['POST'])
def generate_signal():
    if 'user' not in session: return "Unauthorized", 401
    data = request.json or {}
    return jsonify({
        "pair": data.get('pair', 'EUR/USD (OTC)'),
        "action": random.choice(["CALL (BUY) 📈", "PUT (SELL) 📉"]),
        "accuracy": f"{round(random.uniform(92.5, 99.1), 1)}%",
        "entry_time": (datetime.now() + timedelta(seconds=5)).strftime("%H:%M:%S")
    })

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

flask_app = app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
