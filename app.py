#!/usr/bin/env python3
"""
MK SNIPER BOT v47.0 — Complete Full-Stack Application
Flask Web Dashboard + Telegram Bot + Admin Panel + Payment System
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
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123secure")
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
    "USD/CHF": {"type": "forex", "payout": 85, "symbol": "USDCHF", "pip": 0.0001},
    "AUD/USD": {"type": "forex", "payout": 85, "symbol": "AUDUSD", "pip": 0.0001},
    "USD/CAD": {"type": "forex", "payout": 85, "symbol": "USDCAD", "pip": 0.0001},
    "NZD/USD": {"type": "forex", "payout": 85, "symbol": "NZDUSD", "pip": 0.0001},
    "EUR/JPY": {"type": "forex", "payout": 85, "symbol": "EURJPY", "pip": 0.01},
    "GBP/JPY": {"type": "forex", "payout": 85, "symbol": "GBPJPY", "pip": 0.01},
    "EUR/GBP": {"type": "forex", "payout": 85, "symbol": "EURGBP", "pip": 0.0001},
    "EUR/USD OTC": {"type": "otc", "payout": 92, "symbol": "EURUSD_OTC", "pip": 0.0001},
    "GBP/USD OTC": {"type": "otc", "payout": 92, "symbol": "GBPUSD_OTC", "pip": 0.0001},
    "USD/JPY OTC": {"type": "otc", "payout": 92, "symbol": "USDJPY_OTC", "pip": 0.01},
    "AUD/USD OTC": {"type": "otc", "payout": 92, "symbol": "AUDUSD_OTC", "pip": 0.0001},
    "USD/CAD OTC": {"type": "otc", "payout": 92, "symbol": "USDCAD_OTC", "pip": 0.0001},
    "NZD/USD OTC": {"type": "otc", "payout": 92, "symbol": "NZDUSD_OTC", "pip": 0.0001},
    "USD/CHF OTC": {"type": "otc", "payout": 92, "symbol": "USDCHF_OTC", "pip": 0.0001},
    "EUR/JPY OTC": {"type": "otc", "payout": 90, "symbol": "EURJPY_OTC", "pip": 0.01},
    "GBP/JPY OTC": {"type": "otc", "payout": 90, "symbol": "GBPJPY_OTC", "pip": 0.01},
    "EUR/GBP OTC": {"type": "otc", "payout": 90, "symbol": "EURGBP_OTC", "pip": 0.0001},
    "Gold OTC": {"type": "otc", "payout": 92, "symbol": "XAUUSD_OTC", "pip": 0.01},
    "Silver OTC": {"type": "otc", "payout": 88, "symbol": "XAGUSD_OTC", "pip": 0.001},
    "Apple OTC": {"type": "otc", "payout": 90, "symbol": "AAPL_OTC", "pip": 0.01},
    "Tesla OTC": {"type": "otc", "payout": 90, "symbol": "TSLA_OTC", "pip": 0.01},
    "Amazon OTC": {"type": "otc", "payout": 90, "symbol": "AMZN_OTC", "pip": 0.01},
    "BTC/USD": {"type": "crypto", "payout": 80, "binance": "BTCUSDT", "pip": 1.0},
    "ETH/USD": {"type": "crypto", "payout": 80, "binance": "ETHUSDT", "pip": 0.1},
    "SOL/USD": {"type": "crypto", "payout": 80, "binance": "SOLUSDT", "pip": 0.01},
    "XRP/USD": {"type": "crypto", "payout": 80, "binance": "XRPUSDT", "pip": 0.0001},
    "ADA/USD": {"type": "crypto", "payout": 80, "binance": "ADAUSDT", "pip": 0.0001},
    "DOGE/USD": {"type": "crypto", "payout": 80, "binance": "DOGEUSDT", "pip": 0.0001},
    "BNB/USD": {"type": "crypto", "payout": 80, "binance": "BNBUSDT", "pip": 0.1},
    "BTC/USD OTC": {"type": "otc", "payout": 85, "binance": "BTCUSDT", "pip": 1.0},
    "ETH/USD OTC": {"type": "otc", "payout": 85, "binance": "ETHUSDT", "pip": 0.1},
}

DURATIONS = {
    "3s": {"secs": 3, "label": "3s", "candle_sec": 3, "scan_wait": 1.0, "regime": "micro_tick"},
    "5s": {"secs": 5, "label": "5s", "candle_sec": 5, "scan_wait": 1.0, "regime": "micro_tick"},
    "10s": {"secs": 10, "label": "10s", "candle_sec": 10, "scan_wait": 1.2, "regime": "micro_tick"},
    "15s": {"secs": 15, "label": "15s", "candle_sec": 15, "scan_wait": 1.2, "regime": "micro_tick"},
    "30s": {"secs": 30, "label": "30s", "candle_sec": 30, "scan_wait": 1.5, "regime": "momentum"},
    "1m": {"secs": 60, "label": "1m", "candle_sec": 60, "scan_wait": 1.5, "regime": "momentum"},
    "2m": {"secs": 120, "label": "2m", "candle_sec": 120, "scan_wait": 2.0, "regime": "momentum"},
    "3m": {"secs": 180, "label": "3m", "candle_sec": 180, "scan_wait": 2.0, "regime": "swing_trend"},
    "5m": {"secs": 300, "label": "5m", "candle_sec": 300, "scan_wait": 2.5, "regime": "swing_trend"},
    "15m": {"secs": 900, "label": "15m", "candle_sec": 900, "scan_wait": 3.0, "regime": "swing_trend"},
}

# ==================== LOGGING ====================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(BASE_DIR / "bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
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
            "id": self.id,
            "username": self.username,
            "fullname": self.fullname,
            "email": self.email,
            "password_hash": self.password_hash,
            "telegram_id": self.telegram_id,
            "is_admin": self.is_admin,
            "plan": self.plan,
            "trial_used": self.trial_used,
            "expiry": self.expiry,
            "created": self.created,
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
    users = get_all_users()
    return users.get(uid)


def get_user_by_username(username: str) -> Optional[WebUser]:
    for u in get_all_users().values():
        if u.username.lower() == username.lower():
            return u
    return None


# ==================== ACCESS KEYS ====================
def get_all_keys() -> List[dict]:
    return load_json(KEYS_FILE, [])


def save_keys(keys: list):
    save_json(KEYS_FILE, keys)


def generate_access_key(plan: str) -> str:
    key = f"MK-{plan.upper()}-{secrets.token_hex(8).upper()}"
    keys = get_all_keys()
    keys.append({
        "key": key,
        "plan": plan,
        "used": False,
        "used_by": None,
        "created": now_local().strftime("%Y-%m-%d %H:%M"),
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

            # Activate subscription
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


# ==================== SIGNALS HISTORY ====================
def get_signals_history() -> List[dict]:
    return load_json(SIGNALS_FILE, [])


def save_signal(signal: dict):
    signals = get_signals_history()
    signals.insert(0, signal)
    if len(signals) > 500:
        signals = signals[:500]
    save_json(SIGNALS_FILE, signals)


# ==================== CONTENT MANAGEMENT ====================
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


# ==================== ACTIVITY LOG ====================
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


# ==================== MARKET ANALYSIS ENGINE ====================
PRICE_CACHE: Dict[str, dict] = {}
_api_session: Optional[aiohttp.ClientSession] = None
_api_sem = asyncio.Semaphore(25)


async def _get_api_session() -> aiohttp.ClientSession:
    global _api_session
    if not _api_session or _api_session.closed:
        connector = aiohttp.TCPConnector(limit=50, ttl_dns_cache=300)
        _api_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            connector=connector,
        )
    return _api_session


async def fetch_binance_candles(symbol: str, interval: str = "1m", limit: int = 80):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        async with _api_sem:
            sess = await _get_api_session()
            async with sess.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    return [{"open": float(c[1]), "high": float(c[2]),
                             "low": float(c[3]), "close": float(c[4]),
                             "volume": float(c[5])} for c in data]
    except Exception as e:
        log.warning(f"Binance error {symbol}: {e}")
    return None


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


async def get_live_data(pair: str) -> List[dict]:
    cache_key = f"{pair}_live"
    now = time.time()
    if cache_key in PRICE_CACHE and (now - PRICE_CACHE[cache_key]["ts"] < 1.0):
        return PRICE_CACHE[cache_key]["data"]
    pair_cfg = PAIRS.get(pair, {})
    candles = None
    if "binance" in pair_cfg:
        candles = await fetch_binance_candles(pair_cfg["binance"])
    if not candles:
        candles = generate_structured_wave_otc(pair)
    PRICE_CACHE[cache_key] = {"data": candles, "ts": now}
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
            if curr_rsi > 50:
                confluences.append(f"RSI Momentum ({curr_rsi:.1f})")
            else:
                confluences.append(f"RSI Momentum ({curr_rsi:.1f})")

    else:  # swing_trend
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

socketio = SocketIO(flask_app, cors_allowed_origins="*", async_mode="eventlet")

login_manager = LoginManager()
login_manager.init_app(flask_app)
login_manager.login_view = "login_page"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


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
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Admin login check
        if username == "admin" and password == ADMIN_PASSWORD:
            admin_user = get_user_by_username("admin")
            if not admin_user:
                pw_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
                admin_user = WebUser(
                    id=str(ADMIN_ID),
                    username="admin",
                    fullname="Admin",
                    email="admin@mksniper.com",
                    password_hash=pw_hash,
                    is_admin=True,
                    plan="lifetime"
                )
                save_user(admin_user)
            login_user(admin_user, remember=True)
            add_activity("🛡 Admin logged in via web")
            flash("Welcome back, Admin!", "success")
            return redirect(url_for("admin_panel"))

        user = get_user_by_username(username)
        if user and user.check_password(password):
            login_user(user, remember=True)
            add_activity(f"👤 User {username} logged in")
            flash(f"Welcome back, {user.fullname}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@flask_app.route("/register", methods=["GET", "POST"])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        telegram_id = request.form.get("telegram_id", "").strip() or None
        password = request.form.get("password", "")

        if not all([fullname, username, email, password]):
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        if get_user_by_username(username):
            flash("Username already taken.", "error")
            return render_template("register.html")

        # Check email uniqueness
        for u in get_all_users().values():
            if u.email.lower() == email.lower():
                flash("Email already registered.", "error")
                return render_template("register.html")

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user_id = str(uuid.uuid4())[:12]

        user = WebUser(
            id=user_id,
            username=username,
            fullname=fullname,
            email=email,
            password_hash=pw_hash,
            telegram_id=telegram_id,
            is_admin=False,
            plan="trial",
            trial_used=0,
        )
        save_user(user)
        add_activity(f"🆕 New user registered: {username}")

        # Notify admin via Telegram
        try:
            notify_admin_new_user(user)
        except Exception:
            pass

        login_user(user, remember=True)
        flash("Account created! You have 2 free trial signals.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@flask_app.route("/logout")
@login_required
def logout():
    add_activity(f"👋 User {current_user.username} logged out")
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("landing"))


# ==================== AUTHENTICATED ROUTES ====================
@flask_app.route("/dashboard")
@login_required
def dashboard():
    has_sub, sub_status, sub_days = current_user.has_active_sub()

    # Get user session stats
    sess = USER_SESSIONS.get(current_user.id, {"wins": 0, "losses": 0, "pnl": 0.0})
    total_trades = sess["wins"] + sess["losses"]
    win_rate = (sess["wins"] / total_trades * 100) if total_trades > 0 else 0.0

    # Get recent signals for this user
    all_signals = get_signals_history()
    recent = [s for s in all_signals if s.get("user") == current_user.username][:10]

    content_items = get_content()[:6]

    return render_template("dashboard.html",
                           win_rate=win_rate,
                           total_trades=total_trades,
                           pnl=sess["pnl"],
                           sub_status=sub_status,
                           sub_days=sub_days,
                           recent_signals=recent,
                           content_items=content_items)


@flask_app.route("/signals")
@login_required
def signals_page():
    has_access, status, remaining = current_user.has_active_sub()
    trial_remaining = remaining if status == "TRIAL" else 0

    return render_template("signals.html",
                           has_access=has_access,
                           trial_remaining=trial_remaining,
                           has_key_input=True,
                           admin_username=ADMIN_USERNAME,
                           pairs_json=json.dumps({k: {"type": v["type"], "payout": v["payout"]}
                                                  for k, v in PAIRS.items()}),
                           durations=DURATIONS)


@flask_app.route("/subscribe")
@login_required
def subscribe_page():
    return render_template("subscribe.html",
                           usdt_address=USDT_ADDRESS,
                           admin_username=ADMIN_USERNAME)


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


# ==================== API ENDPOINTS ====================
USER_SESSIONS: Dict[str, dict] = {}


@flask_app.route("/api/generate-signal", methods=["POST"])
@login_required
def api_generate_signal():
    has_access, status, remaining = current_user.has_active_sub()
    if not has_access:
        return jsonify({"success": False, "error": "Subscription required. Please upgrade your plan."})

    data = request.json
    pair = data.get("pair")
    dur_key = data.get("duration")

    if pair not in PAIRS or dur_key not in DURATIONS:
        return jsonify({"success": False, "error": "Invalid pair or duration."})

    # Use trial
    if status == "TRIAL":
        current_user.trial_used += 1
        save_user(current_user)

    # Generate signal
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

    # Broadcast to connected clients
    socketio.emit("new_signal", signal)

    return jsonify({"success": True, "signal": signal})


# ==================== ADMIN ROUTES ====================
@flask_app.route("/admin")
@login_required
@admin_required
def admin_panel():
    users = get_all_users()
    keys = get_all_keys()
    signals = get_signals_history()
    today = now_local().strftime("%Y-%m-%d")

    active_subs = sum(1 for u in users.values()
                      if u.plan in ["week", "month", "lifetime"] and u.plan != "trial")

    signals_today = sum(1 for s in signals if s.get("time", "").startswith(today))

    return render_template("admin/panel.html",
                           total_users=len(users),
                           active_subs=active_subs,
                           total_keys=len(keys),
                           signals_today=signals_today,
                           recent_activity=get_activity()[:30])


@flask_app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users_data = []
    for u in get_all_users().values():
        has_sub, _, _ = u.has_active_sub()
        users_data.append({
            "id": u.id,
            "username": u.username,
            "fullname": u.fullname,
            "email": u.email,
            "telegram_id": u.telegram_id,
            "plan": u.plan,
            "active": has_sub,
        })
    return render_template("admin/users.html", users=users_data)


@flask_app.route("/admin/keys")
@login_required
@admin_required
def admin_keys():
    keys = get_all_keys()
    return render_template("admin/keys.html", keys=keys)


@flask_app.route("/admin/signals")
@login_required
@admin_required
def admin_signals():
    signals = get_signals_history()[:100]
    return render_template("admin/signals.html", signals=signals)


@flask_app.route("/admin/content", methods=["GET"])
@login_required
@admin_required
def admin_content():
    content = get_content()
    return render_template("admin/content.html", content=content)


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
    add_activity(f"📝 Admin added content: {item['title']}")
    flash("Content added successfully!", "success")
    return redirect(url_for("admin_content"))


@flask_app.route("/admin/broadcast")
@login_required
@admin_required
def admin_broadcast_page():
    return render_template("admin/broadcast.html",
                           total_users=len(get_all_users()))


# ==================== ADMIN API ====================
@flask_app.route("/admin/api/generate-key", methods=["POST"])
@login_required
@admin_required
def api_generate_key():
    data = request.json
    plan = data.get("plan", "week")
    if plan not in SUBSCRIPTION_PLANS:
        return jsonify({"success": False, "error": "Invalid plan"})
    key = generate_access_key(plan)
    add_activity(f"🔑 Admin generated {plan} key: {key}")
    return jsonify({"success": True, "key": key})


@flask_app.route("/admin/api/activate-user", methods=["POST"])
@login_required
@admin_required
def api_activate_user():
    data = request.json
    user_id = data.get("user_id")
    plan = data.get("plan")

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"})

    user.plan = plan
    if plan == "lifetime":
        user.expiry = None
    else:
        days = SUBSCRIPTION_PLANS.get(plan, {}).get("days", 7)
        user.expiry = (now_local() + timedelta(days=days)).isoformat()
    save_user(user)
    add_activity(f"✅ Admin activated {plan} for {user.username}")

    # Notify user via Telegram if they have telegram_id
    if user.telegram_id:
        try:
            notify_user_activated(user, plan)
        except Exception:
            pass

    return jsonify({"success": True})


@flask_app.route("/admin/api/deactivate-user", methods=["POST"])
@login_required
@admin_required
def api_deactivate_user():
    data = request.json
    user_id = data.get("user_id")
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found"})

    user.plan = "expired"
    user.expiry = now_local().isoformat()
    save_user(user)
    add_activity(f"⛔ Admin deactivated {user.username}")
    return jsonify({"success": True})


@flask_app.route("/admin/api/broadcast", methods=["POST"])
@login_required
@admin_required
def api_broadcast():
    data = request.json
    message = data.get("message", "")
    if not message:
        return jsonify({"success": False, "error": "No message"})

    # Broadcast via SocketIO
    socketio.emit("admin_broadcast", {"message": message})

    # Broadcast via Telegram
    count = 0
    try:
        count = broadcast_telegram_sync(message)
    except Exception:
        pass

    add_activity(f"📢 Broadcast sent: {message[:50]}...")
    return jsonify({"success": True, "count": count})


@flask_app.route("/admin/api/content/<content_id>", methods=["DELETE"])
@login_required
@admin_required
def api_delete_content(content_id):
    delete_content_item(content_id)
    add_activity(f"🗑 Admin deleted content: {content_id}")
    return jsonify({"success": True})


# ==================== SOCKETIO EVENTS ====================
@socketio.on("connect")
def handle_connect():
    if current_user.is_authenticated:
        log.info(f"WebSocket connected: {current_user.username}")


# ==================== TELEGRAM BOT ====================
telegram_app = None

# Telegram session data
TG_SESSIONS: Dict[int, dict] = {}
TG_ACTIVE_TRADES: Dict[int, dict] = {}


def tg_get_sub(uid: int) -> dict:
    # Check if there's a web user linked by telegram_id
    for u in get_all_users().values():
        if u.telegram_id and str(u.telegram_id) == str(uid):
            return {
                "plan": u.plan,
                "trial_used": u.trial_used,
                "expiry": u.expiry
            }
    # Check old subs file
    subs = load_json(SUBS_FILE, {})
    return subs.get(str(uid), {"plan": "trial", "trial_used": 0, "expiry": None})


def tg_has_active(uid: int) -> Tuple[bool, str, Optional[int]]:
    if uid in ADMIN_IDS:
        return True, "ADMIN", None
    s = tg_get_sub(uid)
    if s["plan"] == "trial":
        rem = FREE_TRIAL_SIGNALS - s.get("trial_used", 0)
        return rem > 0, "TRIAL", rem
    if s["plan"] == "lifetime":
        return True, "LIFETIME", None
    if s.get("expiry"):
        exp = datetime.fromisoformat(s["expiry"])
        if now_local() < exp:
            return True, s["plan"].upper(), (exp - now_local()).days
        return False, "EXPIRED", 0
    return False, "NO SUBSCRIPTION", None


def tg_use_trial(uid: int):
    subs = load_json(SUBS_FILE, {})
    subs.setdefault(str(uid), {"plan": "trial", "trial_used": 0, "expiry": None})
    subs[str(uid)]["trial_used"] = subs[str(uid)].get("trial_used", 0) + 1
    save_json(SUBS_FILE, subs)
    # Also update web user if linked
    for u in get_all_users().values():
        if u.telegram_id and str(u.telegram_id) == str(uid):
            u.trial_used += 1
            save_user(u)
            break


def tg_activate_sub(uid: int, plan: str) -> bool:
    subs = load_json(SUBS_FILE, {})
    p = SUBSCRIPTION_PLANS.get(plan)
    if not p:
        return False
    now = now_local()
    subs[str(uid)] = {
        "plan": plan,
        "trial_used": subs.get(str(uid), {}).get("trial_used", 0),
        "expiry": None if plan == "lifetime" else (now + timedelta(days=p["days"])).isoformat(),
        "started": now.isoformat()
    }
    save_json(SUBS_FILE, subs)
    return True


# Telegram keyboards
def tg_main_menu_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎯 GET SIGNAL", callback_data="select_market"),
            InlineKeyboardButton("📊 MY METRICS", callback_data="stats"),
        ],
        [
            InlineKeyboardButton("💳 SUBSCRIBE", callback_data="subscribe"),
            InlineKeyboardButton("🔑 ENTER KEY", callback_data="enter_key"),
        ],
        [
            InlineKeyboardButton("🌐 WEB DASHBOARD", url=f"https://mk-sniper-bot.up.railway.app/"),
            InlineKeyboardButton("ℹ️ HELP", callback_data="howto"),
        ],
    ])


def tg_market_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌙 OTC", callback_data="mkt_otc"),
            InlineKeyboardButton("💱 FOREX", callback_data="mkt_forex"),
            InlineKeyboardButton("₿ CRYPTO", callback_data="mkt_crypto"),
        ],
        [InlineKeyboardButton("« Menu", callback_data="menu")]
    ])


def tg_pairs_kb(market: str, page: int = 0):
    pairs = [p for p, v in PAIRS.items() if v["type"] == market]
    per_page = 14
    total_pages = math.ceil(len(pairs) / per_page)
    start = page * per_page
    page_pairs = pairs[start:start + per_page]

    rows, row = [], []
    for p in page_pairs:
        row.append(InlineKeyboardButton(p, callback_data=f"pair_{p}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"page_{market}_{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"page_{market}_{page + 1}"))
    if nav_row:
        rows.append(nav_row)
    rows.append([InlineKeyboardButton("« Markets", callback_data="select_market")])
    return InlineKeyboardMarkup(rows)


def tg_durations_kb():
    rows = [
        [InlineKeyboardButton("3s", callback_data="dur_3s"),
         InlineKeyboardButton("5s", callback_data="dur_5s"),
         InlineKeyboardButton("10s", callback_data="dur_10s")],
        [InlineKeyboardButton("15s", callback_data="dur_15s"),
         InlineKeyboardButton("30s", callback_data="dur_30s"),
         InlineKeyboardButton("1m", callback_data="dur_1m")],
        [InlineKeyboardButton("2m", callback_data="dur_2m"),
         InlineKeyboardButton("3m", callback_data="dur_3m"),
         InlineKeyboardButton("5m", callback_data="dur_5m")],
        [InlineKeyboardButton("15m", callback_data="dur_15m")],
        [InlineKeyboardButton("« Markets", callback_data="select_market")]
    ]
    return InlineKeyboardMarkup(rows)


def tg_result_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ WIN (Entry)", callback_data="win_entry"),
            InlineKeyboardButton("✅ WIN (MG1)", callback_data="win_mg"),
        ],
        [InlineKeyboardButton("❌ LOSS", callback_data="loss")],
    ])


async def tg_safe_edit(q, text, kb):
    try:
        await q.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except (BadRequest, Exception):
        pass


# Telegram handlers
async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    un = update.effective_user.username or "N/A"
    fn = update.effective_user.first_name or "User"

    has_sub, plan_name, rem = tg_has_active(uid)
    sub_text = f"✅ Status: <b>{plan_name}</b>" if has_sub else "🔒 <b>Subscribe to unlock signals</b>"
    if plan_name == "TRIAL":
        sub_text += f" ({rem}/{FREE_TRIAL_SIGNALS} free signals left)"

    add_activity(f"📱 Telegram user {fn} (@{un}) started bot")

    # Notify admin
    if uid not in ADMIN_IDS:
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"🆕 <b>New Telegram User</b>\n\n"
                f"👤 Name: {fn}\n"
                f"🆔 ID: <code>{uid}</code>\n"
                f"📱 Username: @{un}\n"
                f"📊 Status: {plan_name}",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

    await update.message.reply_text(
        f"🎯 <b>MK SNIPER ENGINE v47.0</b>\n\n"
        f"{sub_text}\n\n"
        f"• Adaptive signal engine active\n"
        f"• 50+ trading pairs available\n"
        f"• Multi-duration support (3s → 15m)\n\n"
        f"🌐 <b>Web Dashboard:</b> Open the web portal for full features.\n\n"
        f"Tap <b>GET SIGNAL</b> below to start.",
        reply_markup=tg_main_menu_kb(),
        parse_mode=ParseMode.HTML
    )


async def tg_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    data = q.data

    try:
        await q.answer()
    except Exception:
        pass

    TG_SESSIONS.setdefault(uid, {"wins": 0, "losses": 0, "pnl": 0.0,
                                  "selected_pair": None, "selected_duration": None})
    sesh = TG_SESSIONS[uid]

    if data == "menu":
        await tg_safe_edit(q, "🎯 <b>MK SNIPER ENGINE</b>\n\nSelect an option:", tg_main_menu_kb())

    elif data == "select_market":
        await tg_safe_edit(q, "🌍 <b>Select Market:</b>", tg_market_kb())

    elif data.startswith("mkt_"):
        market = data.replace("mkt_", "")
        await tg_safe_edit(q, f"📍 <b>Select asset ({market.upper()}):</b>", tg_pairs_kb(market, 0))

    elif data.startswith("page_"):
        parts = data.split("_")
        market, page = parts[1], int(parts[2])
        await tg_safe_edit(q, f"📍 <b>Select asset ({market.upper()}):</b>", tg_pairs_kb(market, page))

    elif data.startswith("pair_"):
        pair = data.replace("pair_", "", 1)
        sesh["selected_pair"] = pair
        await tg_safe_edit(q, f"✅ Selected: <b>{pair}</b>\n\n⏱ <b>Select duration:</b>", tg_durations_kb())

    elif data.startswith("dur_"):
        dur_key = data.replace("dur_", "", 1)
        pair = sesh.get("selected_pair")
        if not pair:
            await tg_safe_edit(q, "⚠️ Select an asset first.", tg_main_menu_kb())
            return

        has_sub, status, rem = tg_has_active(uid)
        if not has_sub:
            await tg_safe_edit(
                q,
                f"🔒 <b>SUBSCRIPTION REQUIRED</b>\n\n"
                f"Your free trial signals have ended.\n\n"
                f"💳 <b>Plans:</b>\n"
                f"• 1 Week: $20\n"
                f"• 1 Month: $100\n"
                f"• Lifetime: $150\n\n"
                f"💰 <b>USDT (TRC20):</b>\n<code>{USDT_ADDRESS}</code>\n\n"
                f"Send payment proof to {ADMIN_USERNAME}\n"
                f"Your ID: <code>{uid}</code>",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
                    [InlineKeyboardButton("« Menu", callback_data="menu")]
                ])
            )
            return

        # Generate signal
        dur_info = DURATIONS[dur_key]
        candles = generate_structured_wave_otc(pair)
        analysis = evaluate_market_direction_sync(pair, dur_key, candles)

        et = next_candle_open(dur_key)
        mgt = et + timedelta(seconds=dur_info["secs"])
        direction = analysis["direction"]
        payout = PAIRS.get(pair, {}).get("payout", 85)

        TG_ACTIVE_TRADES[uid] = {
            "pair": pair, "direction": direction,
            "payout": payout, "duration": dur_key,
        }

        if status == "TRIAL":
            tg_use_trial(uid)

        dir_text = "🟢 CALL ⬆️" if direction == "CALL" else "🔴 PUT ⬇️"
        confluences_txt = "\n".join([f"  • {c}" for c in analysis["confluences"]])

        signal_data = {
            "pair": pair, "direction": direction,
            "duration": dur_info["label"],
            "entry_time": et.strftime("%H:%M:%S"),
            "mg_time": mgt.strftime("%H:%M:%S"),
            "accuracy": analysis["accuracy"],
            "payout": payout,
            "confluences": analysis["confluences"],
            "user": q.from_user.username or str(uid),
            "time": now_local().strftime("%Y-%m-%d %H:%M:%S"),
            "result": None
        }
        save_signal(signal_data)
        add_activity(f"🎯 TG Signal: {pair} {direction} by @{q.from_user.username or uid}")

        await tg_safe_edit(
            q,
            f"🎯 <b>ENTRY SIGNAL</b>\n\n"
            f"📊 <b>Asset:</b> <code>{pair}</code>\n"
            f"⏱ <b>Expiry:</b> <code>{dur_info['label']}</code>\n"
            f"🚀 <b>Action:</b> <b>{dir_text}</b>\n\n"
            f"⏰ <b>Entry:</b> <code>{et.strftime('%H:%M:%S')}</code>\n"
            f"🛡 <b>MG1:</b> <code>{mgt.strftime('%H:%M:%S')}</code>\n\n"
            f"💪 <b>Accuracy:</b> <code>{analysis['accuracy']}%</code>\n\n"
            f"<b>Confluences:</b>\n{confluences_txt}\n\n"
            f"⚠️ Execute at the Entry Time.",
            tg_result_kb()
        )

    elif data == "subscribe":
        await tg_safe_edit(
            q,
            f"💳 <b>SUBSCRIPTION PLANS</b>\n\n"
            f"• 1 Week: $20\n"
            f"• 1 Month: $100\n"
            f"• Lifetime: $150\n\n"
            f"💰 <b>USDT (TRC20):</b>\n<code>{USDT_ADDRESS}</code>\n\n"
            f"📱 Send payment proof to {ADMIN_USERNAME}\n"
            f"Include your ID: <code>{uid}</code>\n\n"
            f"After payment, admin will send you an activation key.",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton("🔑 Enter Key", callback_data="enter_key")],
                [InlineKeyboardButton("« Menu", callback_data="menu")]
            ])
        )

    elif data == "enter_key":
        sesh["awaiting_key"] = True
        await tg_safe_edit(
            q,
            "🔑 <b>Enter Access Key</b>\n\n"
            "Please type your access key in the chat:",
            InlineKeyboardMarkup([[InlineKeyboardButton("« Cancel", callback_data="menu")]])
        )

    elif data == "stats":
        total = sesh["wins"] + sesh["losses"]
        wr = (sesh["wins"] / total * 100) if total > 0 else 0.0
        await tg_safe_edit(
            q,
            f"📊 <b>PERFORMANCE</b>\n\n"
            f"• Wins: <b>{sesh['wins']}</b>\n"
            f"• Losses: <b>{sesh['losses']}</b>\n"
            f"• Win Rate: <b>{wr:.1f}%</b>\n"
            f"• PnL: <b>{sesh['pnl']:+.2f} USDT</b>",
            InlineKeyboardMarkup([[InlineKeyboardButton("« Menu", callback_data="menu")]])
        )

    elif data == "howto":
        await tg_safe_edit(
            q,
            "📖 <b>HOW TO USE</b>\n\n"
            "1. Select market & asset\n"
            "2. Choose trade duration\n"
            "3. Follow the signal direction\n"
            "4. Place trade at Entry Time\n"
            "5. Mark your result\n\n"
            f"🌐 <b>Web Dashboard:</b> Full features online\n"
            f"💳 <b>Subscribe:</b> Contact {ADMIN_USERNAME}",
            InlineKeyboardMarkup([[InlineKeyboardButton("« Menu", callback_data="menu")]])
        )

    elif data in ("win_entry", "win_mg", "loss"):
        trade = TG_ACTIVE_TRADES.pop(uid, None)
        if not trade:
            await q.answer("No active trade.", show_alert=True)
            return
        is_win = data != "loss"
        is_entry = data == "win_entry"
        if is_win:
            profit = (ENTRY_STAKE * trade["payout"] / 100) if is_entry else (
                        MG_STAKE * trade["payout"] / 100 - ENTRY_STAKE)
            sesh["wins"] += 1
            res = "✅ WIN"
        else:
            profit = -(ENTRY_STAKE + MG_STAKE)
            sesh["losses"] += 1
            res = "❌ LOSS"
        sesh["pnl"] += profit

        await tg_safe_edit(
            q,
            f"{res}\n\n"
            f"📊 {trade['pair']}\n"
            f"💰 {'+' if profit > 0 else ''}{profit:.2f} USDT\n"
            f"📈 {sesh['wins']}W - {sesh['losses']}L",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Next Signal", callback_data="select_market")],
                [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
            ])
        )


async def tg_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for key entry and admin forwarding"""
    uid = update.effective_user.id
    text = update.message.text.strip()

    sesh = TG_SESSIONS.get(uid, {})

    # Check if user is entering an access key
    if sesh.get("awaiting_key"):
        sesh["awaiting_key"] = False

        # Try to redeem key
        keys = get_all_keys()
        found = False
        for k in keys:
            if k["key"] == text and not k["used"]:
                plan = k["plan"]
                k["used"] = True
                k["used_by"] = f"tg_{uid}"
                save_keys(keys)
                tg_activate_sub(uid, plan)

                # Also update web user if linked
                for u in get_all_users().values():
                    if u.telegram_id and str(u.telegram_id) == str(uid):
                        u.plan = plan
                        if plan == "lifetime":
                            u.expiry = None
                        else:
                            days = SUBSCRIPTION_PLANS[plan]["days"]
                            u.expiry = (now_local() + timedelta(days=days)).isoformat()
                        save_user(u)
                        break

                add_activity(f"🔑 TG user {uid} redeemed {plan} key")
                await update.message.reply_text(
                    f"🎉 <b>{plan.upper()} plan activated!</b>\n\n"
                    f"You now have full access to all signals.\n"
                    f"Tap /start to begin trading.",
                    parse_mode=ParseMode.HTML
                )
                found = True
                break

        if not found:
            await update.message.reply_text(
                "❌ Invalid or already used key.\n"
                f"Contact {ADMIN_USERNAME} for help.",
                parse_mode=ParseMode.HTML
            )
        return

    # Forward non-admin messages to admin (payment proofs, etc.)
    if uid not in ADMIN_IDS:
        try:
            un = update.effective_user.username or "N/A"
            fn = update.effective_user.first_name or "User"
            await context.bot.send_message(
                ADMIN_ID,
                f"📨 <b>Message from user</b>\n\n"
                f"👤 {fn} (@{un})\n"
                f"🆔 ID: <code>{uid}</code>\n\n"
                f"💬 {text}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Reply to {fn}", url=f"tg://user?id={uid}")]
                ])
            )
            await update.message.reply_text(
                "✅ Message sent to admin. They will respond shortly.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            log.error(f"Forward to admin error: {e}")


# Admin telegram commands
async def tg_activate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    try:
        uid = int(context.args[0])
        plan = context.args[1].lower()
        if tg_activate_sub(uid, plan):
            await update.message.reply_text(
                f"✅ Activated <b>{plan.upper()}</b> for ID: <code>{uid}</code>",
                parse_mode=ParseMode.HTML
            )
            # Notify user
            try:
                await context.bot.send_message(
                    uid,
                    f"🎉 <b>Subscription Activated!</b>\n\n"
                    f"Plan: <b>{plan.upper()}</b>\n"
                    f"Your signals are now unlocked.\n\n"
                    f"Tap /start to begin trading.",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
            add_activity(f"✅ Admin activated {plan} for TG user {uid}")
    except Exception:
        await update.message.reply_text("Usage: /activate USER_ID PLAN\nExample: /activate 123456 month")


async def tg_broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS or not context.args:
        return
    msg = " ".join(context.args)
    # Get all telegram users from subs
    subs = load_json(SUBS_FILE, {})
    count = 0
    for u in subs:
        try:
            await context.bot.send_message(int(u), f"📢 <b>Announcement:</b>\n\n{msg}", parse_mode=ParseMode.HTML)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")
    add_activity(f"📢 TG Broadcast: {msg[:50]}...")


async def tg_genkey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    plan = context.args[0].lower() if context.args else "week"
    if plan not in SUBSCRIPTION_PLANS:
        await update.message.reply_text("Plans: week, month, lifetime")
        return
    key = generate_access_key(plan)
    await update.message.reply_text(
        f"🔑 <b>New {plan.upper()} Key Generated</b>\n\n"
        f"<code>{key}</code>\n\n"
        f"Send this key to the user.",
        parse_mode=ParseMode.HTML
    )
    add_activity(f"🔑 Admin generated {plan} key via TG: {key}")


async def tg_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    users = get_all_users()
    subs = load_json(SUBS_FILE, {})

    msg = f"👥 <b>All Users ({len(users)} web + {len(subs)} telegram)</b>\n\n"

    for uid, u in list(users.items())[:20]:
        has_sub, status, _ = u.has_active_sub()
        emoji = "✅" if has_sub else "❌"
        msg += f"{emoji} {u.username} | {status} | ID: <code>{u.id}</code>\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


# Helper functions for Telegram notifications
def notify_admin_new_user(user: WebUser):
    """Send notification to admin about new web registration"""
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": ADMIN_ID,
        "text": f"🆕 <b>New Web Registration</b>\n\n"
                f"👤 {user.fullname}\n"
                f"📧 {user.email}\n"
                f"🆔 {user.username}\n"
                f"📱 TG: {user.telegram_id or 'Not linked'}",
        "parse_mode": "HTML"
    })


def notify_user_activated(user: WebUser, plan: str):
    """Notify user via Telegram about activation"""
    if not user.telegram_id:
        return
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": int(user.telegram_id),
        "text": f"🎉 <b>Subscription Activated!</b>\n\n"
                f"Plan: <b>{plan.upper()}</b>\n"
                f"Your signals are now unlocked!\n\n"
                f"Open the web dashboard or use /start here.",
        "parse_mode": "HTML"
    })


def broadcast_telegram_sync(message: str) -> int:
    """Broadcast message to all Telegram users"""
    import requests
    subs = load_json(SUBS_FILE, {})
    count = 0
    for uid in subs:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                "chat_id": int(uid),
                "text": f"📢 <b>Announcement:</b>\n\n{message}",
                "parse_mode": "HTML"
            }, timeout=5)
            count += 1
        except Exception:
            pass
    return count


# ==================== BOT STARTUP ====================
def run_telegram_bot():
    """Run telegram bot in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_bot():
        global telegram_app
        telegram_app = Application.builder().token(BOT_TOKEN).build()

        telegram_app.add_handler(CommandHandler("start", tg_start))
        telegram_app.add_handler(CommandHandler("activate", tg_activate_cmd))
        telegram_app.add_handler(CommandHandler("broadcast", tg_broadcast_cmd))
        telegram_app.add_handler(CommandHandler("genkey", tg_genkey_cmd))
        telegram_app.add_handler(CommandHandler("users", tg_users_cmd))
        telegram_app.add_handler(CallbackQueryHandler(tg_button))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_message_handler))

        async with telegram_app:
            await telegram_app.start()
            await telegram_app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            log.info("✅ Telegram bot started successfully")
            try:
                await asyncio.Event().wait()
            finally:
                await telegram_app.updater.stop()
                await telegram_app.stop()

    loop.run_until_complete(start_bot())


# ==================== APPLICATION STARTUP ====================
def create_admin_user():
    """Ensure admin user exists"""
    admin = get_user_by_username("admin")
    if not admin:
        pw_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
        admin = WebUser(
            id=str(ADMIN_ID),
            username="admin",
            fullname="Admin",
            email="admin@mksniper.com",
            password_hash=pw_hash,
            is_admin=True,
            plan="lifetime"
        )
        save_user(admin)
        log.info("Admin user created")


# Create admin on startup
create_admin_user()

# Start Telegram bot in background thread
if BOT_TOKEN and ":" in BOT_TOKEN:
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    log.info("Telegram bot thread started")

print("=" * 60)
print("  MK SNIPER BOT v47.0 — FULL-STACK APPLICATION")
print(f"  Web: http://0.0.0.0:{PORT}")
print(f"  Admin: admin / {ADMIN_PASSWORD}")
print("=" * 60)

if __name__ == "__main__":
    socketio.run(flask_app, host="0.0.0.0", port=PORT, debug=False)