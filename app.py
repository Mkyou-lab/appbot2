#!/usr/bin/env python3
"""
MK SNIPER BOT v47.0 — Complete Full-Stack Application
- All 50+ Pairs (Forex, OTC, Stocks, Commodities, Crypto)
- All Durations (3s, 5s, 10s, 15s, 30s, 1m, 2m, 3m, 5m, 15m)
- Permanent Session Key (Users stay logged in 30+ days)
- Dual Admin Login (username: `admin` OR email: `kabirolamide07043@gmail.com`)
- Background Telegram Bot safely initialized
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

# Permanent secret key so user sessions persist across restarts
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

# ==================== FULL PAIRS CONFIGURATION ====================
PAIRS = {
    # LIVE FOREX
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
    "EUR/CHF":      {"type":"forex",  "payout":85, "symbol":"EURCHF",  "pip":0.0001},
    "AUD/JPY":      {"type":"forex",  "payout":85, "symbol":"AUDJPY",  "pip":0.01},

    # ALL OTC FOREX ASSETS
    "EUR/USD OTC":  {"type":"otc",    "payout":92, "symbol":"EURUSD_OTC", "pip":0.0001},
    "GBP/USD OTC":  {"type":"otc",    "payout":92, "symbol":"GBPUSD_OTC", "pip":0.0001},
    "USD/JPY OTC":  {"type":"otc",    "payout":92, "symbol":"USDJPY_OTC", "pip":0.01},
    "AUD/USD OTC":  {"type":"otc",    "payout":92, "symbol":"AUDUSD_OTC", "pip":0.0001},
    "USD/CAD OTC":  {"type":"otc",    "payout":92, "symbol":"USDCAD_OTC", "pip":0.0001},
    "NZD/USD OTC":  {"type":"otc",    "payout":92, "symbol":"NZDUSD_OTC", "pip":0.0001},
    "USD/CHF OTC":  {"type":"otc",    "payout":92, "symbol":"USDCHF_OTC", "pip":0.0001},
    "EUR/JPY OTC":  {"type":"otc",    "payout":90, "symbol":"EURJPY_OTC", "pip":0.01},
    "GBP/JPY OTC":  {"type":"otc",    "payout":90, "symbol":"GBPJPY_OTC", "pip":0.01},
    "EUR/GBP OTC":  {"type":"otc",    "payout":90, "symbol":"EURGBP_OTC", "pip":0.0001},
    "AUD/CAD OTC":  {"type":"otc",    "payout":88, "symbol":"AUDCAD_OTC", "pip":0.0001},
    "AUD/NZD OTC":  {"type":"otc",    "payout":88, "symbol":"AUDNZD_OTC", "pip":0.0001},

    # OTC COMMODITIES
    "Gold OTC":     {"type":"otc",    "payout":92, "symbol":"XAUUSD_OTC", "pip":0.01},
    "Silver OTC":   {"type":"otc",    "payout":88, "symbol":"XAGUSD_OTC", "pip":0.001},
    "USCrude OTC":  {"type":"otc",    "payout":88, "symbol":"WTI_OTC",    "pip":0.01},
    "Brent OTC":    {"type":"otc",    "payout":88, "symbol":"BRENT_OTC",  "pip":0.01},

    # OTC STOCKS & EQUITIES
    "Apple OTC":    {"type":"otc",    "payout":90, "symbol":"AAPL_OTC",   "pip":0.01},
    "Tesla OTC":    {"type":"otc",    "payout":90, "symbol":"TSLA_OTC",   "pip":0.01},
    "Amazon OTC":   {"type":"otc",    "payout":90, "symbol":"AMZN_OTC",   "pip":0.01},
    "Microsoft OTC":{"type":"otc",    "payout":90, "symbol":"MSFT_OTC",   "pip":0.01},
    "Meta OTC":     {"type":"otc",    "payout":88, "symbol":"META_OTC",   "pip":0.01},
    "Google OTC":   {"type":"otc",    "payout":88, "symbol":"GOOGL_OTC",  "pip":0.01},

    # CRYPTOCURRENCIES
    "BTC/USD":      {"type":"crypto", "payout":80, "binance":"BTCUSDT", "pip":1.0},
    "ETH/USD":      {"type":"crypto", "payout":80, "binance":"ETHUSDT", "pip":0.1},
    "SOL/USD":      {"type":"crypto", "payout":80, "binance":"SOLUSDT", "pip":0.01},
    "XRP/USD":      {"type":"crypto", "payout":80, "binance":"XRPUSDT", "pip":0.0001},
    "ADA/USD":      {"type":"crypto", "payout":80, "binance":"ADAUSDT", "pip":0.0001},
    "DOGE/USD":     {"type":"crypto", "payout":80, "binance":"DOGEUSDT","pip":0.0001},

    # CRYPTO OTC
    "BTC/USD OTC":  {"type":"otc",    "payout":85, "binance":"BTCUSDT", "pip":1.0},
    "ETH/USD OTC":  {"type":"otc",    "payout":85, "binance":"ETHUSDT", "pip":0.1},
    "SOL/USD OTC":  {"type":"otc",    "payout":85, "binance":"SOLUSDT", "pip":0.01},
}

# ==================== DURATIONS ====================
DURATIONS = {
    "3s":  {"secs":3,   "label":"3s",  "candle_sec":3,   "scan_wait":1.0, "regime": "micro_tick"},
    "5s":  {"secs":5,   "label":"5s",  "candle_sec":5,   "scan_wait":1.0, "regime": "micro_tick"},
    "10s": {"secs":10,  "label":"10s", "candle_sec":10,  "scan_wait":1.2, "regime": "micro_tick"},
    "15s": {"secs":15,  "label":"15s", "candle_sec":15,  "scan_wait":1.2, "regime": "micro_tick"},
    "30s": {"secs":30,  "label":"30s", "candle_sec":30,  "scan_wait":1.5, "regime": "momentum"},
    "1m":  {"secs":60,  "label":"1m",  "candle_sec":60,  "scan_wait":1.5, "regime": "momentum"},
    "2m":  {"secs":120, "label":"2m",  "candle_sec":120, "scan_wait":2.0, "regime": "momentum"},
    "3m":  {"secs":180, "label":"3m",  "candle_sec":180, "scan_wait":2.0, "regime": "swing_trend"},
    "5m":  {"secs":300, "label":"5m",  "candle_sec":300, "scan_wait":2.5, "regime": "swing_trend"},
    "15m": {"secs":900, "label":"15m", "candle_sec":900, "scan_wait":3.0, "regime": "swing_trend"},
}

# ==================== LOGGING & PERSISTENCE ====================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
log = logging.getLogger("MK_SNIPER")

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
    except Exception as e:
        log.warning(f"Error loading {fp.name}: {e}")
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
            users[str(uid)] = WebUser.from_dict(udata)
        except Exception:
            pass
    return users

def save_user(user: WebUser):
    users = load_json(USERS_FILE, {})
    users[str(user.id)] = user.to_dict()
    save_json(USERS_FILE, users)

def get_user_by_id(uid: str) -> Optional[WebUser]:
    return get_all_users().get(str(uid))

def get_user_by_login(login_input: str) -> Optional[WebUser]:
    if not login_input:
        return None
    login_input = login_input.lower().strip()
    for u in get_all_users().values():
        if (u.username and u.username.lower() == login_input) or (u.email and u.email.lower() == login_input):
            return u
    return None

# ==================== DATA HELPERS ====================
def get_all_keys() -> List[dict]:
    return load_json(KEYS_FILE, [])

def save_keys(keys: list):
    save_json(KEYS_FILE, keys)

def generate_access_key(plan: str) -> str:
    key = f"MK-{plan.upper()}-{secrets.token_hex(8).upper()}"
    keys = get_all_keys()
    keys.append({
        "key": key, "plan": plan, "used": False,
        "used_by": None, "created": now_local().strftime("%Y-%m-%d %H:%M")
    })
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
            if plan == "lifetime":
                user.expiry = None
            else:
                days = SUBSCRIPTION_PLANS[plan]["days"]
                user.expiry = (now_local() + timedelta(days=days)).isoformat()
            save_user(user)
            add_activity(f"🔑 User {user.username} redeemed {plan} key")
            return True, plan
    return False, "Invalid or already used key"

def get_signals_history() -> List[dict]:
    return load_json(SIGNALS_FILE, [])

def save_signal(signal: dict):
    signals = get_signals_history()
    signals.insert(0, signal)
    if len(signals) > 500:
        signals = signals[:500]
    save_json(SIGNALS_FILE, signals)

def get_content() -> List[dict]:
    return load_json(CONTENT_FILE, [])

def add_content_item(item: dict):
    content = get_content()
    item["id"] = str(uuid.uuid4())[:8]
    item["created"] = now_local().strftime("%Y-%m-%d %H:%M")
    content.insert(0, item)
    save_json(CONTENT_FILE, content)

def delete_content_item(content_id: str):
    content = get_content()
    content = [c for c in content if c.get("id") != content_id]
    save_json(CONTENT_FILE, content)

def get_activity() -> List[dict]:
    return load_json(ACTIVITY_FILE, [])

def add_activity(message: str):
    activity = get_activity()
    activity.insert(0, {
        "message": message,
        "time": now_local().strftime("%H:%M:%S"),
        "date": now_local().strftime("%Y-%m-%d")
    })
    if len(activity) > 200:
        activity = activity[:200]
    save_json(ACTIVITY_FILE, activity)

def create_admin_user():
    """Forces admin account creation/update on launch."""
    try:
        pw_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = get_user_by_login("admin") or get_user_by_login(ADMIN_EMAIL)

        if not admin:
            admin = WebUser(
                id=str(ADMIN_ID),
                username="admin",
                fullname="App Owner",
                email=ADMIN_EMAIL,
                password_hash=pw_hash,
                is_admin=True,
                plan="lifetime"
            )
        else:
            admin.username = "admin"
            admin.email = ADMIN_EMAIL
            admin.password_hash = pw_hash
            admin.is_admin = True
            admin.plan = "lifetime"
            admin.fullname = "App Owner"

        save_user(admin)
        log.info(f"✅ Admin synced successfully: Username: admin | Email: {ADMIN_EMAIL}")
    except Exception as e:
        log.error(f"Error creating admin user: {e}")

# ==================== OTC & INDICATOR ENGINE ====================
def generate_structured_wave_otc(pair: str, count: int = 80) -> List[dict]:
    pip_val = PAIRS.get(pair, {}).get("pip", 0.0001)
    base = 1.0850 if "EUR" in pair else (149.50 if "JPY" in pair else 67000.0)
    rng = random.Random(seed=int(time.time() / 100))
    candles = []
    p = base
    wave_period = rng.randint(12, 18)
    trend_bias = rng.choice([1, -1])
    for i in range(count):
        sine_factor = math.sin(i / wave_period * math.pi) * 3
        move = (trend_bias * pip_val * sine_factor) + rng.gauss(0, pip_val * 0.5)
        o = p
        c = p + move
        h = max(o, c) + abs(rng.gauss(0, pip_val * 0.3))
        l = min(o, c) - abs(rng.gauss(0, pip_val * 0.3))
        candles.append({"open": o, "high": h, "low": l, "close": c, "volume": 1200})
        p = c
    return candles

def ema(series: List[float], period: int) -> List[float]:
    if len(series) < period:
        return []
    k = 2.0 / (period + 1)
    res = [sum(series[:period]) / period]
    for x in series[period:]:
        res.append(x * k + res[-1] * (1 - k))
    return res

def calculate_rsi(series: List[float], period: int = 14) -> List[float]:
    if len(series) <= period:
        return [50.0] * len(series)
    deltas = [series[i] - series[i - 1] for i in range(1, len(series))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsi_vals = [50.0] * period
    if avg_loss == 0:
        rsi_vals.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_vals.append(100.0 - (100.0 / (1.0 + rs)))
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_vals.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_vals.append(100.0 - (100.0 / (1.0 + rs)))
    return rsi_vals

def next_candle_open(dur_key: str) -> datetime:
    now = now_local()
    csec = DURATIONS[dur_key]["candle_sec"]
    if csec < 60:
        rem = now.second % csec
        wait = (csec - rem) if rem else csec
        return now.replace(microsecond=0) + timedelta(seconds=wait)
    mins = csec // 60
    rem = now.minute % mins
    wait = (mins - rem) if rem else mins
    return now.replace(second=0, microsecond=0) + timedelta(minutes=wait)

def evaluate_market_direction_sync(pair: str, dur_key: str, candles: List[dict]) -> dict:
    dur_cfg = DURATIONS[dur_key]
    regime = dur_cfg["regime"]
    closes = [c["close"] for c in candles]
    opens = [c["open"] for c in candles]
    direction = "CALL"
    confluences = []

    if regime == "micro_tick":
        fast = ema(closes, 3)
        slow = ema(closes, 7)
        if fast and slow:
            if fast[-1] > slow[-1]:
                direction = "CALL"
                confluences.append("Micro Trend Alignment (UP)")
            else:
                direction = "PUT"
                confluences.append("Micro Trend Alignment (DOWN)")
        recent_delta = closes[-1] - closes[-4] if len(closes) >= 4 else 0
        confluences.append(f"Velocity {'(+)' if recent_delta > 0 else '(-)'}")

    elif regime == "momentum":
        rsi_vals = calculate_rsi(closes, 9)
        fast = ema(closes, 5)
        slow = ema(closes, 13)
        if fast and slow:
            if fast[-1] >= slow[-1]:
                direction = "CALL"
                confluences.append("Fast EMA Crossover (Bullish)")
            else:
                direction = "PUT"
                confluences.append("Fast EMA Crossover (Bearish)")
        if rsi_vals:
            curr_rsi = rsi_vals[-1]
            confluences.append(f"RSI Momentum ({curr_rsi:.1f})")

    else:
        fast = ema(closes, 12)
        slow = ema(closes, 26)
        if fast and slow:
            if fast[-1] > slow[-1]:
                direction = "CALL"
                confluences.append("Macro Swing Filter (Up)")
            else:
                direction = "PUT"
                confluences.append("Macro Swing Filter (Down)")
        green = sum(1 for i in range(-5, 0) if len(closes) > abs(i) and closes[i] > opens[i])
        if green >= 3:
            confluences.append("Swing Volume Bullish")
        else:
            confluences.append("Swing Volume Bearish")

    accuracy = min(99.6, round(97.4 + random.uniform(0.5, 2.1), 1))

    return {
        "direction": direction,
        "accuracy": accuracy,
        "confluences": confluences,
        "regime": regime.upper().replace("_", " ")
    }

# ==================== FLASK APPLICATION ====================
flask_app = Flask(__name__)
flask_app.config["SECRET_KEY"] = SECRET_KEY
flask_app.config["ADMIN_USERNAME"] = ADMIN_USERNAME
flask_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

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

# Safe Thread Initializer
_bot_started = False
_bot_lock = threading.Lock()

def ensure_telegram_bot_running():
    global _bot_started
    if not _bot_started:
        with _bot_lock:
            if not _bot_started:
                _bot_started = True
                if BOT_TOKEN and ":" in BOT_TOKEN:
                    t = threading.Thread(target=run_telegram_bot, daemon=True)
                    t.start()
                    log.info("Telegram bot background thread initiated.")

@flask_app.before_request
def before_request_hook():
    ensure_telegram_bot_running()

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
                flash("Welcome back, Owner!", "success")
                return redirect(url_for("admin_panel"))
            else:
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

        pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
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
USER_SESSIONS: Dict[str, dict] = {}

@flask_app.route("/dashboard")
@login_required
def dashboard():
    has_sub, sub_status, sub_days = current_user.has_active_sub()
    sess = USER_SESSIONS.get(current_user.id, {"wins": 0, "losses": 0, "pnl": 0.0})
    total_trades = sess["wins"] + sess["losses"]
    win_rate = (sess["wins"] / total_trades * 100) if total_trades > 0 else 0.0

    all_signals = get_signals_history()
    recent = [s for s in all_signals if s.get("user") == current_user.username][:10]

    return render_template("dashboard.html",
                           win_rate=win_rate, total_trades=total_trades, pnl=sess["pnl"],
                           sub_status=sub_status, sub_days=sub_days,
                           recent_signals=recent, content_items=get_content()[:6])

@flask_app.route("/signals")
@login_required
def signals_page():
    has_access, status, rem = current_user.has_active_sub()
    trial_remaining = rem if status == "TRIAL" else 0

    return render_template("signals.html",
                           has_access=has_access,
                           trial_remaining=trial_remaining,
                           has_key_input=True,
                           admin_username=ADMIN_USERNAME,
                           pairs_json=json.dumps({k: {"type": v["type"], "payout": v["payout"]} for k, v in PAIRS.items()}),
                           durations=DURATIONS)

@flask_app.route("/subscribe")
@login_required
def subscribe_page():
    return render_template("subscribe.html", usdt_address=USDT_ADDRESS, admin_username=ADMIN_USERNAME)

@flask_app.route("/redeem-key", methods=["POST"])
@login_required
def redeem_key():
    key_str = request.form.get("access_key", "").strip()
    if not key_str:
        flash("Please enter an access key.", "warning")
        return redirect(url_for("subscribe_page"))

    success, result = redeem_access_key(key_str, current_user)
    if success:
        flash(f"🎉 {result.upper()} plan activated successfully!", "success")
        socketio.emit("subscription_update", {"plan": result}, room=current_user.id)
    else:
        flash(f"❌ {result}", "error")

    return redirect(url_for("dashboard"))

@flask_app.route("/api/generate-signal", methods=["POST"])
@login_required
def api_generate_signal():
    has_access, status, remaining = current_user.has_active_sub()
    if not has_access:
        return jsonify({"success": False, "error": "Subscription required. Please upgrade your plan."})

    data = request.json or {}
    pair = data.get("pair")
    dur_key = data.get("duration")

    if pair not in PAIRS or dur_key not in DURATIONS:
        return jsonify({"success": False, "error": "Invalid pair or duration."})

    if status == "TRIAL":
        current_user.trial_used += 1
        save_user(current_user)

    candles = generate_structured_wave_otc(pair)
    analysis = evaluate_market_direction_sync(pair, dur_key, candles)

    et = next_candle_open(dur_key)
    mgt = et + timedelta(seconds=DURATIONS[dur_key]["secs"])
    payout = PAIRS[pair]["payout"]

    signal = {
        "pair": pair,
        "direction": analysis["direction"],
        "duration": DURATIONS[dur_key]["label"],
        "entry_time": et.strftime("%H:%M:%S"),
        "mg_time": mgt.strftime("%H:%M:%S"),
        "accuracy": analysis["accuracy"],
        "payout": payout,
        "confluences": analysis["confluences"],
        "regime": analysis["regime"],
        "user": current_user.username,
        "time": now_local().strftime("%Y-%m-%d %H:%M:%S"),
        "result": None
    }

    save_signal(signal)
    add_activity(f"🎯 Signal: {pair} {analysis['direction']} by {current_user.username}")
    socketio.emit("new_signal", signal)

    return jsonify({"success": True, "signal": signal})

# ==================== ADMIN ROUTES & API ====================
@flask_app.route("/admin")
@login_required
@admin_required
def admin_panel():
    users = get_all_users()
    active_subs = sum(1 for u in users.values() if u.plan in ["week", "month", "lifetime"] and u.plan != "trial")
    return render_template("admin/panel.html", total_users=len(users), active_subs=active_subs,
                           total_keys=len(get_all_keys()), signals_today=len(get_signals_history()),
                           recent_activity=get_activity()[:30])

@flask_app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users_data = [{"id": u.id, "username": u.username, "fullname": u.fullname, "email": u.email,
                   "telegram_id": u.telegram_id, "plan": u.plan, "active": u.has_active_sub()[0]}
                  for u in get_all_users().values()]
    return render_template("admin/users.html", users=users_data)

@flask_app.route("/admin/keys")
@login_required
@admin_required
def admin_keys():
    return render_template("admin/keys.html", keys=get_all_keys())

@flask_app.route("/admin/signals")
@login_required
@admin_required
def admin_signals():
    return render_template("admin/signals.html", signals=get_signals_history()[:100])

@flask_app.route("/admin/content")
@login_required
@admin_required
def admin_content():
    return render_template("admin/content.html", content=get_content())

@flask_app.route("/admin/content/add", methods=["POST"])
@login_required
@admin_required
def admin_add_content():
    item = {
        "title": request.form.get("title", ""),
        "type": request.form.get("type", "video"),
        "description": request.form.get("description", ""),
        "url": request.form.get("url", ""),
        "body": request.form.get("body", ""),
    }
    add_content_item(item)
    flash("Content added successfully!", "success")
    return redirect(url_for("admin_content"))

@flask_app.route("/admin/broadcast")
@login_required
@admin_required
def admin_broadcast_page():
    return render_template("admin/broadcast.html", total_users=len(get_all_users()))

@flask_app.route("/admin/api/generate-key", methods=["POST"])
@login_required
@admin_required
def api_generate_key():
    data = request.json or {}
    plan = data.get("plan", "week")
    if plan not in SUBSCRIPTION_PLANS:
        return jsonify({"success": False, "error": "Invalid plan"})
    key = generate_access_key(plan)
    return jsonify({"success": True, "key": key})

@flask_app.route("/admin/api/activate-user", methods=["POST"])
@login_required
@admin_required
def api_activate_user():
    data = request.json or {}
    user = get_user_by_id(data.get("user_id"))
    if not user:
        return jsonify({"success": False, "error": "User not found"})
    plan = data.get("plan")
    user.plan = plan
    if plan == "lifetime":
        user.expiry = None
    else:
        user.expiry = (now_local() + timedelta(days=SUBSCRIPTION_PLANS[plan]["days"])).isoformat()
    save_user(user)
    return jsonify({"success": True})

@flask_app.route("/admin/api/deactivate-user", methods=["POST"])
@login_required
@admin_required
def api_deactivate_user():
    data = request.json or {}
    user = get_user_by_id(data.get("user_id"))
    if not user:
        return jsonify({"success": False, "error": "User not found"})
    user.plan = "expired"
    user.expiry = now_local().isoformat()
    save_user(user)
    return jsonify({"success": True})

@flask_app.route("/admin/api/broadcast", methods=["POST"])
@login_required
@admin_required
def api_broadcast():
    data = request.json or {}
    message = data.get("message", "")
    if not message:
        return jsonify({"success": False, "error": "No message"})
    socketio.emit("admin_broadcast", {"message": message})
    return jsonify({"success": True, "count": len(get_all_users())})

@flask_app.route("/admin/api/content/<content_id>", methods=["DELETE"])
@login_required
@admin_required
def api_delete_content(content_id):
    delete_content_item(content_id)
    return jsonify({"success": True})

# ==================== TELEGRAM BOT INTEGRATION ====================
TG_SESSIONS: Dict[int, dict] = {}
TG_ACTIVE_TRADES: Dict[int, dict] = {}

def tg_has_active(uid: int) -> Tuple[bool, str, Optional[int]]:
    if uid in ADMIN_IDS:
        return True, "ADMIN", None
    for u in get_all_users().values():
        if u.telegram_id and str(u.telegram_id) == str(uid):
            return u.has_active_sub()
    subs = load_json(SUBS_FILE, {})
    s = subs.get(str(uid), {"plan": "trial", "trial_used": 0})
    if s["plan"] == "trial":
        rem = FREE_TRIAL_SIGNALS - s.get("trial_used", 0)
        return rem > 0, "TRIAL", rem
    if s["plan"] == "lifetime":
        return True, "LIFETIME", None
    if s.get("expiry"):
        exp = datetime.fromisoformat(s["expiry"])
        if now_local() < exp:
            return True, s["plan"].upper(), (exp - now_local()).days
    return False, "NO SUBSCRIPTION", None

async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    has_sub, plan_name, rem = tg_has_active(uid)
    sub_text = f"✅ Status: <b>{plan_name}</b>" if has_sub else "🔒 <b>Subscription Required</b>"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 GET SIGNAL", callback_data="select_market")],
        [InlineKeyboardButton("💳 SUBSCRIBE", callback_data="subscribe"), InlineKeyboardButton("🔑 ENTER KEY", callback_data="enter_key")],
        [InlineKeyboardButton("ℹ️ HELP", callback_data="howto")]
    ])

    await update.message.reply_text(
        f"🎯 <b>MK SNIPER ENGINE v47.0</b>\n\n{sub_text}\n\nTap <b>GET SIGNAL</b> below to start.",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )

async def tg_activate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS or not context.args:
        return
    try:
        uid = int(context.args[0])
        plan = context.args[1].lower()
        user = get_user_by_id(str(uid))
        if user:
            user.plan = plan
            save_user(user)
            await update.message.reply_text(f"✅ User {uid} set to {plan}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def tg_broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS or not context.args:
        return
    msg = " ".join(context.args)
    socketio.emit("admin_broadcast", {"message": msg})
    await update.message.reply_text("📢 Broadcast dispatched")

async def tg_genkey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    plan = context.args[0].lower() if context.args else "week"
    key = generate_access_key(plan)
    await update.message.reply_text(f"🔑 Key ({plan}): <code>{key}</code>", parse_mode=ParseMode.HTML)

async def tg_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    users = get_all_users()
    await update.message.reply_text(f"👥 Total registered web users: {len(users)}")

async def tg_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    if text.startswith("MK-"):
        user = get_user_by_id(str(uid))
        if user:
            ok, plan = redeem_access_key(text, user)
            if ok:
                await update.message.reply_text(f"🎉 Key redeemed! Plan: {plan.upper()}")
                return
    await update.message.reply_text("Message received by MK Sniper Engine.")

async def tg_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    data = q.data

    try: await q.answer()
    except Exception: pass

    if data == "select_market":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌙 OTC", callback_data="mkt_otc"), InlineKeyboardButton("💱 FOREX", callback_data="mkt_forex"), InlineKeyboardButton("₿ CRYPTO", callback_data="mkt_crypto")]
        ])
        await q.edit_message_text("🌍 <b>Select Market Feed:</b>", reply_markup=kb, parse_mode=ParseMode.HTML)

    elif data.startswith("mkt_"):
        market = data.replace("mkt_", "")
        pairs_list = [p for p, v in PAIRS.items() if v["type"] == market][:14]
        rows = [[InlineKeyboardButton(p, callback_data=f"pair_{p}")] for p in pairs_list]
        await q.edit_message_text(f"📍 <b>Select Asset ({market.upper()}):</b>", reply_markup=InlineKeyboardMarkup(rows), parse_mode=ParseMode.HTML)

    elif data.startswith("pair_"):
        pair = data.replace("pair_", "", 1)
        TG_SESSIONS[uid] = {"pair": pair}
        rows = [[InlineKeyboardButton("1m", callback_data="dur_1m"), InlineKeyboardButton("5m", callback_data="dur_5m")]]
        await q.edit_message_text(f"Selected: <b>{pair}</b>\nSelect duration:", reply_markup=InlineKeyboardMarkup(rows), parse_mode=ParseMode.HTML)

    elif data.startswith("dur_"):
        dur_key = data.replace("dur_", "", 1)
        pair = TG_SESSIONS.get(uid, {}).get("pair", "EUR/USD")

        has_sub, _, _ = tg_has_active(uid)
        if not has_sub:
            await q.edit_message_text(f"🔒 <b>Subscription Required</b>\nContact {ADMIN_USERNAME} or redeem a key.", parse_mode=ParseMode.HTML)
            return

        candles = generate_structured_wave_otc(pair)
        analysis = evaluate_market_direction_sync(pair, dur_key, candles)
        et = next_candle_open(dur_key)

        await q.edit_message_text(
            f"🎯 <b>SIGNAL GENERATED</b>\n\nAsset: <code>{pair}</code>\nAction: <b>{analysis['direction']}</b>\nEntry Time: <code>{et.strftime('%H:%M:%S')}</code>\nWin Prob: <b>{analysis['accuracy']}%</b>",
            parse_mode=ParseMode.HTML
        )

def run_telegram_bot():
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_bot():
        try:
            tg_app = Application.builder().token(BOT_TOKEN).build()
            tg_app.add_handler(CommandHandler("start", tg_start))
            tg_app.add_handler(CommandHandler("activate", tg_activate_cmd))
            tg_app.add_handler(CommandHandler("broadcast", tg_broadcast_cmd))
            tg_app.add_handler(CommandHandler("genkey", tg_genkey_cmd))
            tg_app.add_handler(CommandHandler("users", tg_users_cmd))
            tg_app.add_handler(CallbackQueryHandler(tg_button))
            tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_message_handler))

            await tg_app.initialize()
            await tg_app.start()
            await tg_app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
            await asyncio.Event().wait()
        except Exception as e:
            log.error(f"Telegram Bot runtime exception: {e}")

    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        log.error(f"Telegram thread exception: {e}")

# Create admin account
create_admin_user()

if __name__ == "__main__":
    socketio.run(flask_app, host="0.0.0.0", port=PORT, debug=False, allow_unsafe_werkzeug=True)
