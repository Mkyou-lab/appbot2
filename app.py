#!/usr/bin/env python3
"""
MK SNIPER BOT v47.0 — Complete Full-Stack Application
"""

# Eventlet monkey patch removed for Railway stability (using threading)
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
import threading
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps

# Flask imports
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, abort
)
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from flask_socketio import SocketIO, emit

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import BadRequest, RetryAfter

import bcrypt

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8552395488:AAHFmk5SvVUNbQs5HGTUS_rllHGECoTq31o")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "7038512176").split(",") if x.strip()]
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 7038512176
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@Mkg12333")
USDT_ADDRESS = os.environ.get("USDT_ADDRESS", "TXyzAbc123...")

# FIXED: Hardcoded secret key so users stay logged in across app restarts!
SECRET_KEY = os.environ.get("SECRET_KEY", "mk_sniper_permanent_secret_key_07043")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123secure")
ADMIN_EMAIL = "kabirolamide07043@gmail.com"
PORT = int(os.environ.get("PORT", 5000))

TIMEZONE_OFFSET = 1
LOCAL_TZ = timezone(timedelta(hours=TIMEZONE_OFFSET))
FREE_TRIAL_SIGNALS = 2
ENTRY_STAKE = 10
MG_STAKE = 22

SUBSCRIPTION_PLANS = {
    "week": {"name": "1 Week", "price": "$20", "days": 7},
    "month": {"name": "1 Month", "price": "$100", "days": 30},
    "lifetime": {"name": "Lifetime", "price": "$150", "days": 36500},
}

# ==================== PAIRS CONFIGURATION ====================
PAIRS = {
    "EUR/USD": {"type": "forex", "payout": 85, "symbol": "EURUSD", "pip": 0.0001},
    "GBP/USD": {"type": "forex", "payout": 85, "symbol": "GBPUSD", "pip": 0.0001},
    "USD/JPY": {"type": "forex", "payout": 85, "symbol": "USDJPY", "pip": 0.01},
    "BTC/USD": {"type": "crypto", "payout": 80, "binance": "BTCUSDT", "pip": 1.0},
    "ETH/USD": {"type": "crypto", "payout": 80, "binance": "ETHUSDT", "pip": 0.1},
    "EUR/USD OTC": {"type": "otc", "payout": 92, "symbol": "EURUSD_OTC", "pip": 0.0001},
    "Gold OTC": {"type": "otc", "payout": 92, "symbol": "XAUUSD_OTC", "pip": 0.01},
}

DURATIONS = {
    "1m": {"secs": 60, "label": "1m", "candle_sec": 60, "scan_wait": 1.5, "regime": "momentum"},
    "5m": {"secs": 300, "label": "5m", "candle_sec": 300, "scan_wait": 2.5, "regime": "swing_trend"},
}

# ==================== LOGGING ====================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
log = logging.getLogger("MK_SNIPER")

# ==================== DATA PERSISTENCE ====================
USERS_FILE = DATA_DIR / "users.json"
SUBS_FILE = DATA_DIR / "subscriptions.json"
KEYS_FILE = DATA_DIR / "access_keys.json"
SIGNALS_FILE = DATA_DIR / "signals_history.json"
CONTENT_FILE = DATA_DIR / "content.json"
ACTIVITY_FILE = DATA_DIR / "activity.json"

def load_json(fp: Path, default=None):
    try:
        if fp.exists():
            return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default if default is not None else {}

def save_json(fp: Path, data):
    try:
        fp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    except Exception as e:
        log.error(f"Error saving {fp.name}: {e}")

def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)

# ==================== USER MODEL ====================
class WebUser(UserMixin):
    def __init__(self, id, username, fullname, email, password_hash,
                 telegram_id=None, is_admin=False, plan="trial",
                 trial_used=0, expiry=None, created=None):
        self.id = id
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
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def has_active_sub(self):
        if self.is_admin:
            return True, "ADMIN", None
        if self.plan == "trial":
            rem = FREE_TRIAL_SIGNALS - self.trial_used
            return rem > 0, "TRIAL", rem
        if self.plan == "lifetime":
            return True, "LIFETIME", None
        if self.expiry:
            exp = datetime.fromisoformat(self.expiry)
            now = now_local()
            if now < exp:
                return True, self.plan.upper(), (exp - now).days
            return False, "EXPIRED", 0
        return False, "NO SUBSCRIPTION", None

    def to_dict(self):
        return {
            "id": self.id, "username": self.username, "fullname": self.fullname,
            "email": self.email, "password_hash": self.password_hash,
            "telegram_id": self.telegram_id, "is_admin": self.is_admin,
            "plan": self.plan, "trial_used": self.trial_used,
            "expiry": self.expiry, "created": self.created,
        }

    @staticmethod
    def from_dict(d):
        return WebUser(**d)

def get_all_users() -> Dict[str, WebUser]:
    data = load_json(USERS_FILE, {})
    users = {}
    for uid, udata in data.items():
        try:
            users[uid] = WebUser.from_dict(udata)
        except Exception:
            pass
    return users

def save_user(user: WebUser):
    users = load_json(USERS_FILE, {})
    users[user.id] = user.to_dict()
    save_json(USERS_FILE, users)

def get_user_by_id(uid: str) -> Optional[WebUser]:
    return get_all_users().get(uid)

def get_user_by_login(login_input: str) -> Optional[WebUser]:
    """Finds a user by EITHER username OR email."""
    login_input = login_input.lower().strip()
    for u in get_all_users().values():
        if u.username.lower() == login_input or u.email.lower() == login_input:
            return u
    return None

def create_admin_user():
# ==================== FLASK APP INIT ====================
flask_app = Flask(__name__)
flask_app.config["SECRET_KEY"] = SECRET_KEY
flask_app.config["ADMIN_USERNAME"] = ADMIN_USERNAME
flask_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30) # Keep logged in for 30 days

socketio = SocketIO(flask_app, cors_allowed_origins="*", async_mode="threading")

login_manager = LoginManager()
login_manager.init_app(flask_app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ==================== PUBLIC ROUTES ====================
@flask_app.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@flask_app.route("/login", methods=["GET", "POST"])
def login_page():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin_panel"))
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        login_input = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_login(login_input)

        if user and user.check_password(password):
            session.permanent = True
            login_user(user, remember=True)
            if user.is_admin:
                flash("Welcome Owner — Admin Panel unlocked", "success")
                return redirect(url_for("admin_panel"))
            flash(f"Welcome back, {user.fullname}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username/email or password.", "error")

    return render_template("login.html")

@flask_app.route("/register", methods=["GET", "POST"])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if get_user_by_login(username) or get_user_by_login(email):
            flash("Username or Email already taken.", "error")
            return render_template("register.html")

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user_id = str(uuid.uuid4())[:12]

        user = WebUser(id=user_id, username=username, fullname=fullname, email=email, password_hash=pw_hash)
        save_user(user)
        
        session.permanent = True
        login_user(user, remember=True)
        flash("Account created! You have 2 free trial signals.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@flask_app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("landing"))

# ==================== AUTHENTICATED ROUTES ====================
@flask_app.route("/dashboard")
@login_required
def dashboard():
    has_sub, sub_status, sub_days = current_user.has_active_sub()
    return render_template("dashboard.html", win_rate=0, total_trades=0, pnl=0,
                           sub_status=sub_status, sub_days=sub_days, recent_signals=[], content_items=[])

@flask_app.route("/signals")
@login_required
def signals_page():
    has_access, status, rem = current_user.has_active_sub()
    return render_template("signals.html", has_access=has_access, trial_remaining=rem,
                           has_key_input=True, admin_username=ADMIN_USERNAME,
                           pairs_json=json.dumps(PAIRS), durations=DURATIONS)

@flask_app.route("/subscribe")
@login_required
def subscribe_page():
    return render_template(
        "subscribe.html",
        usdt_address=USDT_ADDRESS,
        admin_username=ADMIN_USERNAME
    )
# ==================== ADMIN ROUTES ====================
@flask_app.route("/admin")
@login_required
@admin_required
def admin_panel():
    users = get_all_users()
    active_subs = sum(1 for u in users.values() if u.plan in ["week", "month", "lifetime"])
    return render_template(
        "admin/panel.html",
        total_users=len(users),
        active_subs=active_subs,
        total_keys=len(get_all_keys()),
        signals_today=len(get_signals_history()),
        recent_activity=get_activity()[:30]
    )
@flask_app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users_data = [{"id": u.id, "username": u.username, "fullname": u.fullname, "email": u.email, "plan": u.plan, "active": u.has_active_sub()[0]} for u in get_all_users().values()]
    return render_template("admin/users.html", users=users_data)

@flask_app.route("/admin/keys")
@login_required
@admin_required
def admin_keys():
    return render_template("admin/keys.html", keys=load_json(KEYS_FILE, []))

@flask_app.route("/admin/signals")
@login_required
@admin_required
def admin_signals():
    return render_template("admin/signals.html", signals=load_json(SIGNALS_FILE, []))

@flask_app.route("/admin/content")
@login_required
@admin_required
def admin_content():
    return render_template("admin/content.html", content=load_json(CONTENT_FILE, []))

@flask_app.route("/admin/broadcast")
@login_required
@admin_required
def admin_broadcast_page():
    return render_template("admin/broadcast.html", total_users=len(get_all_users()))

# ==================== RUN APPLICATION ====================
if __name__ == "__main__":
    create_admin_user() # Creates admin on startup
    socketio.run(flask_app, host="0.0.0.0", port=PORT, debug=False, allow_unsafe_werkzeug=True)
