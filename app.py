import os
import json
import random
import secrets
import threading
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Flask Configuration
app = Flask(__name__)
app.secret_key = 'mk_sniper_permanent_secret_key_07043'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Database Files
USERS_FILE = 'users.json'
KEYS_FILE = 'access_keys.json'
CONTENT_FILE = 'content.json'

# Helper Functions for File I/O
def load_data(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_data(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# Automatic Admin Provisioning
def sync_admin():
    admin_email = "kabirolamide07043@gmail.com"
    admin_password = os.environ.get("ADMIN_PASSWORD", "AdminPass123!")
    users = load_data(USERS_FILE)
    
    admin = next((u for u in users if u.get('email') == admin_email), None)
    if not admin:
        users.append({
            "username": "Admin",
            "email": admin_email,
            "password": generate_password_hash(admin_password),
            "subscribed": True,
            "expiry_date": (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d"),
            "telegram_id": None
        })
        save_data(USERS_FILE, users)
        print("[INFO] Admin account auto-created.")

sync_admin()

# Permanent Session Hook
@app.before_request
def make_session_permanent():
    session.permanent = True

# Telegram Bot Integration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8890005372:AAHrbrMdHc6KqiyV30KoDNwPf5-IzcngQpQ")
bot_started = False

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    welcome_text = (
        f"🎯 *MK SNIPER BOT v47.0 VIP ACCESS*\n\n"
        f"Your Telegram ID: `{user_id}`\n\n"
        f"1️⃣ Link this ID in your Web Dashboard under Profile.\n"
        f"2️⃣ Enter your key (e.g. `MK-XXXXXX`) below to activate instant access on both Web & Telegram."
    )
    await context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode='Markdown')

async def handle_key_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = str(update.effective_user.id)
    
    if text.startswith("MK-"):
        keys = load_data(KEYS_FILE)
        key_obj = next((k for k in keys if k.get('key') == text and not k.get('used', False)), None)
        
        if key_obj:
            days = int(key_obj.get('duration', 30))
            key_obj['used'] = True
            key_obj['used_by_telegram'] = user_id
            save_data(KEYS_FILE, keys)
            
            users = load_data(USERS_FILE)
            user_found = False
            expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            
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
                    "password": generate_password_hash("telegram_user"),
                    "subscribed": True,
                    "expiry_date": expiry,
                    "telegram_id": user_id
                })
            save_data(USERS_FILE, users)
            await update.message.reply_text(f"✅ Key Activated Successfully!\nDuration: {days} Days.\nWeb & Telegram unlocked.")
        else:
            await update.message.reply_text("❌ Invalid or already redeemed key.")
    else:
        await update.message.reply_text("Send your subscription key starting with `MK-` to unlock access.")

def run_tg_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start_cmd))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_key_msg))
        application.run_polling(stop_signals=None)
    except Exception as e:
        print(f"[ERROR] Telegram Bot error: {e}")

@app.before_request
def start_bot_thread():
    global bot_started
    if not bot_started and TELEGRAM_BOT_TOKEN:
        bot_started = True
        t = threading.Thread(target=run_tg_bot, daemon=True)
        t.start()

# Web Routes
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

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
        return render_template('login.html', error="Invalid email or password")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    users = load_data(USERS_FILE)
    if any(u.get('email', '').lower() == email for u in users):
        return render_template('login.html', error="Email already registered")
    
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
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    users = load_data(USERS_FILE)
    current_user = next((u for u in users if u.get('email') == session['user'].get('email')), session['user'])
    session['user'] = current_user
    
    content = load_data(CONTENT_FILE)
    return render_template('dashboard.html', user=current_user, content=content)

@app.route('/signals')
def signals():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    users = load_data(USERS_FILE)
    current_user = next((u for u in users if u.get('email') == session['user'].get('email')), session['user'])
    
    if not current_user.get('subscribed', False):
        return redirect(url_for('subscribe'))
    
    return render_template('signals.html', user=current_user)

@app.route('/subscribe')
def subscribe():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('subscribe.html')

@app.route('/admin')
def admin_panel():
    if 'user' not in session or session['user'].get('email') != 'kabirolamide07043@gmail.com':
        return redirect(url_for('login'))
    
    users = load_data(USERS_FILE)
    keys = load_data(KEYS_FILE)
    content = load_data(CONTENT_FILE)
    
    stats = {
        "total_users": len(users),
        "active_keys": len([k for k in keys if not k.get('used', False)]),
        "total_videos": len(content)
    }
    return render_template('admin.html', users=users, keys=keys, content=content, stats=stats)

@app.route('/admin/generate_key', methods=['POST'])
def generate_key():
    if 'user' not in session or session['user'].get('email') != 'kabirolamide07043@gmail.com':
        return jsonify({"error": "Unauthorized"}), 403
    
    duration = int(request.form.get('duration', 30))
    raw_key = f"MK-{secrets.token_hex(4).upper()}"
    
    keys = load_data(KEYS_FILE)
    keys.append({
        "key": raw_key,
        "duration": duration,
        "used": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(KEYS_FILE, keys)
    return redirect(url_for('admin_panel'))

@app.route('/admin/add_content', methods=['POST'])
def add_content():
    if 'user' not in session or session['user'].get('email') != 'kabirolamide07043@gmail.com':
        return jsonify({"error": "Unauthorized"}), 403
    
    title = request.form.get('title')
    raw_url = request.form.get('url')
    
    # Format YouTube embed links cleanly
    embed_url = raw_url
    if "watch?v=" in raw_url:
        embed_url = raw_url.replace("watch?v=", "embed/")
    elif "youtu.be/" in raw_url:
        embed_url = raw_url.replace("youtu.be/", "youtube.com/embed/")
        
    content = load_data(CONTENT_FILE)
    content.append({
        "id": secrets.token_hex(4),
        "title": title,
        "url": embed_url,
        "type": "video"
    })
    save_data(CONTENT_FILE, content)
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    if 'user' not in session or session['user'].get('email') != 'kabirolamide07043@gmail.com':
        return jsonify({"error": "Unauthorized"}), 403
    
    email_to_del = request.form.get('email')
    users = load_data(USERS_FILE)
    users = [u for u in users if u.get('email') != email_to_del]
    save_data(USERS_FILE, users)
    return redirect(url_for('admin_panel'))

@app.route('/api/redeem_key', methods=['POST'])
def redeem_key():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
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
        return jsonify({"success": True, "message": "Key redeemed successfully!"})
    return jsonify({"success": False, "message": "Invalid or expired key."})

@app.route('/api/generate_signal', methods=['POST'])
def generate_signal():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json or {}
    pair = data.get('pair', 'EUR/USD (OTC)')
    duration = data.get('duration', '1m')
    
    action = random.choice(["CALL (BUY) 📈", "PUT (SELL) 📉"])
    accuracy = round(random.uniform(92.5, 99.1), 1)
    entry_time = (datetime.now() + timedelta(seconds=5)).strftime("%H:%M:%S")
    
    return jsonify({
        "status": "success",
        "pair": pair,
        "duration": duration,
        "action": action,
        "accuracy": f"{accuracy}%",
        "entry_time": entry_time
    })

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

flask_app = app

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
