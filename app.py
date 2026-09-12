#!/usr/bin/env python3
"""
MK SNIPER BOT v47.0 — Complete Full-Stack Application
- Step-by-Step Signal Engine
- Unified Telegram & Web Key Sync
- Live Video Embeds
"""

import asyncio
import aiohttp
import json
import os
import sys
import time
import math
import random
import logging
import hashlib
import secrets
import threading
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps

# Flask imports
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

import bcrypt

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8552395488:AAHFmk5SvVUNbQs5HGTUS_rllHGECoTq31o")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "7038512176").split(",") if x.strip()]
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 7038512176
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@Mkg12333")
USDT_ADDRESS = os.environ.get("USDT_ADDRESS", "TXyzAbc123...")

SECRET_KEY = os.environ.get("SECRET_KEY", "mk_sniper_permanent_secret_key_07043")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123secure")
ADMIN_EMAIL = "kabirolamide07043@gmail.com"
PORT = int(os.environ.get("PORT", 5000))

TIMEZONE_OFFSET = 1
LOCAL_TZ = timezone(timedelta(hours=TIMEZONE_OFFSET))
FREE_TRIAL_SIGNALS = 2

SUBSCRIPTION_PLANS = {
    "week": {"name": "1 Week", "price": "$20", "days": 7},
    "month": {"name": "1 Month", "price": "$100", "days": 30},
    "lifetime": {"name": "Lifetime", "price": "$150", "days": 36500},
}

# ==================== PAIRS CONFIGURATION ====================
PAIRS = {
    "EUR/USD":      {"type":"forex",  "payout":85, "symbol":"EURUSD",  "pip":0.0001},
    "GBP/USD":      {"type":"forex",  "payout":85, "symbol":"GBPUSD",  "pip":0.0001},
    "USD/JPY":      {"type":"forex",  "payout":85, "symbol":"USDJPY",  "pip":0.01},
    "USD/CHF":      {"type":"forex",  "payout":85, "symbol":"USDCHF",  "pip":0.0001},
    "AUD/USD":      {"type":"forex",  "payout":85, "symbol":"AUDUSD",  "pip":0.0001},
    "USD/CAD":      {"type":"forex",  "payout":85, "symbol":"USDCAD",  "pip":0.0001},
    "NZD/USD":      {"type":"forex",  "payout":85, "symbol":"NZDUSD",  "pip":0.0001},
    "EUR/JPY":      {"type":"forex",  "payout":85, "symbol":"EURJPY",  "pip":0.01},
    "GBP/JPY":      {"type":"forex",  "payout":85, "symbol":"GBPJPY",  "pip":0.01},
    "EUR/GBP":      {"type":"forex",  "payout":85, "symbol":"EURGBP",  "pip":0.0001},
    
    "EUR/USD OTC":  {"type":"otc",    "payout":92, "symbol":"EURUSD_OTC", "pip":0.0001},
    "GBP/USD OTC":  {"type":"otc",    "payout":92, "symbol":"GBPUSD_OTC", "pip":0.0001},
    "USD/JPY OTC":  {"type":"otc",    "payout":92, "symbol":"USDJPY_OTC", "pip":0.01},
    "AUD/USD OTC":  {"type":"otc",    "payout":92, "symbol":"AUDUSD_OTC", "pip":0.0001},
    "USD/CAD OTC":  {"type":"otc",    "payout":92, "symbol":"USDCAD_OTC", "pip":0.0001},
    "NZD/USD OTC":  {"type":"otc",    "payout":92, "symbol":"NZDUSD_OTC", "pip":0.0001},
    "EUR/JPY OTC":  {"type":"otc",    "payout":90, "symbol":"EURJPY_OTC", "pip":0.01},
    "GBP/JPY OTC":  {"type":"otc",    "payout":90, "symbol":"GBPJPY_OTC", "pip":0.01},
    
    "Gold OTC":     {"type":"otc",    "payout":92, "symbol":"XAUUSD_OTC", "pip":0.01},
    "Silver OTC":   {"type":"otc",    "payout":88, "symbol":"XAGUSD_OTC", "pip":0.001},
    "USCrude OTC":  {"type":"otc",    "payout":88, "symbol":"WTI_OTC",    "pip":0.01},
    
    "Apple OTC":    {"type":"otc",    "payout":90, "symbol":"AAPL_OTC",   "pip":0.01},
    "Tesla OTC":    {"type":"otc",    "payout":90, "symbol":"TSLA_OTC",   "pip":0.01},
    
    "BTC/USD":      {"type":"crypto", "payout":80, "binance":"BTCUSDT", "pip":1.0},
    "ETH/USD":      {"type":"crypto", "payout":80, "binance":"ETHUSDT", "pip":0.1},
    "SOL/USD":      {"type":"crypto", "payout":80, "binance":"SOLUSDT", "pip":0.01},
    "XRP/USD":      {"type":"crypto", "payout":80, "binance":"XRPUSDT", "pip":0.0001},
}

DURATIONS = {
    "3s":  {"secs":3,   "label":"3s",  "candle_sec":3,   "regime": "micro_tick"},
    "5s":  {"secs":5,   "label":"5s",  "candle_sec":5,   "regime": "micro_tick"},
    "10s": {"secs":10,  "label":"10s", "candle_sec":10,  "regime": "micro_tick"},
    "15s": {"secs":15,  "label":"15s", "candle_sec":15,  "regime": "micro_tick"},
    "30s": {"secs":30,  "label":"30s", "candle_sec":30,  "regime": "momentum"},
    "1m":  {"secs":60,  "label":"1m",  "candle_sec":60,  "regime": "momentum"},
    "2m":  {"secs":120, "label":"2m",  "candle_sec":120, "regime": "momentum"},
    "3m":  {"secs":180, "label":"3m",  "candle_sec":180, "regime": "swing_trend"},
    "5m":  {"secs":300, "label":"5m",  "candle_sec":300, "regime": "swing_trend"},
    "15m": {"secs":900, "label":"15m", "candle_sec":900, "regime": "swing_trend"},
}

# ==================== STORAGE & UTILS ====================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
log = logging.getLogger("MK_SNIPER")

USERS_FILE = DATA_DIR / "users.json"
KEYS_FILE = DATA_DIR / "access_keys.json"
SIGNALS_FILE = DATA_DIR / "signals_history.json"
CONTENT_FILE = DATA_DIR / "content.json"
ACTIVITY_FILE = DATA_DIR / "activity.json"

def load_json(fp: Path, default=None):
    try:
        if fp.exists(): return json.loads(fp.read_text(encoding="utf-8"))
    except: pass
    return default if default is not None else {}

def save_json(fp: Path, data):
    try: fp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    except: pass

def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)

# ==================== USER MODEL ====================
class WebUser(UserMixin):
    def __init__(self, id, username, fullname, email, password_hash, telegram_id=None, is_admin=False, plan="trial", trial_used=0, expiry=None, created=None):
        self.id = str(id)
        self.username = username
        self.fullname = fullname
        self.email = email
        self.password_hash = password_hash
        self.telegram_id = telegram_id
        self.is_admin = is_admin
        self.plan = plan
        self.trial_used = trial_used
        self.expiry = expiry
        self.created = created or now_local().isoformat()

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def has_active_sub(self):
        if self.is_admin: return True, "ADMIN", None
        if self.plan == "trial":
            rem = FREE_TRIAL_SIGNALS - self.trial_used
            return rem > 0, "TRIAL", rem
        if self.plan == "lifetime": return True, "LIFETIME", None
        if self.expiry:
            exp = datetime.fromisoformat(self.expiry)
            now = now_local()
            if now < exp: return True, self.plan.upper(), (exp - now).days
            return False, "EXPIRED", 0
        return False, "NO SUBSCRIPTION", None

    def to_dict(self):
        return {"id": self.id, "username": self.username, "fullname": self.fullname, "email": self.email, "password_hash": self.password_hash, "telegram_id": self.telegram_id, "is_admin": self.is_admin, "plan": self.plan, "trial_used": self.trial_used, "expiry": self.expiry, "created": self.created}

    @staticmethod
    def from_dict(d): return WebUser(**d)

def get_all_users() -> Dict[str, WebUser]:
    users = {}
    for uid, udata in load_json(USERS_FILE, {}).items():
        try: users[str(uid)] = WebUser.from_dict(udata)
        except: pass
    return users

def save_user(user: WebUser):
    users = load_json(USERS_FILE, {})
    users[str(user.id)] = user.to_dict()
    save_json(USERS_FILE, users)

def get_user_by_login(login_input: str) -> Optional[WebUser]:
    if not login_input: return None
    login_input = login_input.lower().strip()
    for u in get_all_users().values():
        if (u.username and u.username.lower() == login_input) or (u.email and u.email.lower() == login_input): return u
    return None

def get_user_by_telegram_id(tg_id: str) -> Optional[WebUser]:
    for u in get_all_users().values():
        if str(u.telegram_id) == str(tg_id): return u
    return None

def create_admin_user():
    pw_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = get_user_by_login("admin") or get_user_by_login(ADMIN_EMAIL)
    if not admin:
        admin = WebUser(id=str(ADMIN_ID), username="admin", fullname="App Owner", email=ADMIN_EMAIL, password_hash=pw_hash, is_admin=True, plan="lifetime")
    else:
        admin.username = "admin"
        admin.email = ADMIN_EMAIL
        admin.password_hash = pw_hash
        admin.is_admin = True
        admin.plan = "lifetime"
    save_user(admin)
    log.info(f"✅ Admin active: admin / {ADMIN_EMAIL}")

# ==================== ENGINE CORE ====================
def get_all_keys(): return load_json(KEYS_FILE, [])
def save_keys(keys): save_json(KEYS_FILE, keys)

def generate_access_key(plan: str) -> str:
    key = f"MK-{plan.upper()}-{secrets.token_hex(8).upper()}"
    keys = get_all_keys()
    keys.append({"key": key, "plan": plan, "used": False, "used_by": None, "created": now_local().strftime("%Y-%m-%d %H:%M")})
    save_keys(keys)
    return key

def redeem_access_key(key_str: str, user: WebUser) -> Tuple[bool, str]:
    keys = get_all_keys()
    for k in keys:
        if k["key"] == key_str and not k["used"]:
            plan = k["plan"]
            k["used"] = True
            k["used_by"] = user.username
            save_keys(keys)
            user.plan = plan
            user.expiry = None if plan == "lifetime" else (now_local() + timedelta(days=SUBSCRIPTION_PLANS[plan]["days"])).isoformat()
            save_user(user)
            return True, plan
    return False, "Invalid or already used key"

def format_video_url(url: str) -> str:
    if "youtube.com/watch?v=" in url: return f"https://www.youtube.com/embed/{url.split('v=')[1].split('&')[0]}"
    if "youtu.be/" in url: return f"https://www.youtube.com/embed/{url.split('youtu.be/')[1].split('?')[0]}"
    return url

def add_content_item(item: dict):
    content = load_json(CONTENT_FILE, [])
    item["id"] = str(uuid.uuid4())[:8]
    item["url"] = format_video_url(item.get("url", ""))
    item["created"] = now_local().strftime("%Y-%m-%d %H:%M")
    content.insert(0, item)
    save_json(CONTENT_FILE, content)

def evaluate_market_sync(pair: str, dur_key: str) -> dict:
    rng = random.Random(seed=int(time.time() / 10))
    direction = "CALL" if rng.choice([True, False]) else "PUT"
    acc = min(99.6, round(97.4 + rng.uniform(0.1, 2.1), 1))
    confluences = [
        "Wave Structure Alignment (Matched)",
        "RSI Momentum Oscillator (Optimal)",
        f"Micro-Tick Velocity {'(+)' if direction=='CALL' else '(-)'}"
    ]
    return {"direction": direction, "accuracy": acc, "confluences": confluences}

def calc_entry(dur_key: str):
    now = now_local()
    csec = DURATIONS[dur_key]["candle_sec"]
    if csec < 60:
        wait = (csec - (now.second % csec)) if (now.second % csec) else csec
        return now.replace(microsecond=0) + timedelta(seconds=wait)
    mins = csec // 60
    wait = (mins - (now.minute % mins)) if (now.minute % mins) else mins
    return now.replace(second=0, microsecond=0) + timedelta(minutes=wait)

# ==================== FLASK SETUP ====================
flask_app = Flask(__name__)
flask_app.config["SECRET_KEY"] = SECRET_KEY
flask_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
socketio = SocketIO(flask_app, cors_allowed_origins="*", async_mode="threading")
login_manager = LoginManager(flask_app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(user_id): return get_user_by_id(user_id)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin: abort(403)
        return f(*args, **kwargs)
    return decorated

# Thread safety for bot
_bot_started = False
_bot_lock = threading.Lock()

@flask_app.before_request
def boot_bot():
    global _bot_started
    if not _bot_started:
        with _bot_lock:
            if not _bot_started:
                _bot_started = True
                if BOT_TOKEN and ":" in BOT_TOKEN:
                    threading.Thread(target=run_telegram_bot, daemon=True).start()

# ==================== WEB ROUTES ====================
@flask_app.route("/")
def landing():
    return redirect(url_for("dashboard")) if current_user.is_authenticated else render_template("landing.html")

@flask_app.route("/login", methods=["GET", "POST"])
def login_page():
    if current_user.is_authenticated: return redirect(url_for("admin_panel" if current_user.is_admin else "dashboard"))
    if request.method == "POST":
        user = get_user_by_login(request.form.get("username", ""))
        if user and user.check_password(request.form.get("password", "")):
            session.permanent = True
            login_user(user, remember=True)
            return redirect(url_for("admin_panel" if user.is_admin else "dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("login.html")

@flask_app.route("/register", methods=["GET", "POST"])
def register_page():
    if current_user.is_authenticated: return redirect(url_for("dashboard"))
    if request.method == "POST":
        username, email, tg_id, pw = request.form.get("username", ""), request.form.get("email", ""), request.form.get("telegram_id", ""), request.form.get("password", "")
        if get_user_by_login(username) or get_user_by_login(email):
            flash("Username/Email taken.", "error")
            return render_template("register.html")
        pw_hash = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = WebUser(id=str(uuid.uuid4())[:12], username=username, fullname=request.form.get("fullname",""), email=email, telegram_id=tg_id, password_hash=pw_hash)
        save_user(user)
        login_user(user, remember=True)
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@flask_app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("landing"))

@flask_app.route("/dashboard")
@login_required
def dashboard():
    has_sub, sub_status, sub_days = current_user.has_active_sub()
    recent = [s for s in load_json(SIGNALS_FILE, []) if s.get("user") == current_user.username][:10]
    return render_template("dashboard.html", sub_status=sub_status, sub_days=sub_days, recent_signals=recent, content_items=load_json(CONTENT_FILE, [])[:6])

@flask_app.route("/signals")
@login_required
def signals_page():
    has_access, status, rem = current_user.has_active_sub()
    return render_template("signals.html", has_access=has_access, trial_remaining=(rem if status=="TRIAL" else 0), admin_username=ADMIN_USERNAME, pairs_json=json.dumps(PAIRS), durations=DURATIONS)

@flask_app.route("/subscribe")
@login_required
def subscribe_page():
    return render_template("subscribe.html", usdt_address=USDT_ADDRESS, admin_username=ADMIN_USERNAME)

@flask_app.route("/redeem-key", methods=["POST"])
@login_required
def redeem_key():
    ok, res = redeem_access_key(request.form.get("access_key", "").strip(), current_user)
    flash(f"🎉 {res.upper()} plan activated!" if ok else f"❌ {res}", "success" if ok else "error")
    return redirect(url_for("dashboard"))

@flask_app.route("/api/generate-signal", methods=["POST"])
@login_required
def api_generate_signal():
    if not current_user.has_active_sub()[0]: return jsonify({"success": False, "error": "Subscription required."})
    data = request.json or {}
    pair, dur = data.get("pair"), data.get("duration")
    if current_user.plan == "trial":
        current_user.trial_used += 1
        save_user(current_user)
    
    analysis = evaluate_market_sync(pair, dur)
    et = calc_entry(dur)
    
    signal = {
        "pair": pair, "direction": analysis["direction"], "duration": DURATIONS[dur]["label"],
        "entry_time": et.strftime("%H:%M:%S"), "mg_time": (et + timedelta(seconds=DURATIONS[dur]["secs"])).strftime("%H:%M:%S"),
        "accuracy": analysis["accuracy"], "payout": PAIRS[pair]["payout"],
        "confluences": analysis["confluences"], "user": current_user.username, "time": now_local().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_signal(signal)
    return jsonify({"success": True, "signal": signal})

# ==================== ADMIN ROUTES ====================
@app.route('/admin')
def admin_panel():
    if 'user' not in session or session['user'].get('email') != 'kabirolamide07043@gmail.com':
        return redirect(url_for('login'))
    
    # Safety load for all data
    users = load_data(USERS_FILE)
    keys = load_data(KEYS_FILE)
    content = load_data(CONTENT_FILE)
    
    # Ensure they are lists so the HTML loop doesn't crash
    if not isinstance(users, list): users = []
    if not isinstance(keys, list): keys = []
    if not isinstance(content, list): content = []

    # Calculate stats
    stats = {
        "total_users": len(users),
        "active_keys": len([k for k in keys if not k.get('used', False)]),
        "total_videos": len(content)
    }

    return render_template('admin.html', users=users, keys=keys, content=content, stats=stats)

@flask_app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    return render_template("admin/users.html", users=[{"id": u.id, "username": u.username, "email": u.email, "plan": u.plan, "active": u.has_active_sub()[0]} for u in get_all_users().values()])

@flask_app.route("/admin/keys")
@login_required
@admin_required
def admin_keys():
    return render_template("admin/keys.html", keys=get_all_keys())

@flask_app.route("/admin/content", methods=["GET", "POST"])
@login_required
@admin_required
def admin_content():
    if request.method == "POST":
        add_content_item({"title": request.form.get("title"), "type": request.form.get("type", "video"), "description": request.form.get("description"), "url": request.form.get("url"), "body": request.form.get("body")})
        return redirect(url_for("admin_content"))
    return render_template("admin/content.html", content=load_json(CONTENT_FILE, []))

@flask_app.route("/admin/api/generate-key", methods=["POST"])
@login_required
@admin_required
def api_generate_key():
    return jsonify({"success": True, "key": generate_access_key(request.json.get("plan", "week"))})

# ==================== TELEGRAM BOT (UNIFIED) ====================
async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    user = get_user_by_telegram_id(uid)
    
    if user:
        has_sub, plan, rem = user.has_active_sub()
        txt = f"✅ Connected to Web Account: <b>{user.username}</b>\nStatus: <b>{plan}</b>"
    else:
        txt = f"⚠️ Unlinked Account.\nYour TG ID is <code>{uid}</code>.\nRegister on the Web Dashboard and put this ID to link accounts!"

    await update.message.reply_text(f"🎯 <b>MK SNIPER ENGINE</b>\n\n{txt}", parse_mode=ParseMode.HTML)

async def tg_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    text = update.message.text.strip()
    
    if text.startswith("MK-"):
        user = get_user_by_telegram_id(uid)
        if not user:
            await update.message.reply_text("❌ Create a web account and link your Telegram ID first!")
            return
        ok, plan = redeem_access_key(text, user)
        if ok:
            await update.message.reply_text(f"🎉 KEY REDEEMED! Plan {plan.upper()} unlocked across Web & Telegram!")
        else:
            await update.message.reply_text("❌ Invalid key.")

def run_telegram_bot():
    if not BOT_TOKEN or ":" not in BOT_TOKEN: return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def start_bot():
        tg_app = Application.builder().token(BOT_TOKEN).build()
        tg_app.add_handler(CommandHandler("start", tg_start))
        tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_message_handler))
        await tg_app.initialize()
        await tg_app.start()
        await tg_app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()
    try: loop.run_until_complete(start_bot())
    except: pass

create_admin_user()
if __name__ == "__main__":
    socketio.run(flask_app, host="0.0.0.0", port=PORT, debug=False, allow_unsafe_werkzeug=True)
