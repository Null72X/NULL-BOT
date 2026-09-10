"""
============================================================
              NULL - ADVANCED PRODUCT INFO BOT
============================================================
Developed for: NULL
Architecture: Discord.py 2.x + Flask Micro-Dashboard
Author: NULL
All Rights Reserved © 2026 NULL

FEATURES:
- Channel ID product & catalog broadcasting (/product_send, /catalog_send, /showcase_publish)
- Dynamic Discord UI (Interactive buttons, Dropdowns, Order Modals)
- Multi-tier pricing (1D, 7D, 30D, Lifetime)
- Real-time software/cheat status tracking (🟢 Undetected, 🟡 Updating, 🔴 Detected)
- Slash command autocomplete for instant product selection
- Promo / discount code system
- Customer 5-star ratings & reviews
- Auto-backup rotation to /backups directory & discord /backup file export
- Audit logging channel for all administrative actions
- Cyberpunk dark Flask web dashboard (port 10000)
- Backward-compatible mention search (@NULL <keyword>)
============================================================
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import shutil
import asyncio
import traceback
import time
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, send_from_directory
import threading
import sys
import math
import re
from dotenv import load_dotenv

# Ensure console outputs cleanly in UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

bot_instance = None

def normalize_name(text: str) -> str:
    """Cleans names by removing emojis and symbols for matching"""
    return re.sub(r'[^a-zA-Z0-9\-]', '', str(text).replace(' ', '-')).lower()

def find_matching_channel_for_plan(bot_ref=None, plan_name: str = "", product_dict: dict = None):
    """Auto-detects matching server channel for a plan or uses previously saved channel"""
    bot_target = bot_ref or bot_instance
    if not bot_target or not hasattr(bot_target, 'guilds'):
        return None

    # Priority 1: Check if admin previously saved a target channel for this plan
    if product_dict and product_dict.get("saved_channel_id"):
        try:
            cid = int(product_dict["saved_channel_id"])
            if cid > 0:
                ch = bot_target.get_channel(cid)
                if ch:
                    return ch
        except:
            pass

    norm_plan = normalize_name(plan_name)
    if not norm_plan:
        return None
    for guild in bot_target.guilds:
        for ch in guild.text_channels:
            norm_ch = normalize_name(ch.name)
            if norm_plan == norm_ch or norm_ch.endswith(norm_plan) or norm_plan in norm_ch:
                return ch
    return None

def get_latency_ms(bot_ref=None):
    """Safely retrieves latency without failing on float NaN"""
    bot_target = bot_ref or bot_instance
    try:
        if bot_target and bot_target.latency is not None:
            lat = float(bot_target.latency)
            if not math.isnan(lat) and not math.isinf(lat):
                return max(0, round(lat * 1000))
    except:
        pass
    return 0


# =========================================================
# CONFIGURATION & ENVIRONMENT
# =========================================================

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0") or "0")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or "0")
DEFAULT_SHOWCASE_CHANNEL_ID = int(os.getenv("SHOWCASE_CHANNEL_ID", "0") or "0")
DEFAULT_LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1547230630759239710") or "1547230630759239710")
BOT_NAME = os.getenv("BOT_NAME", "NULL")
CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "₹")
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://discord.gg/")
BUY_INSTRUCTIONS = os.getenv(
    "BUY_INSTRUCTIONS", 
    "To purchase, click the 'Order / Buy' button to submit an order ticket or contact an administrator."
)

if not TOKEN:
    raise ValueError("❌ TOKEN not found in environment variables (.env)!")

BOT_START_TIME = time.time()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "product_data.json")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# Ensure backup and upload directories exist
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================================================
# DATA MANAGEMENT & BACKUPS
# =========================================================

DEFAULT_PRODUCTS = {
    "ext_lite": {
        "name": "External-Lite",
        "category": "External Plans",
        "description": "Null External Lite Panel For Free Fire 100% Safe in all Server",
        "price_1d": "₹100",
        "price_7d": "₹500",
        "price_30d": "₹1,200",
        "price_lifetime": "₹2,500",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "🎯 Aimbot",
            "⚡ Location",
            "🛡️ Stream Mode"
        ],
        "banner_url": "/uploads/banner_1788953842_4eecc2.png",
        "image_url": "/uploads/banner_1788953842_4eecc2.png",
        "images": [
            "/uploads/banner_1788953842_4eecc2.png"
        ],
        "saved_channel_id": "1510598006959767562",
        "color": "red"
    },
    "ext_basic": {
        "name": "External-Basic",
        "category": "External Plans",
        "description": "Null External Lite Panel For Free Fire 100% Safe in all Server",
        "price_1d": "₹200",
        "price_7d": "₹800",
        "price_30d": "₹1,800",
        "price_lifetime": "₹3,800",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "🎯 Aimbot",
            "🚀 Sniper",
            "⚡ Location"
        ],
        "banner_url": "/uploads/banner_1788954053_f11ac4.png",
        "image_url": "/uploads/banner_1788954053_f11ac4.png",
        "images": [
            "/uploads/banner_1788954053_f11ac4.png"
        ],
        "saved_channel_id": "1510598006959767562",
        "color": "red"
    },
    "ext_premium": {
        "name": "External-Premium",
        "category": "External Plans",
        "description": "Null External Lite Panel For Free Fire 100% Safe in all Server",
        "price_1d": "₹500",
        "price_7d": "₹1,800",
        "price_30d": "₹3,500",
        "price_lifetime": "₹7,000",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "🎯 Aimbot",
            "🚀 Sniper",
            "✨ Location"
        ],
        "banner_url": "/uploads/banner_1788954181_bf5431.png",
        "image_url": "/uploads/banner_1788954181_bf5431.png",
        "images": [
            "/uploads/banner_1788954181_bf5431.png"
        ],
        "saved_channel_id": "1510598006959767562",
        "color": "red"
    },
    "int_lite": {
        "name": "Internal-Lite",
        "category": "Internal Plans",
        "description": "Null External Lite Panel For Free Fire 100% Safe in all Server",
        "price_1d": "₹150",
        "price_7d": "₹600",
        "price_30d": "₹1,400",
        "price_lifetime": "₹3,000",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "🎯 Aimbot",
            "✨ Esp",
            "🔒 Stream Mode"
        ],
        "banner_url": "/uploads/banner_1788954281_23e470.png",
        "image_url": "/uploads/banner_1788954281_23e470.png",
        "images": [
            "/uploads/banner_1788954281_23e470.png"
        ],
        "saved_channel_id": "1543872330973978674",
        "color": "red"
    },
    "int_basic": {
        "name": "Internal-Basic",
        "category": "Internal Plans",
        "description": "Null External Lite Panel For Free Fire 100% Safe in all Server",
        "price_1d": "₹250",
        "price_7d": "₹950",
        "price_30d": "₹2,200",
        "price_lifetime": "₹4,500",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "🎯 Aimbot",
            "⚡ Esp",
            "🔒 Stream Mode"
        ],
        "banner_url": "/uploads/banner_1788954491_45b85d.png",
        "image_url": "/uploads/banner_1788954491_45b85d.png",
        "images": [
            "/uploads/banner_1788954491_45b85d.png"
        ],
        "saved_channel_id": "1543872330973978674",
        "color": "red"
    },
    "int_premium": {
        "name": "Internal-Premium",
        "category": "Internal Plans",
        "description": "The ultimate internal masterpiece: silent aim, full legit/rage switching, priority VIP updates, and skin changer.",
        "price_1d": "₹550",
        "price_7d": "₹2,000",
        "price_30d": "₹4,000",
        "price_lifetime": "₹8,000",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "🎯 Aimbot",
            "⚡ Esp",
            "🔒 Stream Mode"
        ],
        "banner_url": "/uploads/banner_1788954644_9bf324.png",
        "image_url": "/uploads/banner_1788954644_9bf324.png",
        "images": [
            "/uploads/banner_1788954644_9bf324.png"
        ],
        "saved_channel_id": "1543872330973978674",
        "color": "red"
    },
    "aim_assist": {
        "name": "Aim-Assist",
        "category": "Aim Assist Plans",
        "description": "Natural humanized aim smoothing for both keyboard/mouse and controllers with anti-detection curve simulation.",
        "price_1d": "₹100",
        "price_7d": "₹450",
        "price_30d": "₹1,000",
        "price_lifetime": "₹2,200",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "Humanized Aim Smoothing Curves",
            "Soft Lock on Target Center",
            "Controller & KBM Emulation"
        ],
        "banner_url": "",
        "image_url": "",
        "images": [],
        "saved_channel_id": "1547110395976749106",
        "color": "red"
    },
    "aim_assist_esp": {
        "name": "Aim-Assist-ESP",
        "category": "Aim Assist Plans",
        "description": "Complete dual combo combining smooth humanized aim assist with clean player box & distance visuals.",
        "price_1d": "₹200",
        "price_7d": "₹800",
        "price_30d": "₹1,800",
        "price_lifetime": "₹3,800",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "Soft Aim Assist with Auto-Tracking",
            "Clean 2D Player Box ESP",
            "Snaplines & Health Indicators"
        ],
        "banner_url": "",
        "image_url": "",
        "images": [],
        "saved_channel_id": "1542075967328227339",
        "color": "red"
    },
    "ext_streamer": {
        "name": "Ext-Streamer",
        "category": "Streamer Plans",
        "description": "Streamer-grade external tool completely hidden from OBS Studio, Discord Screenshare, and ShadowPlay.",
        "price_1d": "₹500",
        "price_7d": "₹1,900",
        "price_30d": "₹3,800",
        "price_lifetime": "₹7,500",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "100% Invisible to Streaming / Recording Software",
            "Stealth Overlay Only Visible to You",
            "Ultra Smooth Natural Aim Assist"
        ],
        "banner_url": "",
        "image_url": "",
        "images": [],
        "saved_channel_id": "1542076319297179688",
        "color": "red"
    },
    "int_streamer_basic": {
        "name": "Int-Streamer-Basic",
        "category": "Streamer Plans",
        "description": "Internal memory streamproof build providing seamless legit smoothing and hidden visuals for live broadcasts.",
        "price_1d": "₹350",
        "price_7d": "₹1,300",
        "price_30d": "₹2,800",
        "price_lifetime": "₹5,800",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "Internal Kernel Bypass for Stream Capture",
            "Legit Smooth Aim with FOV Limiter",
            "Invisible Chams on Capture Devices"
        ],
        "banner_url": "",
        "image_url": "",
        "images": [],
        "saved_channel_id": "1542076319297179688",
        "color": "red"
    },
    "int_streamer_lite": {
        "name": "Int-Streamer-Lite",
        "category": "Streamer Plans",
        "description": "Lightweight, high-framerate streamproof internal package designed for clean recordings and streams.",
        "price_1d": "₹200",
        "price_7d": "₹750",
        "price_30d": "₹1,600",
        "price_lifetime": "₹3,500",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "OBS & Discord Invisible Hook",
            "Minimalist Chams Overlay",
            "High Refresh Rate (240Hz+ Ready)"
        ],
        "banner_url": "",
        "image_url": "",
        "images": [],
        "saved_channel_id": "1542076319297179688",
        "color": "red"
    },
    "uid_bypass": {
        "name": "Uid-Bypass",
        "category": "Bypass Plans",
        "description": "Advanced UID, HWID, and registry spoofer with deep kernel masking to bypass anti-cheat restrictions.",
        "price_1d": "₹150",
        "price_7d": "₹550",
        "price_30d": "₹1,200",
        "price_lifetime": "₹2,600",
        "status": "🟢 Undetected",
        "stock": "In Stock",
        "compatibility": "Windows 10 / 11 | Intel & AMD",
        "features": [
            "Full UID & HWID Randomizer",
            "Registry & Network Adapter Masking",
            "Disk Serial & BIOS Spoofer"
        ],
        "banner_url": "",
        "image_url": "",
        "images": [],
        "saved_channel_id": "1510597998219104390",
        "color": "red"
    }
}

DEFAULT_DATA = {
    "config": {
        "showcase_channel_id": str(DEFAULT_SHOWCASE_CHANNEL_ID),
        "log_channel_id": str(DEFAULT_LOG_CHANNEL_ID),
        "brand_name": BOT_NAME,
        "currency_symbol": CURRENCY_SYMBOL,
        "support_url": SUPPORT_URL
    },
    "categories": {
        "external plans": "External Plans",
        "internal plans": "Internal Plans",
        "aim assist plans": "Aim Assist Plans",
        "streamer plans": "Streamer Plans",
        "bypass plans": "Bypass Plans"
    },
    "products": DEFAULT_PRODUCTS,
    "promos": {},
    "reviews": {},
    "analytics": {
        "total_queries": 0,
        "products_sent": 0
    }
}

def load_json():
    """Load product database with schema guarantees and auto-seed defaults"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all root keys exist
                for key, val in DEFAULT_DATA.items():
                    if key not in data:
                        data[key] = json.loads(json.dumps(val))
                
                # Auto-seed any missing default products
                products = data.setdefault("products", {})
                changed = False
                for pid, pval in DEFAULT_PRODUCTS.items():
                    if pid not in products:
                        products[pid] = json.loads(json.dumps(pval))
                        changed = True
                if changed:
                    save_json(data)
                return data
        except Exception as e:
            print(f"⚠️ Warning loading {DATA_FILE}: {e}. Initializing defaults.")
            data = json.loads(json.dumps(DEFAULT_DATA))
            save_json(data)
            return data
    data = json.loads(json.dumps(DEFAULT_DATA))
    save_json(data)
    return data

def save_json(data):
    """Save product data atomically and create rolling timestamped backup"""
    try:
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Atomic replace
        if os.path.exists(DATA_FILE):
            os.replace(temp_file, DATA_FILE)
        else:
            os.rename(temp_file, DATA_FILE)
        
        # Rolling backup (max 10 recent backups)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")
        try:
            shutil.copyfile(DATA_FILE, backup_path)
            backups = sorted([os.path.join(BACKUP_DIR, b) for b in os.listdir(BACKUP_DIR) if b.endswith(".json")])
            if len(backups) > 10:
                for old in backups[:-10]:
                    try:
                        os.remove(old)
                    except:
                        pass
        except Exception as be:
            print(f"⚠️ Backup notice: {be}")

        return True
    except Exception as e:
        print(f"❌ Error saving database: {e}")
        return False

# =========================================================
# FLASK WEB DASHBOARD
# =========================================================

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ bot_name }} | Control Matrix</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090a0f;
            --card-bg: rgba(18, 20, 29, 0.75);
            --border: rgba(147, 51, 234, 0.25);
            --primary: #9333ea;
            --primary-glow: rgba(147, 51, 234, 0.4);
            --accent: #06b6d4;
            --text-main: #f3f4f6;
            --text-dim: #9ca3af;
            --success: #10b981;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            background-image: 
                radial-gradient(at 0% 0%, rgba(147, 51, 234, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.12) 0px, transparent 50%);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }
        .container {
            width: 100%;
            max-width: 1100px;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 24px;
            margin-bottom: 36px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .logo-box {
            width: 50px;
            height: 50px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            font-weight: 800;
            box-shadow: 0 0 25px var(--primary-glow);
        }
        .brand h1 {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #fff, var(--text-dim));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand p {
            font-size: 13px;
            color: var(--text-dim);
            font-family: 'JetBrains Mono', monospace;
        }
        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--success);
            padding: 8px 16px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 14px;
        }
        .pulse {
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--success);
            animation: pulse-anim 2s infinite;
        }
        @keyframes pulse-anim {
            0% { opacity: 0.4; }
            50% { opacity: 1; }
            100% { opacity: 0.4; }
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            backdrop-filter: blur(12px);
            border-radius: 18px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s, border-color 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            border-color: var(--primary);
        }
        .stat-title {
            font-size: 13px;
            color: var(--text-dim);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .stat-value {
            font-size: 32px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            color: #fff;
        }
        .section-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        .product-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: border-color 0.2s;
        }
        .product-card:hover {
            border-color: var(--accent);
        }
        .product-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        .product-name {
            font-size: 18px;
            font-weight: 700;
        }
        .product-category {
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 6px;
            background: rgba(147, 51, 234, 0.2);
            color: #d8b4fe;
            font-weight: 600;
        }
        .product-desc {
            font-size: 13px;
            color: var(--text-dim);
            line-height: 1.5;
            margin-bottom: 16px;
        }
        .price-tag {
            display: flex;
            gap: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            padding-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }
        .price-item span {
            color: var(--text-dim);
            font-size: 11px;
            display: block;
        }
        .price-item strong {
            color: var(--accent);
        }
        footer {
            margin-top: 60px;
            text-align: center;
            color: var(--text-dim);
            font-size: 13px;
            font-family: 'JetBrains Mono', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <div class="logo-box">∅</div>
                <div>
                    <h1>{{ bot_name }} SYSTEM</h1>
                    <p>PRODUCT MANAGEMENT & BROADCAST MATRIX</p>
                </div>
            </div>
            <div class="status-badge">
                <span class="pulse"></span>
                SYSTEM OPERATIONAL
            </div>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Catalog Inventory</div>
                <div class="stat-value">{{ total_products }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Active Categories</div>
                <div class="stat-value">{{ total_categories }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Total Inquiries</div>
                <div class="stat-value">{{ total_queries }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Broadcasts Sent</div>
                <div class="stat-value">{{ products_sent }}</div>
            </div>
        </div>

        <div class="section-title">
            <span>📦</span> Live Product Repository
        </div>

        <div class="product-grid">
            {% for pid, p in products.items() %}
            <div class="product-card">
                <div>
                    <div class="product-header">
                        <div class="product-name">{{ p.name }}</div>
                        <span class="product-category">{{ p.category }}</span>
                    </div>
                    <p class="product-desc">{{ p.description }}</p>
                </div>
                <div>
                    <div style="font-size: 12px; margin-bottom: 8px; color: #10b981;">
                        Status: <strong>{{ p.status or '🟢 Undetected' }}</strong>
                    </div>
                    <div class="price-tag">
                        <div class="price-item">
                            <span>1 DAY</span>
                            <strong>{{ p.price_1d or 'N/A' }}</strong>
                        </div>
                        <div class="price-item">
                            <span>7 DAYS</span>
                            <strong>{{ p.price_7d or 'N/A' }}</strong>
                        </div>
                        {% if p.price_30d %}
                        <div class="price-item">
                            <span>30 DAYS</span>
                            <strong>{{ p.price_30d }}</strong>
                        </div>
                        {% endif %}
                        {% if p.price_lifetime %}
                        <div class="price-item">
                            <span>LIFETIME</span>
                            <strong>{{ p.price_lifetime }}</strong>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <footer>
            PROPRIETARY ARCHITECTURE • BELONGS TO NULL • RUNNING V2.0
        </footer>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    html_file = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        return content, 200, {"Content-Type": "text/html; charset=utf-8"}

    data = load_json()
    products = data.get("products", {})
    categories = data.get("categories", {})
    analytics = data.get("analytics", {})
    
    return render_template_string(
        DASHBOARD_HTML,
        bot_name=BOT_NAME,
        total_products=len(products),
        total_categories=len(categories),
        total_queries=analytics.get("total_queries", 0),
        products_sent=analytics.get("products_sent", 0),
        products=products
    )

@app.route('/api/products')
def api_products():
    return jsonify(load_json())

def run_flask():
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    port = int(os.environ.get("PORT") or os.environ.get("SERVER_PORT") or 10000)
    app.run(host='0.0.0.0', port=port, debug=False)


# =========================================================
# DISCORD UI COMPONENTS (VIEWS & MODALS)
# =========================================================

class OrderModal(discord.ui.Modal, title="🛒 Order Request - NULL"):
    duration = discord.ui.TextInput(
        label="Subscription Duration",
        placeholder="e.g. 1 Day, 7 Days, 30 Days, Lifetime",
        required=True,
        max_length=50
    )
    payment_method = discord.ui.TextInput(
        label="Preferred Payment Method",
        placeholder="e.g. UPI (PhonePe, GPay, Paytm, QR), Crypto, Card, PayPal",
        required=True,
        max_length=50
    )
    notes = discord.ui.TextInput(
        label="Special Notes or Questions (Optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Any specific instructions or configuration questions...",
        required=False,
        max_length=500
    )

    def __init__(self, product_name: str, product_id: str, bot_ref):
        super().__init__()
        self.product_name = product_name
        self.product_id = product_id
        self.bot_ref = bot_ref

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # User confirmation
        confirm_embed = discord.Embed(
            title="✅ Order Request Submitted!",
            description=(
                f"Thank you **{interaction.user.name}**! Your request for **{self.product_name}** has been received.\n\n"
                f"**Duration:** `{self.duration.value}`\n"
                f"**Payment:** `{self.payment_method.value}`\n\n"
                f"An administrator will reach out to you shortly, or you may open a ticket in our support server: {SUPPORT_URL}"
            ),
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        confirm_embed.set_footer(text=f"NULL Systems • Order ID: {int(time.time())}")
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)
        
        # Dispatch alert to configured order notification channel (1547230630759239710)
        log_chan_id = 0
        try:
            if hasattr(self.bot_ref, 'get_log_channel_id'):
                log_chan_id = self.bot_ref.get_log_channel_id()
            else:
                data = load_json()
                log_chan_id = int(data.get("config", {}).get("log_channel_id", "1547230630759239710") or "1547230630759239710")
        except:
            log_chan_id = 1547230630759239710

        if not log_chan_id or log_chan_id == 0:
            log_chan_id = 1547230630759239710

        bot_obj = self.bot_ref or bot_instance
        if bot_obj and log_chan_id:
            chan = bot_obj.get_channel(log_chan_id)
            if not chan:
                try:
                    chan = await bot_obj.fetch_channel(log_chan_id)
                except Exception as e:
                    chan = None
            if chan:
                alert_embed = discord.Embed(
                    title="🚨 NEW PRODUCT ORDER REQUEST",
                    color=discord.Color.from_rgb(239, 68, 68),  # Crimson Red
                    timestamp=datetime.now()
                )
                alert_embed.add_field(name="👤 Customer", value=f"{interaction.user.mention} (`{interaction.user.name}` | ID: `{interaction.user.id}`)", inline=True)
                alert_embed.add_field(name="🛒 Product", value=f"**{self.product_name}** (`{self.product_id}`)", inline=True)
                alert_embed.add_field(name="⏱️ Duration", value=f"`{self.duration.value}`", inline=True)
                alert_embed.add_field(name="💳 Payment Method", value=f"`{self.payment_method.value}`", inline=True)
                if self.notes.value:
                    alert_embed.add_field(name="📝 Customer Notes", value=self.notes.value, inline=False)
                alert_embed.set_footer(text=f"NULL Order Dispatch • Order #{int(time.time())}")
                try:
                    await chan.send(content=f"🔔 **Incoming Order Alert!** {interaction.user.mention} submitted an order for **{self.product_name}**!", embed=alert_embed)
                except Exception as e:
                    print(f"⚠️ Failed to send order notification: {e}")

class ProductCardView(discord.ui.View):
    """Persistent Interactive Action Buttons attached to Product Cards"""
    def __init__(self, product_id: str, product_data: dict = None, bot_ref = None):
        super().__init__(timeout=None)
        self.product_id = product_id
        self.product_data = product_data or {}
        self.bot_ref = bot_ref

        # 1. Buy Now button (Primary / Blurple, matches web preview)
        btn_buy = discord.ui.Button(
            label="Buy Now",
            style=discord.ButtonStyle.primary,
            emoji="🛒",
            custom_id=f"null_buy:{product_id}"
        )
        btn_buy.callback = self.buy_callback
        self.add_item(btn_buy)

        # 2. Features button (Secondary / Grey, matches web preview)
        btn_feats = discord.ui.Button(
            label="Features",
            style=discord.ButtonStyle.secondary,
            emoji="✨",
            custom_id=f"null_feats:{product_id}"
        )
        btn_feats.callback = self.features_callback
        self.add_item(btn_feats)

        # 3. Open Ticket button (Secondary / Grey, matches web preview)
        btn_ticket = discord.ui.Button(
            label="Open Ticket",
            style=discord.ButtonStyle.secondary,
            emoji="🎫",
            custom_id=f"null_ticket:{product_id}"
        )
        btn_ticket.callback = self.ticket_callback
        self.add_item(btn_ticket)

    def get_product(self):
        if self.product_data and self.product_data.get("name"):
            return self.product_data
        try:
            data = load_json()
            return data.get("products", {}).get(self.product_id, {}) or self.product_data or {}
        except:
            return self.product_data or {}

    async def buy_callback(self, interaction: discord.Interaction):
        p = self.get_product()
        pname = p.get("name") or self.product_id
        modal = OrderModal(
            product_name=pname,
            product_id=self.product_id,
            bot_ref=self.bot_ref or bot_instance
        )
        await interaction.response.send_modal(modal)

    async def features_callback(self, interaction: discord.Interaction):
        p = self.get_product()
        features = p.get("features", [])
        if not features:
            features_text = "No detailed features specified for this item."
        elif isinstance(features, str):
            features_text = features
        else:
            features_text = "\n".join([f if f.startswith("✅") else f"✅ {f}" for f in features])

        embed = discord.Embed(
            description=f"## ✨ Features: {p.get('name', self.product_id)}\n\n{features_text}",
            color=discord.Color.from_rgb(239, 68, 68),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"ID: {self.product_id} • NULL System")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def ticket_callback(self, interaction: discord.Interaction):
        data = load_json()
        support_url = data.get("config", {}).get("support_url") or SUPPORT_URL
        buy_instr = data.get("config", {}).get("buy_instructions") or BUY_INSTRUCTIONS
        p = self.get_product()
        pname = p.get("name") or self.product_id

        embed = discord.Embed(
            description=f"## 🎫 Support & Order Ticket — {pname}\n\n{buy_instr}\n\n🔗 **Support Channel:** {support_url}",
            color=discord.Color.from_rgb(239, 68, 68),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"ID: {self.product_id} • NULL System")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def pricing_callback(self, interaction: discord.Interaction):
        p = self.get_product()
        p1 = p.get("price_1d", "₹100")
        p7 = p.get("price_7d", "₹500")
        p30 = p.get("price_30d", "₹1,200")
        plife = p.get("price_lifetime", "₹2,500")

        embed = discord.Embed(
            description=f"## 💰 Pricing (INR): {p.get('name', self.product_id)}",
            color=discord.Color.from_rgb(239, 68, 68),
            timestamp=datetime.now()
        )
        embed.add_field(name="⏱️ 1 Day Access", value=f"**`{p1}`**", inline=True)
        embed.add_field(name="📅 7 Days Access", value=f"**`{p7}`**", inline=True)
        embed.add_field(name="🗓️ 30 Days Access", value=f"**`{p30}`**", inline=True)
        embed.add_field(name="♾️ Lifetime Access", value=f"**`{plife}`**", inline=True)
        embed.set_footer(text="Prices in INR (₹) • Click 'Buy / Order' to purchase")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def status_callback(self, interaction: discord.Interaction):
        p = self.get_product()
        status = p.get("status", "🟢 Undetected")
        compat = p.get("compatibility", "Windows 10 / 11 | Intel & AMD")
        stock = p.get("stock", "In Stock")

        embed = discord.Embed(
            description=f"## 🛡️ Status: {p.get('name', self.product_id)}",
            color=discord.Color.from_rgb(239, 68, 68),
            timestamp=datetime.now()
        )
        embed.add_field(name="Detection Status", value=f"**{status}**", inline=True)
        embed.add_field(name="Stock Level", value=f"**`{stock}`**", inline=True)
        embed.add_field(name="System Compatibility", value=f"**`{compat}`**", inline=False)
        embed.set_footer(text="Maintained by NULL Dev Team")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CustomMessageView(discord.ui.View):
    """Interactive Action Buttons for custom announcements, store plans, and messages"""
    def __init__(self, bot_ref=None, buy_enabled: bool = True, support_url: str = None):
        super().__init__(timeout=None)
        self.bot_ref = bot_ref or bot_instance
        if buy_enabled:
            order_btn = discord.ui.Button(
                label="🛒 Buy / Order",
                style=discord.ButtonStyle.success,
                emoji="💳",
                custom_id="null_custom_buy"
            )
            async def _on_buy(interaction: discord.Interaction):
                modal = OrderModal(product_name="In-Store Plan", product_id="custom_plan", bot_ref=self.bot_ref)
                await interaction.response.send_modal(modal)
            order_btn.callback = _on_buy
            self.add_item(order_btn)

        url = support_url or SUPPORT_URL
        if url:
            support_btn = discord.ui.Button(label="💬 Support Ticket", style=discord.ButtonStyle.link, url=url, emoji="🎟️")
            self.add_item(support_btn)

class CatalogCategorySelect(discord.ui.Select):
    def __init__(self, data: dict, bot_ref):
        self.data = data
        self.bot_ref = bot_ref
        
        categories = data.get("categories", {})
        options = []
        for cat_id, cat_data in categories.items():
            name = cat_data.get("name", cat_id)
            emoji = cat_data.get("emoji", "📁")
            options.append(discord.SelectOption(
                label=name[:100],
                value=cat_id,
                description=f"Browse {name} products"[:100],
                emoji=emoji if len(emoji) <= 3 else "📁"
            ))
        
        if not options:
            options.append(discord.SelectOption(label="No categories available", value="none"))

        super().__init__(
            placeholder="📂 Select a Product Category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("No categories found.", ephemeral=True)
            return

        cat_id = self.values[0]
        cat_info = self.data["categories"].get(cat_id, {})
        cat_name = cat_info.get("name", cat_id)

        # Find products in this category
        matched = []
        for pid, p in self.data.get("products", {}).items():
            if p.get("category", "").lower() == cat_name.lower():
                matched.append((pid, p))

        if not matched:
            await interaction.response.send_message(f"No products found under **{cat_name}**.", ephemeral=True)
            return

        # Build category selection view
        view = CatalogProductSelectView(self.data, matched, self.bot_ref)
        embed = discord.Embed(
            title=f"📂 Category: {cat_name.upper()}",
            description=f"Found **{len(matched)}** available products.\nSelect a product from the dropdown below to view full details.",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        for pid, p in matched[:10]:
            p1 = p.get("price_1d", "N/A")
            p7 = p.get("price_7d", "N/A")
            status = p.get("status", "🟢 Undetected")
            embed.add_field(
                name=f"{p.get('name')}",
                value=f"💰 1D: `{p1}` | 7D: `{p7}`\n🛡️ `{status}`",
                inline=False
            )
        embed.set_footer(text="NULL Catalog Browser")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class CatalogProductSelect(discord.ui.Select):
    def __init__(self, data: dict, products_list: list, bot_ref):
        self.data = data
        self.bot_ref = bot_ref
        
        options = []
        for pid, p in products_list[:25]:
            name = p.get("name", pid)
            options.append(discord.SelectOption(
                label=name[:100],
                value=pid,
                description=f"1D: {p.get('price_1d', 'N/A')} | 7D: {p.get('price_7d', 'N/A')}"[:100],
                emoji="🛒"
            ))

        super().__init__(
            placeholder="🛒 Select a Product to inspect...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        pid = self.values[0]
        product = self.data.get("products", {}).get(pid)
        if not product:
            await interaction.response.send_message("❌ Product data not found.", ephemeral=True)
            return
        
        # Build product card
        embed = build_product_embed(pid, product)
        view = ProductCardView(pid, product, self.bot_ref)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class CatalogProductSelectView(discord.ui.View):
    def __init__(self, data: dict, products_list: list, bot_ref):
        super().__init__(timeout=180)
        self.add_item(CatalogProductSelect(data, products_list, bot_ref))

class CatalogMainView(discord.ui.View):
    """Main view with interactive dropdown selector for all categories"""
    def __init__(self, data: dict, bot_ref):
        super().__init__(timeout=None)
        self.add_item(CatalogCategorySelect(data, bot_ref))

# =========================================================
# EMBED BUILDER
# =========================================================

def format_inr_price(val, default="N/A"):
    if not val:
        return default
    s = str(val).strip()
    if not s or s.lower() == "n/a":
        return default
    if s.isdigit():
        try:
            num = int(s)
            return f"₹{num:,}"
        except:
            return f"₹{s}"
    if not s.startswith(("₹", "$", "€", "£")):
        return f"₹{s}"
    return s

def build_product_embed(product_id: str, product: dict) -> discord.Embed:
    """Builds an aesthetic, highly polished Discord Embed for a given product with permanent Red accent"""
    # Title
    raw_title = product.get('embed_title') or product.get('name', 'Unknown Product')
    if not any(raw_title.startswith(emoji) for emoji in ["🛒", "💎", "⚡", "🎯", "🌐", "🔐", "🎥", "🛡️", "📦"]):
        title_str = f"🛒 {raw_title}"
    else:
        title_str = raw_title

    # Accent color: STRICTLY RED (Permanent, not changeable)
    color_obj = discord.Color.from_rgb(239, 68, 68)

    desc = product.get('description', '').strip() or "No description provided."
    description_text = f"## {title_str}\n{desc}"

    embed = discord.Embed(
        description=description_text,
        color=color_obj,
        timestamp=datetime.now()
    )

    # Category, Status & Stock (3 columns inline)
    cat = product.get('category', 'General')
    status = product.get('status', '🟢 Undetected')
    stock = product.get('stock', 'In Stock')
    compat = product.get('compatibility', 'Windows 10 / 11 (All Builds) | Intel & AMD')

    embed.add_field(name="📁 Category", value=f"**{cat}**", inline=True)
    embed.add_field(name="🛡️ Status", value=f"**{status}**", inline=True)
    embed.add_field(name="📦 Stock", value=f"**{stock}**", inline=True)

    # Pricing grid (full-width for clean readability)
    p1 = format_inr_price(product.get('price_1d'), "₹100")
    p7 = format_inr_price(product.get('price_7d'), "₹500")
    p30 = format_inr_price(product.get('price_30d'), "₹1,200")
    plife = format_inr_price(product.get('price_lifetime'), "₹2,500")

    pricing_text = (
        f"• **1 Day**: **{p1}**\n"
        f"• **7 Days**: **{p7}**\n"
        f"• **30 Days**: **{p30}**\n"
        f"• **Lifetime**: **{plife}**"
    )
    embed.add_field(name="💰 Pricing Plans (INR)", value=pricing_text, inline=False)
    embed.add_field(name="💻 Compatibility", value=f"**{compat}**", inline=False)

    # Key Highlights / Features (clean checklist)
    features = product.get('features', [])
    if isinstance(features, str):
        features = [f.strip() for f in features.split("\n") if f.strip()]

    if features:
        cleaned_features = []
        for f in features:
            f = f.strip()
            if not f:
                continue
            if not f.startswith("✅"):
                f = f"✅ {f}"
            cleaned_features.append(f"**{f}**")
        if cleaned_features:
            embed.add_field(name="✨ Key Highlights", value="\n".join(cleaned_features[:10]), inline=False)

    # Media / Banners (Supports direct URL, CDN links, and attachments)
    thumb = product.get('thumbnail_url') or product.get('thumbnail')
    if thumb and isinstance(thumb, str) and thumb.strip().startswith(('http://', 'https://')):
        embed.set_thumbnail(url=thumb.strip())

    img = product.get('banner_url') or product.get('image_url') or product.get('image')
    if img and isinstance(img, str) and img.strip().startswith(('http://', 'https://')):
        embed.set_image(url=img.strip())

    # Footer - matches web preview exactly (ID: {product_id} • NULL System)
    embed.set_footer(text=f"ID: {product_id} • NULL System")
    return embed

# =========================================================
# DISCORD BOT COG
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class ProductBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_json()

    def reload_data(self):
        self.data = load_json()

    def get_showcase_channel_id(self) -> int:
        """Fetch configured showcase channel ID from dynamic json or .env fallback"""
        cid = self.data.get("config", {}).get("showcase_channel_id", "0")
        try:
            val = int(cid)
            return val if val != 0 else DEFAULT_SHOWCASE_CHANNEL_ID
        except:
            return DEFAULT_SHOWCASE_CHANNEL_ID

    def get_log_channel_id(self) -> int:
        """Fetch configured audit log channel ID"""
        cid = self.data.get("config", {}).get("log_channel_id", "0")
        try:
            val = int(cid)
            return val if val != 0 else DEFAULT_LOG_CHANNEL_ID
        except:
            return DEFAULT_LOG_CHANNEL_ID

    def is_admin(self, member: discord.Member) -> bool:
        """Verify if user is Administrator, Bot Owner, or holds the configured ADMIN_ROLE_ID"""
        if member.id == OWNER_ID:
            return True
        if member.guild_permissions.administrator:
            return True
        if ADMIN_ROLE_ID != 0:
            for role in member.roles:
                if role.id == ADMIN_ROLE_ID:
                    return True
        return False

    async def log_action(self, title: str, description: str, user: discord.User = None):
        """Sends an audit log embed to LOG_CHANNEL_ID"""
        log_id = self.get_log_channel_id()
        if not log_id:
            return
        channel = self.bot.get_channel(log_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title=f"🛡️ AUDIT: {title}",
            description=description,
            color=discord.Color.dark_purple(),
            timestamp=datetime.now()
        )
        if user:
            embed.set_author(name=f"{user.name} ({user.id})", icon_url=user.display_avatar.url if user.display_avatar else None)
        embed.set_footer(text="NULL Security Audit")
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Failed to write audit log: {e}")

    # =========================================================
    # AUTOCOMPLETE PROVIDERS
    # =========================================================

    async def product_autocomplete(self, interaction: discord.Interaction, current: str):
        choices = []
        current = current.lower()
        for pid, p in self.data.get("products", {}).items():
            name = p.get("name", pid)
            if current in name.lower() or current in pid.lower():
                choices.append(app_commands.Choice(name=f"{name} ({p.get('category', 'Gen')})", value=pid))
            if len(choices) >= 25:
                break
        return choices

    async def category_autocomplete(self, interaction: discord.Interaction, current: str):
        choices = []
        current = current.lower()
        for cat_id, cat in self.data.get("categories", {}).items():
            name = cat.get("name", cat_id)
            if current in name.lower() or current in cat_id.lower():
                choices.append(app_commands.Choice(name=name, value=name))
            if len(choices) >= 25:
                break
        return choices

    # =========================================================
    # MENTION & QUERY HANDLER
    # =========================================================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check mention
        bot_mention = f"<@{self.bot.user.id}>"
        bot_mention_nick = f"<@!{self.bot.user.id}>"

        if bot_mention in message.content or bot_mention_nick in message.content:
            # Track analytics
            self.data.setdefault("analytics", {})["total_queries"] = self.data.get("analytics", {}).get("total_queries", 0) + 1
            save_json(self.data)

            raw = message.content.replace(bot_mention, "").replace(bot_mention_nick, "").strip()
            if not raw:
                # Show master catalog view
                embed = discord.Embed(
                    title=f"∅ {BOT_NAME} - PRODUCT CATALOG",
                    description=(
                        f"Welcome to **{BOT_NAME}**. Select a category from the dropdown below to explore our verified software and products.\n\n"
                        f"💡 **Quick Search:** Type `@{self.bot.user.name} <product name>`\n"
                        f"🌐 **Support:** [Click here to join]({SUPPORT_URL})"
                    ),
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"Developed by NULL • {len(self.data.get('products', {}))} products active")
                view = CatalogMainView(self.data, self.bot)
                await message.reply(embed=embed, view=view, mention_author=False)
                return

            # Search by keyword or exact name
            query = raw.lower()
            matched_id = None
            matched_product = None

            for pid, p in self.data.get("products", {}).items():
                if query == p.get("name", "").lower() or query == pid.lower():
                    matched_id, matched_product = pid, p
                    break
                for kw in p.get("keywords", []):
                    if query == kw.lower():
                        matched_id, matched_product = pid, p
                        break
                if matched_id:
                    break

            if matched_product:
                # Increment views
                matched_product["views_count"] = matched_product.get("views_count", 0) + 1
                save_json(self.data)
                
                embed = build_product_embed(matched_id, matched_product)
                view = ProductCardView(matched_id, matched_product, self.bot)
                await message.reply(embed=embed, view=view, mention_author=False)
                return

            # Check if keyword matches a category
            for cat_id, cat_info in self.data.get("categories", {}).items():
                if query == cat_info.get("name", "").lower() or query == cat_id.lower():
                    cat_name = cat_info.get("name", cat_id)
                    products_in_cat = [
                        (pid, p) for pid, p in self.data.get("products", {}).items()
                        if p.get("category", "").lower() == cat_name.lower()
                    ]
                    if products_in_cat:
                        view = CatalogProductSelectView(self.data, products_in_cat, self.bot)
                        embed = discord.Embed(
                            title=f"📂 Category: {cat_name.upper()}",
                            description=f"Showing **{len(products_in_cat)}** products in this category.",
                            color=discord.Color.purple()
                        )
                        for pid, p in products_in_cat[:8]:
                            embed.add_field(
                                name=f"{p.get('name')}",
                                value=f"💰 1D: `{p.get('price_1d', 'N/A')}` | 7D: `{p.get('price_7d', 'N/A')}`\n🛡️ `{p.get('status', '🟢 Undetected')}`",
                                inline=False
                            )
                        await message.reply(embed=embed, view=view, mention_author=False)
                        return

            # Not found
            embed = discord.Embed(
                title="❌ Product Not Found",
                description=f"No active listing matches `{raw}`.",
                color=discord.Color.red()
            )
            embed.add_field(name="💡 Suggestions", value=f"• Mention `@{self.bot.user.name}` without text to open the interactive dropdown\n• Use `/catalog` to view all categories", inline=False)
            embed.set_footer(text=f"NULL Systems • Type @{self.bot.user.name}")
            await message.reply(embed=embed, mention_author=False)

    # =========================================================
    # CHANNEL ID BROADCAST & SEND COMMANDS
    # =========================================================

    @app_commands.command(
        name="product_send",
        description="Send a rich product card directly to a designated Channel ID or selected channel"
    )
    @app_commands.describe(
        product="Product to send (choose from suggestions)",
        channel="Target channel to send product to (optional)",
        channel_id="Raw channel ID to send product to (optional, overrides channel picker)",
        ping="Alert ping (e.g. @everyone, @here, or leave empty)"
    )
    @app_commands.autocomplete(product=product_autocomplete)
    async def product_send(
        self,
        interaction: discord.Interaction,
        product: str,
        channel: discord.TextChannel = None,
        channel_id: str = None,
        ping: str = None
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied: Admin permissions required.", ephemeral=True)
            return

        if product not in self.data.get("products", {}):
            await interaction.response.send_message("❌ Product ID not found.", ephemeral=True)
            return

        # Determine target channel
        target_channel = None
        if channel_id:
            try:
                target_channel = self.bot.get_channel(int(channel_id.strip()))
            except:
                pass
        elif channel:
            target_channel = channel
        else:
            default_id = self.get_showcase_channel_id()
            if default_id:
                target_channel = self.bot.get_channel(default_id)

        if not target_channel:
            await interaction.response.send_message(
                "❌ Target channel could not be resolved! Please specify a channel or configure `SHOWCASE_CHANNEL_ID`.",
                ephemeral=True
            )
            return

        product_data = self.data["products"][product]
        embed = build_product_embed(product, product_data)
        view = ProductCardView(product, product_data, self.bot)

        content = ping if ping in ["@everyone", "@here"] or (ping and ping.startswith("<@&")) else None

        try:
            sent_msg = await target_channel.send(content=content, embed=embed, view=view)
            
            # Analytics update
            self.data.setdefault("analytics", {})["products_sent"] = self.data.get("analytics", {}).get("products_sent", 0) + 1
            save_json(self.data)

            # Audit log
            await self.log_action(
                title="Product Sent to Channel",
                description=f"Admin {interaction.user.mention} broadcasted **{product_data.get('name')}** to {target_channel.mention} (`{target_channel.id}`).",
                user=interaction.user
            )

            await interaction.response.send_message(
                f"✅ **{product_data.get('name')}** successfully sent to {target_channel.mention}!\n🔗 [Jump to Message]({sent_msg.jump_url})",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ Bot does not have permission to send messages in {target_channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to send product: {e}", ephemeral=True)

    @app_commands.command(
        name="catalog_send",
        description="Send an interactive catalog selector to a target Channel ID"
    )
    @app_commands.describe(
        channel="Target text channel",
        channel_id="Raw channel ID"
    )
    async def catalog_send(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel = None,
        channel_id: str = None
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        target_channel = None
        if channel_id:
            try:
                target_channel = self.bot.get_channel(int(channel_id.strip()))
            except:
                pass
        elif channel:
            target_channel = channel
        else:
            default_id = self.get_showcase_channel_id()
            if default_id:
                target_channel = self.bot.get_channel(default_id)

        if not target_channel:
            await interaction.response.send_message("❌ Target channel could not be found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"∅ {BOT_NAME} - PRODUCT CATALOG",
            description=(
                f"Welcome to the official **{BOT_NAME}** catalog.\n"
                "Browse through our verified software and services using the interactive dropdown menu below.\n\n"
                f"💎 **Instant Delivery & Support:** [Join Support Server]({SUPPORT_URL})\n"
                "🛡️ All listings are actively tested and monitored."
            ),
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"NULL Systems • Verified Catalog")
        view = CatalogMainView(self.data, self.bot)

        try:
            msg = await target_channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Interactive catalog posted to {target_channel.mention}!\n🔗 [Jump]({msg.jump_url})", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error sending catalog: {e}", ephemeral=True)

    @app_commands.command(
        name="showcase_publish",
        description="Publish all catalog products with action buttons into the showcase channel ID"
    )
    @app_commands.describe(
        channel="Target channel (defaults to configured showcase channel)"
    )
    async def showcase_publish(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel = None
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        target = channel or self.bot.get_channel(self.get_showcase_channel_id())
        if not target:
            await interaction.response.send_message("❌ Showcase channel not found! Use `/config_set` or specify a channel.", ephemeral=True)
            return

        products = self.data.get("products", {})
        if not products:
            await interaction.response.send_message("📭 No products in database to publish.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Header banner
        header = discord.Embed(
            title=f"∅ {BOT_NAME} - OFFICIAL PRODUCT REPOSITORY",
            description=(
                f"Welcome to the official showcase of **{BOT_NAME}**.\n"
                "All items below feature instant access, automated security updates, and dedicated support.\n\n"
                f"🌐 Support Portal: {SUPPORT_URL}\n"
                "─────────────────────────────────────────"
            ),
            color=discord.Color.purple()
        )
        await target.send(embed=header)

        published_count = 0
        for pid, p in products.items():
            embed = build_product_embed(pid, p)
            view = ProductCardView(pid, p, self.bot)
            await target.send(embed=embed, view=view)
            published_count += 1
            await asyncio.sleep(0.8)  # prevent rate limit

        await interaction.followup.send(f"✅ Successfully published **{published_count}** products to {target.mention}!", ephemeral=True)

    @app_commands.command(
        name="send_message",
        description="Send a custom message or announcement to a specific channel (e.g. Internal-Plans)"
    )
    @app_commands.describe(
        channel="Target channel to send the message to",
        message="Message content to send (supports line breaks)",
        as_embed="Send as a stylish NULL embed card? (Default: True)",
        title="Custom title for the embed",
        ping="Alert ping (@everyone, @here)",
        add_buy_button="Include interactive 'Buy / Order' button? (Default: True)"
    )
    @app_commands.choices(ping=[
        app_commands.Choice(name="None", value="none"),
        app_commands.Choice(name="@everyone", value="@everyone"),
        app_commands.Choice(name="@here", value="@here")
    ])
    async def send_message_cmd(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str,
        as_embed: bool = True,
        title: str = "💎 BOT UPDATE",
        ping: str = "none",
        add_buy_button: bool = True
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        content = None if ping == "none" else ping

        try:
            if as_embed:
                embed = discord.Embed(
                    title=title,
                    description=message.replace("\\n", "\n"),
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"{BOT_NAME} System • Bot Announcement")
                view = CustomMessageView(self.bot, buy_enabled=add_buy_button) if add_buy_button else None
                sent = await channel.send(content=content, embed=embed, view=view)
            else:
                full_text = f"{content}\n{message}" if content else message
                sent = await channel.send(content=full_text.replace("\\n", "\n"))

            await self.log_action("Custom Message Dispatched", f"Admin {interaction.user.mention} sent message to {channel.mention}", interaction.user)
            await interaction.response.send_message(
                f"✅ Message successfully sent to {channel.mention}!\n🔗 [Jump to Message]({sent.jump_url})",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ Bot lacks permission to send messages in {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to send message: {e}", ephemeral=True)

    @app_commands.command(
        name="category_set_channel",
        description="Link a store category to its dedicated channel (e.g. Internal-Plans -> #Internal-Plans)"
    )
    @app_commands.describe(
        category="Category to link (autocomplete)",
        channel="Target channel"
    )
    @app_commands.autocomplete(category=category_autocomplete)
    async def category_set_channel(
        self,
        interaction: discord.Interaction,
        category: str,
        channel: discord.TextChannel
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        cat_found = None
        for cid, cdata in self.data.get("categories", {}).items():
            if cdata.get("name", "").lower() == category.lower() or cid.lower() == category.lower():
                cdata["channel_id"] = str(channel.id)
                cat_found = cdata.get("name", category)
                break

        if not cat_found:
            cid = category.lower().replace(" ", "_")
            self.data.setdefault("categories", {})[cid] = {
                "name": category,
                "emoji": "💎",
                "channel_id": str(channel.id),
                "created_at": datetime.now().isoformat()
            }
            cat_found = category

        save_json(self.data)
        await self.log_action("Category Linked to Channel", f"Category **{cat_found}** linked to {channel.mention}", interaction.user)
        await interaction.response.send_message(
            f"✅ Category **{cat_found}** is now linked to {channel.mention} (`{channel.id}`)!",
            ephemeral=True
        )

    @app_commands.command(
        name="category_broadcast",
        description="Broadcast all products belonging to a category directly to its linked channel"
    )
    @app_commands.describe(
        category="Category to broadcast (autocomplete)",
        channel="Override target channel (optional)"
    )
    @app_commands.autocomplete(category=category_autocomplete)
    async def category_broadcast(
        self,
        interaction: discord.Interaction,
        category: str,
        channel: discord.TextChannel = None
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        target_channel = channel
        if not target_channel:
            for cid, cdata in self.data.get("categories", {}).items():
                if cdata.get("name", "").lower() == category.lower():
                    chan_id = int(cdata.get("channel_id", "0") or "0")
                    if chan_id != 0:
                        target_channel = self.bot.get_channel(chan_id)
                    break

        if not target_channel:
            default_id = self.get_showcase_channel_id()
            if default_id:
                target_channel = self.bot.get_channel(default_id)

        if not target_channel:
            await interaction.response.send_message("❌ No target channel found! Please link a channel with `/category_set_channel` or specify one.", ephemeral=True)
            return

        matched = [
            (pid, p) for pid, p in self.data.get("products", {}).items()
            if p.get("category", "").lower() == category.lower()
        ]
        if not matched:
            await interaction.response.send_message(f"📭 No products found under category **{category}**.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        for pid, p in matched:
            embed = build_product_embed(pid, p)
            view = ProductCardView(pid, p, self.bot)
            await target_channel.send(embed=embed, view=view)
            await asyncio.sleep(0.8)

        await interaction.followup.send(f"✅ Successfully sent **{len(matched)}** {category} products to {target_channel.mention}!", ephemeral=True)

    @app_commands.command(
        name="sync_all_plans",
        description="Auto-detects matching store channels (#Ext-Lite, #Int-Basic, etc.) and posts plan cards"
    )
    async def sync_all_plans(self, interaction: discord.Interaction):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        products = self.data.get("products", {})
        if not products:
            await interaction.response.send_message("📭 No plans registered.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        synced = 0
        skipped = []
        for pid, p in products.items():
            ch = find_matching_channel_for_plan(self.bot, p.get("name", pid))
            if ch:
                embed = build_product_embed(pid, p)
                view = ProductCardView(pid, p, self.bot)
                try:
                    await ch.send(embed=embed, view=view)
                    synced += 1
                    await asyncio.sleep(0.8)
                except Exception as e:
                    skipped.append(f"{p.get('name')} (Send error: {e})")
            else:
                skipped.append(f"{p.get('name')} (Channel not found)")

        msg = f"✅ **Auto-Sync Complete!** Posted **{synced}/{len(products)}** plans into their respective channels."
        if skipped:
            msg += f"\n⚠️ Skipped: {', '.join(skipped[:6])}"
        await self.log_action("Auto-Sync Plans", f"Admin {interaction.user.mention} synced {synced} plans across store channels.", interaction.user)
        await interaction.followup.send(msg, ephemeral=True)

    # =========================================================
    # PRODUCT & CATEGORY MANAGEMENT
    # =========================================================

    @app_commands.command(name="product_add", description="Add a new product with full specifications")
    @app_commands.describe(
        name="Product name",
        category="Category name (autocomplete)",
        description="Detailed description",
        price_1d="1 Day price (e.g. $10)",
        price_7d="7 Days price (e.g. $50)",
        price_30d="30 Days / Monthly price (e.g. $120)",
        price_lifetime="Lifetime price (e.g. $250)",
        status="Detection status",
        compatibility="Compatible OS/hardware",
        features="Features (comma separated)",
        keywords="Keywords (comma separated)",
        image_file="Upload product image file directly (PNG/JPG)",
        banner_url="Or direct image banner URL (optional)",
        thumbnail_url="Thumbnail icon URL (optional)",
        auto_announce="Automatically broadcast to showcase channel ID?"
    )
    @app_commands.autocomplete(category=category_autocomplete)
    @app_commands.choices(status=[
        app_commands.Choice(name="🟢 Undetected", value="🟢 Undetected"),
        app_commands.Choice(name="🟡 Updating / Testing", value="🟡 Updating / Testing"),
        app_commands.Choice(name="🔴 Detected / Out of Stock", value="🔴 Detected / Out of Stock"),
        app_commands.Choice(name="🔵 Maintenance", value="🔵 Maintenance")
    ])
    async def product_add(
        self,
        interaction: discord.Interaction,
        name: str,
        category: str,
        description: str,
        price_1d: str,
        price_7d: str,
        price_30d: str = "N/A",
        price_lifetime: str = "N/A",
        status: str = "🟢 Undetected",
        compatibility: str = "Windows 10 / 11 | Intel & AMD",
        features: str = "",
        keywords: str = "",
        image_file: discord.Attachment = None,
        banner_url: str = "",
        thumbnail_url: str = "",
        auto_announce: bool = False
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        cat_id = category.lower().replace(" ", "_")
        if cat_id not in self.data.get("categories", {}):
            # Auto-create category if not found
            self.data.setdefault("categories", {})[cat_id] = {
                "name": category,
                "emoji": "📁",
                "created_at": datetime.now().isoformat()
            }

        product_id = name.lower().replace(" ", "_") + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
        features_list = [f.strip() for f in features.split(",") if f.strip()]
        keywords_list = [k.strip() for k in keywords.split(",") if k.strip()]
        keywords_list.append(name.lower())

        resolved_img = image_file.url if image_file else banner_url

        new_product = {
            "name": name,
            "category": category,
            "description": description,
            "price_1d": price_1d,
            "price_7d": price_7d,
            "price_30d": price_30d,
            "price_lifetime": price_lifetime,
            "status": status,
            "compatibility": compatibility,
            "stock": "In Stock",
            "features": features_list,
            "keywords": keywords_list,
            "banner_url": resolved_img,
            "image_url": resolved_img,
            "thumbnail_url": thumbnail_url,
            "views_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        self.data.setdefault("products", {})[product_id] = new_product
        save_json(self.data)

        # Audit log
        await self.log_action("Product Created", f"Added **{name}** (`{product_id}`) under **{category}**", interaction.user)

        embed = discord.Embed(
            title="✅ Product Created Successfully",
            description=f"**{name}** has been registered in the database.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="📂 Category", value=category, inline=True)
        embed.add_field(name="🛡️ Status", value=status, inline=True)
        embed.add_field(name="💰 1D / 7D / 30D / Life", value=f"`{price_1d}` | `{price_7d}` | `{price_30d}` | `{price_lifetime}`", inline=False)
        embed.set_footer(text=f"Product ID: {product_id} • NULL System")

        await interaction.response.send_message(embed=embed)

        # Auto-announce to showcase channel if requested
        if auto_announce:
            showcase_id = self.get_showcase_channel_id()
            if showcase_id:
                chan = self.bot.get_channel(showcase_id)
                if chan:
                    card_embed = build_product_embed(product_id, new_product)
                    view = ProductCardView(product_id, new_product, self.bot)
                    try:
                        await chan.send(content=f"🚨 **NEW PRODUCT RELEASE** — **{name}** is now available!", embed=card_embed, view=view)
                    except Exception as e:
                        print(f"⚠️ Auto announce failed: {e}")

    @app_commands.command(name="product_edit", description="Edit any field of an existing product")
    @app_commands.describe(
        product="Product to edit (autocomplete)",
        name="New name",
        category="New category",
        description="New description",
        price_1d="New 1D price",
        price_7d="New 7D price",
        price_30d="New 30D price",
        price_lifetime="New Lifetime price",
        status="New status",
        compatibility="New compatibility info",
        stock="Stock status",
        image_file="Upload new product image directly",
        banner_url="New banner URL (or type 'clear')",
        thumbnail_url="New thumbnail URL (or type 'clear')"
    )
    @app_commands.autocomplete(product=product_autocomplete, category=category_autocomplete)
    @app_commands.choices(status=[
        app_commands.Choice(name="🟢 Undetected", value="🟢 Undetected"),
        app_commands.Choice(name="🟡 Updating / Testing", value="🟡 Updating / Testing"),
        app_commands.Choice(name="🔴 Detected / Out of Stock", value="🔴 Detected / Out of Stock"),
        app_commands.Choice(name="🔵 Maintenance", value="🔵 Maintenance")
    ])
    async def product_edit(
        self,
        interaction: discord.Interaction,
        product: str,
        name: str = None,
        category: str = None,
        description: str = None,
        price_1d: str = None,
        price_7d: str = None,
        price_30d: str = None,
        price_lifetime: str = None,
        status: str = None,
        compatibility: str = None,
        stock: str = None,
        image_file: discord.Attachment = None,
        banner_url: str = None,
        thumbnail_url: str = None
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        if product not in self.data.get("products", {}):
            await interaction.response.send_message("❌ Product not found.", ephemeral=True)
            return

        p = self.data["products"][product]
        if name: p["name"] = name
        if category: p["category"] = category
        if description: p["description"] = description
        if price_1d: p["price_1d"] = price_1d
        if price_7d: p["price_7d"] = price_7d
        if price_30d: p["price_30d"] = price_30d
        if price_lifetime: p["price_lifetime"] = price_lifetime
        if status: p["status"] = status
        if compatibility: p["compatibility"] = compatibility
        if stock: p["stock"] = stock

        if image_file:
            p["banner_url"] = image_file.url
            p["image_url"] = image_file.url
        elif banner_url:
            if banner_url.lower() in ["clear", "none", "remove", "delete"]:
                p["banner_url"] = ""
                p["image_url"] = ""
            else:
                p["banner_url"] = banner_url
                p["image_url"] = banner_url

        if thumbnail_url:
            if thumbnail_url.lower() in ["clear", "none", "remove", "delete"]:
                p["thumbnail_url"] = ""
            else:
                p["thumbnail_url"] = thumbnail_url

        p["updated_at"] = datetime.now().isoformat()
        save_json(self.data)
        await self.log_action("Product Edited", f"Updated product **{p.get('name')}** (`{product}`)", interaction.user)

        embed = discord.Embed(
            title="✅ Product Updated",
            description=f"Changes saved for **{p['name']}**.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"ID: {product} • NULL System")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="product_set_image", description="Upload or set an image/banner for any product")
    @app_commands.describe(
        product="Product to update (autocomplete)",
        image_file="Upload image directly from your device (PNG/JPG)",
        image_url="Or paste direct image URL (Discord CDN, Imgur, etc.)",
        mode="Display as large card banner or top-right thumbnail"
    )
    @app_commands.autocomplete(product=product_autocomplete)
    @app_commands.choices(mode=[
        app_commands.Choice(name="🖼️ Large Banner (Bottom of Card)", value="banner"),
        app_commands.Choice(name="📌 Thumbnail Icon (Top-Right of Card)", value="thumbnail")
    ])
    async def product_set_image(
        self,
        interaction: discord.Interaction,
        product: str,
        image_file: discord.Attachment = None,
        image_url: str = None,
        mode: str = "banner"
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        if product not in self.data.get("products", {}):
            await interaction.response.send_message("❌ Product not found.", ephemeral=True)
            return

        p = self.data["products"][product]
        target_url = None
        if image_file:
            target_url = image_file.url
        elif image_url:
            target_url = image_url.strip()

        if not target_url or target_url.lower() in ["remove", "clear", "none", "delete"]:
            if mode == "thumbnail":
                p["thumbnail_url"] = ""
            else:
                p["banner_url"] = ""
                p["image_url"] = ""
            p["updated_at"] = datetime.now().isoformat()
            save_json(self.data)
            await self.log_action("Product Image Removed", f"Cleared {mode} image for **{p.get('name')}**", interaction.user)
            await interaction.response.send_message(f"✅ Removed {mode} image from **{p.get('name')}**.", ephemeral=True)
            return

        if mode == "thumbnail":
            p["thumbnail_url"] = target_url
        else:
            p["banner_url"] = target_url
            p["image_url"] = target_url
        p["updated_at"] = datetime.now().isoformat()
        save_json(self.data)

        await self.log_action("Product Image Updated", f"Set {mode} image for **{p.get('name')}**", interaction.user)
        preview_embed = build_product_embed(product, p)
        await interaction.response.send_message(
            content=f"✅ **[SUCCESS]** Successfully updated image for **{p.get('name')}**! Preview card:",
            embed=preview_embed,
            ephemeral=True
        )

    @app_commands.command(name="status_set", description="Quickly toggle the detection/availability status of a product")
    @app_commands.describe(
        product="Product to update (autocomplete)",
        status="New status"
    )
    @app_commands.autocomplete(product=product_autocomplete)
    @app_commands.choices(status=[
        app_commands.Choice(name="🟢 Undetected", value="🟢 Undetected"),
        app_commands.Choice(name="🟡 Updating / Testing", value="🟡 Updating / Testing"),
        app_commands.Choice(name="🔴 Detected / Out of Stock", value="🔴 Detected / Out of Stock"),
        app_commands.Choice(name="🔵 Maintenance", value="🔵 Maintenance")
    ])
    async def status_set(self, interaction: discord.Interaction, product: str, status: str):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        if product not in self.data.get("products", {}):
            await interaction.response.send_message("❌ Product not found.", ephemeral=True)
            return

        p = self.data["products"][product]
        old_status = p.get("status", "Unknown")
        p["status"] = status
        p["updated_at"] = datetime.now().isoformat()
        save_json(self.data)

        await self.log_action("Status Updated", f"Product **{p.get('name')}** status changed: `{old_status}` ➔ `{status}`", interaction.user)

        embed = discord.Embed(
            title="🛡️ Status Updated",
            description=f"**{p['name']}** is now marked as **{status}**.",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="product_delete", description="Permanently delete a product")
    @app_commands.describe(product="Product to delete (autocomplete)")
    @app_commands.autocomplete(product=product_autocomplete)
    async def product_delete(self, interaction: discord.Interaction, product: str):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        if product not in self.data.get("products", {}):
            await interaction.response.send_message("❌ Product not found.", ephemeral=True)
            return

        p_name = self.data["products"][product].get("name", product)
        del self.data["products"][product]
        save_json(self.data)

        await self.log_action("Product Deleted", f"Deleted product **{p_name}** (`{product}`)", interaction.user)

        embed = discord.Embed(
            title="🗑️ Product Deleted",
            description=f"Product **{p_name}** has been removed from the database.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="product_info", description="View full product card and details")
    @app_commands.describe(product="Product to inspect (autocomplete)")
    @app_commands.autocomplete(product=product_autocomplete)
    async def product_info_cmd(self, interaction: discord.Interaction, product: str):
        if product not in self.data.get("products", {}):
            await interaction.response.send_message("❌ Product not found.", ephemeral=True)
            return

        p_data = self.data["products"][product]
        p_data["views_count"] = p_data.get("views_count", 0) + 1
        save_json(self.data)

        embed = build_product_embed(product, p_data)
        view = ProductCardView(product, p_data, self.bot)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="product_list", description="List all products grouped by category")
    async def product_list(self, interaction: discord.Interaction):
        products = self.data.get("products", {})
        if not products:
            await interaction.response.send_message("📭 No products available.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📋 {BOT_NAME} - Complete Product Inventory",
            description=f"Total active listings: **{len(products)}**",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        grouped = {}
        for pid, p in products.items():
            cat = p.get("category", "General")
            grouped.setdefault(cat, []).append((pid, p))

        for cat, items in grouped.items():
            text = ""
            for pid, p in items[:6]:
                status_icon = "🟢" if "Undetected" in p.get("status", "") else "🔴" if "Detected" in p.get("status", "") else "🟡"
                text += f"{status_icon} **{p.get('name')}** — 1D: `{p.get('price_1d', 'N/A')}` | 7D: `{p.get('price_7d', 'N/A')}`\n"
            if len(items) > 6:
                text += f"*...and {len(items)-6} more*"
            embed.add_field(name=f"📁 {cat} ({len(items)})", value=text or "Empty", inline=False)

        embed.set_footer(text=f"NULL Systems • Type /product_send to broadcast")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="catalog", description="Open the interactive product catalog")
    async def catalog_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"∅ {BOT_NAME} - PRODUCT CATALOG",
            description=(
                f"Browse our complete inventory using the dropdown menu below.\n\n"
                f"🌐 Support Portal: {SUPPORT_URL}"
            ),
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="NULL Catalog Matrix")
        view = CatalogMainView(self.data, self.bot)
        await interaction.response.send_message(embed=embed, view=view)

    # =========================================================
    # CATEGORY COMMANDS
    # =========================================================

    @app_commands.command(name="category_add", description="Create a new category")
    @app_commands.describe(name="Category name", emoji="Emoji icon (optional)")
    async def category_add(self, interaction: discord.Interaction, name: str, emoji: str = "📁"):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        cat_id = name.lower().replace(" ", "_")
        if cat_id in self.data.get("categories", {}):
            await interaction.response.send_message("❌ Category already exists.", ephemeral=True)
            return

        self.data.setdefault("categories", {})[cat_id] = {
            "name": name,
            "emoji": emoji,
            "created_at": datetime.now().isoformat()
        }
        save_json(self.data)

        await self.log_action("Category Added", f"Added category **{name}**", interaction.user)
        embed = discord.Embed(title="✅ Category Added", description=f"{emoji} **{name}**", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="category_list", description="List all registered categories")
    async def category_list(self, interaction: discord.Interaction):
        categories = self.data.get("categories", {})
        if not categories:
            await interaction.response.send_message("📭 No categories registered.", ephemeral=True)
            return

        embed = discord.Embed(title="📋 Registered Categories", color=discord.Color.purple(), timestamp=datetime.now())
        for cat_id, cat_data in categories.items():
            name = cat_data.get("name", cat_id)
            emoji = cat_data.get("emoji", "📁")
            count = len([p for p in self.data.get("products", {}).values() if p.get("category", "").lower() == name.lower()])
            embed.add_field(name=f"{emoji} {name}", value=f"`{count}` products attached", inline=True)

        embed.set_footer(text="NULL System")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="category_delete", description="Delete a category")
    @app_commands.describe(category="Category name (autocomplete)")
    @app_commands.autocomplete(category=category_autocomplete)
    async def category_delete(self, interaction: discord.Interaction, category: str):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        cat_id = category.lower().replace(" ", "_")
        if cat_id not in self.data.get("categories", {}):
            await interaction.response.send_message("❌ Category not found.", ephemeral=True)
            return

        # Check if products exist in category
        products = [p for p in self.data.get("products", {}).values() if p.get("category", "").lower() == category.lower()]
        if products:
            await interaction.response.send_message(f"❌ Cannot delete: Category still contains {len(products)} products.", ephemeral=True)
            return

        del self.data["categories"][cat_id]
        save_json(self.data)
        await self.log_action("Category Deleted", f"Deleted category **{category}**", interaction.user)
        await interaction.response.send_message(f"✅ Category **{category}** deleted.")

    # =========================================================
    # PROMO CODES
    # =========================================================

    @app_commands.command(name="promo_add", description="Create a discount promo code")
    @app_commands.describe(code="Promo code (e.g. NULL20)", discount="Discount amount (e.g. 20%)", description="Description", max_uses="Max uses")
    async def promo_add(self, interaction: discord.Interaction, code: str, discount: str, description: str = "", max_uses: int = 100):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        code_upper = code.upper().strip()
        self.data.setdefault("promos", {})[code_upper] = {
            "discount": discount,
            "description": description,
            "uses_left": max_uses,
            "active": True
        }
        save_json(self.data)

        await self.log_action("Promo Created", f"Promo **{code_upper}** created for `{discount}` discount.", interaction.user)
        embed = discord.Embed(title="🎟️ Promo Code Created", description=f"Code: `{code_upper}`\nDiscount: `{discount}`\nUses: `{max_uses}`", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="promo_check", description="Verify a promo code")
    @app_commands.describe(code="Promo code to check")
    async def promo_check(self, interaction: discord.Interaction, code: str):
        code_upper = code.upper().strip()
        promo = self.data.get("promos", {}).get(code_upper)
        if not promo or not promo.get("active") or promo.get("uses_left", 0) <= 0:
            await interaction.response.send_message(f"❌ Promo code `{code_upper}` is invalid or expired.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎟️ Valid Promo Code!",
            description=f"Code: **{code_upper}**\nDiscount: **{promo.get('discount')}**\n{promo.get('description')}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Mention code when opening an order ticket")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="promo_list", description="List all active promo codes")
    async def promo_list(self, interaction: discord.Interaction):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        promos = self.data.get("promos", {})
        if not promos:
            await interaction.response.send_message("📭 No active promo codes.", ephemeral=True)
            return

        embed = discord.Embed(title="🎟️ Active Promo Codes", color=discord.Color.gold())
        for c, p in promos.items():
            status = "🟢 Active" if p.get("active") and p.get("uses_left", 0) > 0 else "🔴 Inactive"
            embed.add_field(name=c, value=f"Discount: `{p.get('discount')}` | Uses: `{p.get('uses_left')}` | {status}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =========================================================
    # REVIEWS & RATINGS
    # =========================================================

    @app_commands.command(name="review_add", description="Add a customer review and rating for a product")
    @app_commands.describe(
        product="Product to review (autocomplete)",
        rating="Rating from 1 to 5 stars",
        comment="Your review comment"
    )
    @app_commands.autocomplete(product=product_autocomplete)
    @app_commands.choices(rating=[
        app_commands.Choice(name="⭐⭐⭐⭐⭐ 5 Stars - Outstanding", value=5),
        app_commands.Choice(name="⭐⭐⭐⭐ 4 Stars - Great", value=4),
        app_commands.Choice(name="⭐⭐⭐ 3 Stars - Average", value=3),
        app_commands.Choice(name="⭐⭐ 2 Stars - Below Expectations", value=2),
        app_commands.Choice(name="⭐ 1 Star - Poor", value=1)
    ])
    async def review_add(self, interaction: discord.Interaction, product: str, rating: int, comment: str):
        if product not in self.data.get("products", {}):
            await interaction.response.send_message("❌ Product not found.", ephemeral=True)
            return

        p_name = self.data["products"][product].get("name", product)
        reviews = self.data.setdefault("reviews", {}).setdefault(product, [])
        
        reviews.append({
            "user_name": interaction.user.name,
            "user_id": interaction.user.id,
            "rating": rating,
            "comment": comment,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        save_json(self.data)

        stars = "⭐" * rating
        embed = discord.Embed(
            title="⭐ Review Submitted!",
            description=f"Thank you for reviewing **{p_name}**!\n\n**Rating:** {stars}\n**Comment:** \"{comment}\"",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="NULL Verified Customer Feedback")
        await interaction.response.send_message(embed=embed)

    # =========================================================
    # BACKUP & CONFIGURATION COMMANDS
    # =========================================================

    @app_commands.command(name="backup", description="Instantly export and download the product database file")
    async def backup_cmd(self, interaction: discord.Interaction):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        if not os.path.exists(DATA_FILE):
            await interaction.response.send_message("❌ Data file missing.", ephemeral=True)
            return

        file = discord.File(DATA_FILE, filename=f"null_product_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        await interaction.response.send_message("📦 **NULL Database Backup**:", file=file, ephemeral=True)

    @app_commands.command(name="config_set", description="Dynamically configure bot settings and channel IDs")
    @app_commands.describe(
        showcase_channel="Default channel to broadcast products and catalogs to",
        log_channel="Channel for security audit logs and order requests",
        support_url="Support server or ticket link"
    )
    async def config_set(
        self,
        interaction: discord.Interaction,
        showcase_channel: discord.TextChannel = None,
        log_channel: discord.TextChannel = None,
        support_url: str = None
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        conf = self.data.setdefault("config", {})
        if showcase_channel:
            conf["showcase_channel_id"] = str(showcase_channel.id)
        if log_channel:
            conf["log_channel_id"] = str(log_channel.id)
        if support_url:
            conf["support_url"] = support_url

        save_json(self.data)

        embed = discord.Embed(title="⚙️ Bot Configuration Updated", color=discord.Color.green(), timestamp=datetime.now())
        embed.add_field(name="Showcase Channel", value=f"<#{conf.get('showcase_channel_id', '0')}>", inline=True)
        embed.add_field(name="Audit Log Channel", value=f"<#{conf.get('log_channel_id', '0')}>", inline=True)
        embed.add_field(name="Support URL", value=conf.get("support_url", SUPPORT_URL), inline=False)
        embed.set_footer(text="NULL Systems")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="config_view", description="View current bot settings and linked channel IDs")
    async def config_view(self, interaction: discord.Interaction):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            return

        conf = self.data.get("config", {})
        showcase_id = conf.get("showcase_channel_id", str(DEFAULT_SHOWCASE_CHANNEL_ID))
        log_id = conf.get("log_channel_id", str(DEFAULT_LOG_CHANNEL_ID))

        embed = discord.Embed(title="⚙️ NULL System Configuration", color=discord.Color.purple(), timestamp=datetime.now())
        embed.add_field(name="Showcase Channel ID", value=f"`{showcase_id}` (<#{showcase_id}>)", inline=True)
        embed.add_field(name="Audit Log Channel ID", value=f"`{log_id}` (<#{log_id}>)", inline=True)
        embed.add_field(name="Bot Name", value=f"`{BOT_NAME}`", inline=True)
        embed.add_field(name="Admin Role ID", value=f"`{ADMIN_ROLE_ID}`", inline=True)
        embed.add_field(name="Support URL", value=conf.get("support_url", SUPPORT_URL), inline=False)
        embed.set_footer(text="NULL Security Matrix")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="View bot analytics, uptime, and database metrics")
    async def stats_cmd(self, interaction: discord.Interaction):
        uptime_sec = int(time.time() - BOT_START_TIME)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        analytics = self.data.get("analytics", {})
        embed = discord.Embed(
            title=f"📊 {BOT_NAME} - SYSTEM ANALYTICS",
            color=discord.Color.from_rgb(6, 182, 212),
            timestamp=datetime.now()
        )
        embed.add_field(name="Bot Ping", value=f"`{get_latency_ms(self.bot)}ms`", inline=True)
        embed.add_field(name="Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="Connected Guilds", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="Total Products", value=f"`{len(self.data.get('products', {}))}`", inline=True)
        embed.add_field(name="Total Categories", value=f"`{len(self.data.get('categories', {}))}`", inline=True)
        embed.add_field(name="Products Broadcasted", value=f"`{analytics.get('products_sent', 0)}`", inline=True)
        embed.add_field(name="User Inquiries", value=f"`{analytics.get('total_queries', 0)}`", inline=True)
        embed.set_footer(text="NULL Systems • Advanced Engine")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="null_help", description="Show comprehensive command directory and guide")
    async def null_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"∅ {BOT_NAME} - COMMAND MANUAL",
            description="Complete product management, broadcasting, and customer engagement system.",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📡 Channel Broadcasting",
            value=(
                "• `/product_send` — Broadcast a product card with action buttons to a Channel ID\n"
                "• `/catalog_send` — Post an interactive dropdown catalog to a Channel ID\n"
                "• `/showcase_publish` — Publish full product inventory to showcase channel"
            ),
            inline=False
        )
        embed.add_field(
            name="🛒 Product Management (Admin)",
            value=(
                "• `/product_add` — Register product (1D/7D/30D/Lifetime, status, banners)\n"
                "• `/product_edit` — Modify any existing product specification\n"
                "• `/status_set` — Quick toggle status (Undetected / Updating / Detected)\n"
                "• `/product_delete` — Permanently remove a product\n"
                "• `/product_list` — View all products grouped by category"
            ),
            inline=False
        )
        embed.add_field(
            name="📂 Categories & Tools",
            value=(
                "• `/category_add` & `/category_delete` — Category manager\n"
                "• `/promo_add` & `/promo_list` — Discount promo code system\n"
                "• `/backup` — Download instant database backup file\n"
                "• `/config_set` & `/config_view` — Set showcase and log channel IDs\n"
                "• `/stats` — Real-time performance and view counts"
            ),
            inline=False
        )
        embed.add_field(
            name="👥 User Interactions",
            value=(
                f"• `@{self.bot.user.name}` — Interactive catalog select menu\n"
                f"• `@{self.bot.user.name} <keyword>` — Instant product lookup\n"
                "• `/catalog` — Browse categories and products\n"
                "• `/review_add` — Submit 5-star customer feedback\n"
                "• `/promo_check` — Validate discount codes"
            ),
            inline=False
        )
        embed.set_footer(text="Engineered for NULL • All Rights Reserved")
        await interaction.response.send_message(embed=embed)

# =========================================================
# FLASK WEB API CONTROLLER (REPLACES CONSOLE CLI)
# =========================================================

@app.route('/api/status')
def api_status():
    """Returns real-time Discord bot gateway and store inventory status"""
    is_ready = bool(bot_instance and bot_instance.is_ready())
    data = load_json()
    uptime_sec = int(time.time() - BOT_START_TIME) if is_ready else 0
    bot_tag = f"{bot_instance.user.name}#{bot_instance.user.discriminator}" if (is_ready and bot_instance.user) else "Connecting..."
    bot_id = str(bot_instance.user.id) if (is_ready and bot_instance.user) else None
    
    guild_list = []
    if is_ready:
        for g in bot_instance.guilds:
            guild_list.append({"id": str(g.id), "name": g.name, "members": getattr(g, "member_count", 0)})

    return jsonify({
        "online": is_ready,
        "bot_name": BOT_NAME,
        "bot_user": bot_tag,
        "bot_id": bot_id,
        "latency_ms": get_latency_ms(bot_instance) if is_ready else 0,
        "guilds_count": len(bot_instance.guilds) if is_ready else 0,
        "guilds": guild_list,
        "products_count": len(data.get("products", {})),
        "categories_count": len(data.get("categories", {})),
        "products_sent": data.get("analytics", {}).get("products_sent", 0),
        "uptime_sec": uptime_sec,
        "currency_symbol": CURRENCY_SYMBOL,
        "showcase_channel_id": data.get("config", {}).get("showcase_channel_id", str(DEFAULT_SHOWCASE_CHANNEL_ID)),
        "log_channel_id": data.get("config", {}).get("log_channel_id", str(DEFAULT_LOG_CHANNEL_ID))
    })

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serves uploaded product images"""
    return send_from_directory(UPLOAD_DIR, filename)

@app.route('/api/upload_image', methods=['POST'])
def api_upload_image():
    """Uploads one or multiple product images, GIFs, or videos from user's PC"""
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Collect all files from any field
        files = []
        for key in request.files:
            files.extend(request.files.getlist(key))
        
        if not files:
            return jsonify({"success": False, "error": "No file uploaded in form data."}), 400
        
        uploaded = []
        allowed_exts = {
            '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.jfif', '.svg',
            '.mp4', '.webm', '.mov', '.m4v', '.ogg'
        }
        video_exts = {'.mp4', '.webm', '.mov', '.m4v', '.ogg'}
        
        for file in files:
            if not file or not file.filename:
                continue
            
            raw_ext = os.path.splitext(file.filename)[1].lower()
            if raw_ext not in allowed_exts:
                continue
            
            clean_name = f"media_{int(time.time())}_{os.urandom(3).hex()}{raw_ext}"
            dest_path = os.path.join(UPLOAD_DIR, clean_name)
            
            try:
                file.save(dest_path)
            except Exception as fe:
                print(f"❌ Error saving file {file.filename}: {fe}")
                continue
            
            rel_url = f"/uploads/{clean_name}"
            is_vid = raw_ext in video_exts
            uploaded.append({
                "url": rel_url,
                "image_url": rel_url,
                "filename": clean_name,
                "full_path": dest_path,
                "is_video": is_vid
            })
        
        if not uploaded:
            return jsonify({"success": False, "error": "No valid image, GIF, or video files could be saved."}), 400
        
        url_list = [u["image_url"] for u in uploaded]
        return jsonify({
            "success": True,
            "files": uploaded,
            "images": uploaded,
            "image_urls": url_list,
            "urls": url_list,
            "image_url": uploaded[0]["image_url"],
            "filename": uploaded[0]["filename"],
            "count": len(uploaded)
        })
    except Exception as e:
        print(f"❌ api_upload_image fatal error: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

@app.route('/api/save_channel', methods=['POST'])
def api_save_channel():
    """Saves the preferred target channel for a product so auto-detect remembers it"""
    payload = request.get_json(force=True, silent=True) or {}
    product_id = payload.get("product_id")
    channel_id = payload.get("channel_id")
    if not product_id:
        return jsonify({"success": False, "error": "Missing product_id"}), 400
    
    data = load_json()
    products = data.setdefault("products", {})
    if product_id not in products:
        if product_id in DEFAULT_PRODUCTS:
            products[product_id] = json.loads(json.dumps(DEFAULT_PRODUCTS[product_id]))
        else:
            products[product_id] = {"name": product_id}
    
    products[product_id]["saved_channel_id"] = str(channel_id) if channel_id else ""
    data["products"][product_id]["updated_at"] = datetime.now().isoformat()
    save_json(data)
    return jsonify({"success": True, "product_id": product_id, "saved_channel_id": channel_id})

@app.route('/api/channels')
def api_channels():
    """Returns all available server text channels across connected Discord guilds with saved mappings"""
    data = load_json()
    products = data.get("products", {})
    saved_channels = { pid: p.get("saved_channel_id", "") for pid, p in products.items() }

    if not bot_instance or not bot_instance.is_ready():
        return jsonify({"channels": [], "online": False, "saved_channels": saved_channels, "message": "Bot is connecting..."})
    
    channel_list = []
    for guild in bot_instance.guilds:
        for ch in guild.text_channels:
            can_send = ch.permissions_for(guild.me).send_messages if guild.me else True
            channel_list.append({
                "id": str(ch.id),
                "name": ch.name,
                "guild_name": guild.name,
                "guild_id": str(guild.id),
                "can_send": can_send
            })
    
    data = load_json()
    products = data.get("products", {})
    saved_channels = { pid: p.get("saved_channel_id", "") for pid, p in products.items() }
    
    return jsonify({"channels": channel_list, "online": True, "saved_channels": saved_channels})

@app.route('/api/match_channels')
def api_match_channels():
    """Detects matching store channels for each product (e.g. Ext-Lite -> #ext-lite)"""
    data = load_json()
    products = data.get("products", {})
    matches = []
    is_ready = bool(bot_instance and bot_instance.is_ready())

    for pid, p in products.items():
        ch = find_matching_channel_for_plan(bot_instance, p.get("name", pid)) if is_ready else None
        matches.append({
            "product_id": pid,
            "product_name": p.get("name", pid),
            "category": p.get("category", ""),
            "status": p.get("status", "🟢 Undetected"),
            "price_1d": p.get("price_1d", "N/A"),
            "matched_channel": {
                "id": str(ch.id),
                "name": ch.name,
                "guild": ch.guild.name
            } if ch else None
        })
    return jsonify({"online": is_ready, "matches": matches})

@app.route('/api/send_product', methods=['POST'])
def api_send_product():
    """Broadcasts a complete product embed card with interactive Buy/Feature buttons to a Discord channel"""
    if not bot_instance or not bot_instance.is_ready():
        return jsonify({"success": False, "error": "Discord bot is offline or still connecting."}), 503

    payload = request.get_json(force=True, silent=True) or {}
    product_id = payload.get("product_id")
    target_channel_id = payload.get("channel_id")
    ping = payload.get("ping", "none")

    data = load_json()
    products = data.setdefault("products", {})
    if product_id not in products:
        if product_id in DEFAULT_PRODUCTS:
            products[product_id] = json.loads(json.dumps(DEFAULT_PRODUCTS[product_id]))
            save_json(data)
        else:
            products[product_id] = {
                "name": payload.get("name", product_id),
                "category": payload.get("category", "Store Plans"),
                "description": payload.get("description", "Store plan details."),
                "price_1d": payload.get("price_1d", "₹100"),
                "price_7d": payload.get("price_7d", "₹500"),
                "price_30d": payload.get("price_30d", "₹1,200"),
                "price_lifetime": payload.get("price_lifetime", "₹2,500"),
                "status": payload.get("status", "🟢 Undetected"),
                "stock": payload.get("stock", "In Stock"),
                "compatibility": payload.get("compatibility", "Windows 10 / 11 | Intel & AMD"),
                "features": payload.get("features", []),
                "saved_channel_id": str(target_channel_id) if target_channel_id else "",
                "color": "red"
            }
            save_json(data)

    save_permanent = payload.get("save_permanent", True)

    if product_id in products:
        product = dict(products[product_id])
    else:
        product = {
            "name": payload.get("name", "Custom Plan"),
            "category": payload.get("category", "Store Plans"),
            "description": payload.get("description", "Store plan details."),
            "price_1d": payload.get("price_1d", "₹100"),
            "price_7d": payload.get("price_7d", "₹500"),
            "price_30d": payload.get("price_30d", "₹1,200"),
            "price_lifetime": payload.get("price_lifetime", "₹2,500"),
            "status": payload.get("status", "🟢 Undetected"),
            "stock": payload.get("stock", "In Stock"),
            "compatibility": payload.get("compatibility", "Windows 10 / 11 | Intel & AMD"),
            "features": payload.get("features", [])
        }

    # Overlay any custom edits from the editor
    editable_keys = [
        "name", "embed_title", "description", "category", "status", "stock",
        "price_1d", "price_7d", "price_30d", "price_lifetime", "compatibility",
        "features", "banner_url", "image_url", "images", "color", "saved_channel_id"
    ]
    product["color"] = "red"

    has_custom_edits = False
    for k in editable_keys:
        if k in payload and payload[k] is not None:
            product[k] = payload[k]
            has_custom_edits = True
            if k == "images" and isinstance(payload[k], list) and payload[k]:
                product["image_url"] = payload[k][0]
                product["banner_url"] = payload[k][0]
            elif k == "image_url" and payload[k]:
                product["banner_url"] = payload[k]
            elif k == "banner_url" and payload[k]:
                product["image_url"] = payload[k]

    # Save selected channel permanently if target_channel_id was provided
    if target_channel_id:
        product["saved_channel_id"] = str(target_channel_id)
        if product_id in products:
            products[product_id]["saved_channel_id"] = str(target_channel_id)

    # Save to database if requested
    if save_permanent and product_id in products:
        for k in editable_keys:
            if k in product:
                products[product_id][k] = product[k]
        products[product_id]["updated_at"] = datetime.now().isoformat()
        save_json(data)

    # If no channel specified, check saved channel first, then auto-match, then showcase
    if not target_channel_id:
        auto_ch = find_matching_channel_for_plan(bot_instance, product.get("name", product_id), product)
        if auto_ch:
            target_id = auto_ch.id
        else:
            cid = data.get("config", {}).get("showcase_channel_id", "0")
            try:
                target_id = int(cid)
            except:
                target_id = 0
    else:
        try:
            target_id = int(target_channel_id)
        except:
            return jsonify({"success": False, "error": "Invalid channel ID provided."}), 400

    if not target_id:
        return jsonify({
            "success": False, 
            "error": "No target channel selected and no auto-matched channel found for this plan."
        }), 400

    ping_str = "@everyone" if ping == "@everyone" else "@here" if ping == "@here" else None

    async def _send_product_task():
        ch = bot_instance.get_channel(target_id)
        if not ch:
            ch = await bot_instance.fetch_channel(target_id)

        main_embed = build_product_embed(product_id, product)
        embed_list = [main_embed]
        files_list = []

        # Gather list of all images for multi-image gallery
        raw_images = product.get("images") or []
        if isinstance(raw_images, str):
            raw_images = [img.strip() for img in raw_images.split(',') if img.strip()]
        img_list = [str(x).strip() for x in raw_images if str(x).strip()]
        if not img_list:
            single = product.get("image_url") or product.get("banner_url") or ""
            if single and str(single).strip():
                img_list = [str(single).strip()]

        # In Discord, multiple images only merge into the SAME BOX if all embeds share the exact same URL
        gallery_url = None
        if len(img_list) > 1:
            guild_id = getattr(ch.guild, 'id', 0)
            gallery_url = f"https://discord.com/channels/{guild_id}/{ch.id}"
            main_embed.url = gallery_url

        for i, img_item in enumerate(img_list[:10]):
            target_img_url = None
            if img_item.startswith(('http://', 'https://')):
                target_img_url = img_item
            else:
                # Check for local file upload in UPLOAD_DIR
                local_path = img_item
                if local_path.startswith('/uploads/'):
                    local_path = os.path.join(UPLOAD_DIR, os.path.basename(local_path))
                elif not os.path.isabs(local_path):
                    local_path = os.path.join(UPLOAD_DIR, os.path.basename(local_path))
                
                if os.path.exists(local_path):
                    fname = f"item_{i}_{os.path.basename(local_path)}"
                    files_list.append(discord.File(local_path, filename=fname))
                    target_img_url = f"attachment://{fname}"

            if target_img_url:
                is_vid = any(target_img_url.lower().split('?')[0].endswith(ext) for ext in ('.mp4', '.webm', '.mov', '.m4v', '.ogg'))
                if not is_vid:
                    if i == 0:
                        main_embed.set_image(url=target_img_url)
                    else:
                        if gallery_url:
                            sub_embed = discord.Embed(url=gallery_url, color=main_embed.color)
                        else:
                            sub_embed = discord.Embed(color=main_embed.color)
                        sub_embed.set_image(url=target_img_url)
                        embed_list.append(sub_embed)

        view = ProductCardView(product_id, product, bot_instance)
        try:
            bot_instance.add_view(view)
        except:
            pass
        if files_list:
            msg = await ch.send(content=ping_str, embeds=embed_list, file=files_list[0] if len(files_list)==1 else None, files=files_list if len(files_list)>1 else None, view=view)
        else:
            msg = await ch.send(content=ping_str, embeds=embed_list, view=view)

        # Update sent metrics
        data.setdefault("analytics", {})["products_sent"] = data.get("analytics", {}).get("products_sent", 0) + 1
        save_json(data)

        return {
            "channel_name": ch.name,
            "guild_name": ch.guild.name,
            "jump_url": msg.jump_url
        }

    try:
        future = asyncio.run_coroutine_threadsafe(_send_product_task(), bot_instance.loop)
        result = future.result(timeout=15)
        return jsonify({
            "success": True,
            "message": f"Successfully sent '{product.get('name')}' to #{result['channel_name']} ({result['guild_name']})!",
            "jump_url": result["jump_url"],
            "channel_name": result["channel_name"]
        })
    except discord.Forbidden:
        return jsonify({"success": False, "error": f"Bot lacks permissions to send messages or embeds in channel ID {target_id}."}), 403
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sync_all', methods=['POST'])
def api_sync_all():
    """1-Click Auto-Sync: Publishes all store plans to their respective matching server channels"""
    if not bot_instance or not bot_instance.is_ready():
        return jsonify({"success": False, "error": "Discord bot is offline or still connecting."}), 503

    data = load_json()
    products = data.get("products", {})
    if not products:
        return jsonify({"success": False, "error": "No products found in database to sync."}), 404

    matched = []
    unmatched = []
    for pid, p in products.items():
        ch = find_matching_channel_for_plan(bot_instance, p.get("name", pid))
        if ch:
            matched.append((pid, p, ch))
        else:
            unmatched.append(p.get("name", pid))

    if not matched:
        return jsonify({
            "success": False,
            "error": "No matching channels found! Ensure channel names contain plan names (e.g. #ext-lite, #ext-basic, #aim-assist).",
            "unmatched": unmatched
        }), 400

    async def _sync_all_task():
        results = []
        sent_count = 0
        for pid, p, chan in matched:
            try:
                embed = build_product_embed(pid, p)
                view = ProductCardView(pid, p, bot_instance)
                msg = await chan.send(embed=embed, view=view)
                sent_count += 1
                results.append({"name": p.get("name"), "channel": chan.name, "jump_url": msg.jump_url, "ok": True})
                await asyncio.sleep(0.5)
            except Exception as e:
                results.append({"name": p.get("name"), "channel": chan.name, "error": str(e), "ok": False})

        data.setdefault("analytics", {})["products_sent"] = data.get("analytics", {}).get("products_sent", 0) + sent_count
        save_json(data)
        return results, sent_count

    try:
        future = asyncio.run_coroutine_threadsafe(_sync_all_task(), bot_instance.loop)
        results, sent_count = future.result(timeout=60)
        return jsonify({
            "success": True,
            "synced_count": sent_count,
            "total_matched": len(matched),
            "results": results,
            "unmatched": unmatched
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/send_custom', methods=['POST'])
def api_send_custom():
    """Dispatches a custom announcement or store message to any Discord channel with Buy button"""
    if not bot_instance or not bot_instance.is_ready():
        return jsonify({"success": False, "error": "Discord bot is offline."}), 503

    payload = request.get_json(force=True, silent=True) or {}
    channel_id = payload.get("channel_id")
    title = payload.get("title", "💎 NULL BOT ANNOUNCEMENT").strip() or "💎 NULL BOT ANNOUNCEMENT"
    description = payload.get("description", "").strip()
    color_choice = payload.get("color", "red")
    ping = payload.get("ping", "none")
    buy_button = payload.get("buy_button", True)
    is_plain = payload.get("plain_text", False)

    if not channel_id:
        return jsonify({"success": False, "error": "Please select a target channel."}), 400
    if not description:
        return jsonify({"success": False, "error": "Message content cannot be empty."}), 400

    try:
        target_id = int(channel_id)
    except:
        return jsonify({"success": False, "error": "Invalid channel ID provided."}), 400

    embed_color = discord.Color.from_rgb(239, 68, 68)
    ping_str = "@everyone" if ping == "@everyone" else "@here" if ping == "@here" else None

    async def _send_custom_task():
        ch = bot_instance.get_channel(target_id)
        if not ch:
            ch = await bot_instance.fetch_channel(target_id)

        view = CustomMessageView(bot_instance, buy_enabled=buy_button) if buy_button else None
        if view:
            try:
                bot_instance.add_view(view)
            except:
                pass

        if is_plain:
            content_payload = f"{ping_str}\n{description}" if ping_str else description
            msg = await ch.send(content=content_payload, view=view)
        else:
            custom_desc = f"## {title}\n\n{description}" if title else description
            embed = discord.Embed(
                description=custom_desc,
                color=embed_color,
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"{BOT_NAME} Systems • Official Bot Announcement")
            msg = await ch.send(content=ping_str, embed=embed, view=view)

        return {"channel_name": ch.name, "guild_name": ch.guild.name, "jump_url": msg.jump_url}

    try:
        future = asyncio.run_coroutine_threadsafe(_send_custom_task(), bot_instance.loop)
        res = future.result(timeout=15)
        return jsonify({
            "success": True,
            "message": f"Successfully sent announcement to #{res['channel_name']} ({res['guild_name']})!",
            "jump_url": res["jump_url"]
        })
    except discord.Forbidden:
        return jsonify({"success": False, "error": "Bot lacks permission to post messages in that channel."}), 403
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/change_status', methods=['POST'])
def api_change_status():
    """Updates cheat detection status (Undetected / Updating / Detected) in the database"""
    payload = request.get_json(force=True, silent=True) or {}
    product_id = payload.get("product_id")
    new_status = payload.get("status")

    if not product_id or not new_status:
        return jsonify({"success": False, "error": "Missing product_id or status."}), 400

    data = load_json()
    if product_id not in data.get("products", {}):
        return jsonify({"success": False, "error": f"Product '{product_id}' not found."}), 404

    data["products"][product_id]["status"] = new_status
    data["products"][product_id]["updated_at"] = datetime.now().isoformat()
    save_json(data)
    return jsonify({"success": True, "product_id": product_id, "new_status": new_status})

@app.route('/api/edit_product', methods=['POST'])
def api_edit_product():
    """Edits pricing, compatibility, banner, or description for a product"""
    payload = request.get_json(force=True, silent=True) or {}
    product_id = payload.get("product_id")
    if not product_id:
        return jsonify({"success": False, "error": "Missing product_id."}), 400

    data = load_json()
    products = data.setdefault("products", {})
    if product_id not in products:
        if product_id in DEFAULT_PRODUCTS:
            products[product_id] = json.loads(json.dumps(DEFAULT_PRODUCTS[product_id]))
        else:
            products[product_id] = {"name": product_id, "category": "Store Plans", "description": ""}
    
    p = products[product_id]
    editable_fields = [
        "name", "category", "description", "price_1d", "price_7d",
        "price_30d", "price_lifetime", "status", "compatibility",
        "banner_url", "image_url", "saved_channel_id", "stock", "images"
    ]
    for field in editable_fields:
        if field in payload:
            p[field] = payload[field]
            if field == "banner_url" and payload[field]:
                p["image_url"] = payload[field]
            elif field == "image_url" and payload[field]:
                p["banner_url"] = payload[field]
            elif field == "images" and isinstance(payload[field], list) and payload[field]:
                p["image_url"] = payload[field][0]
                p["banner_url"] = payload[field][0]
    if "features" in payload:
        if isinstance(payload["features"], list):
            p["features"] = payload["features"]
        elif isinstance(payload["features"], str):
            p["features"] = [f.strip() for f in payload["features"].split(",") if f.strip()]

    p["color"] = "red"
    p["updated_at"] = datetime.now().isoformat()
    save_json(data)
    return jsonify({"success": True, "product": p})

@app.route('/api/add_product', methods=['POST'])
def api_add_product():
    """Adds a new product to the database from the web interface"""
    payload = request.get_json(force=True, silent=True) or {}
    name = payload.get("name", "").strip()
    category = payload.get("category", "Store Plans").strip()
    if not name:
        return jsonify({"success": False, "error": "Product name is required."}), 400

    data = load_json()
    product_id = re.sub(r'[^a-zA-Z0-9_]', '', name.lower().replace(' ', '_').replace('-', '_'))
    if not product_id:
        product_id = f"prod_{int(time.time())}"

    features = payload.get("features", [])
    if isinstance(features, str):
        features = [f.strip() for f in features.split(",") if f.strip()]

    new_prod = {
        "name": name,
        "category": category,
        "description": payload.get("description", f"High performance {name} package."),
        "price_1d": payload.get("price_1d", "₹100"),
        "price_7d": payload.get("price_7d", "₹500"),
        "price_30d": payload.get("price_30d", "₹1,200"),
        "price_lifetime": payload.get("price_lifetime", "₹2,500"),
        "status": payload.get("status", "🟢 Undetected"),
        "compatibility": payload.get("compatibility", "Windows 10 / 11 | Intel & AMD"),
        "stock": "In Stock",
        "features": features or ["Plug & Play", "24/7 Support"],
        "keywords": [name.lower(), category.lower()],
        "banner_url": payload.get("banner_url", ""),
        "image_url": payload.get("banner_url", ""),
        "thumbnail_url": "",
        "views_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    data.setdefault("products", {})[product_id] = new_prod
    save_json(data)
    return jsonify({"success": True, "product_id": product_id, "product": new_prod})

@app.route('/api/delete_product', methods=['POST'])
def api_delete_product():
    """Deletes a product from the database"""
    payload = request.get_json(force=True, silent=True) or {}
    product_id = payload.get("product_id")
    data = load_json()
    if product_id in data.get("products", {}):
        del data["products"][product_id]
        save_json(data)
        return jsonify({"success": True, "deleted": product_id})
    return jsonify({"success": False, "error": "Product not found."}), 404

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Retrieves or updates bot configuration settings"""
    data = load_json()
    if request.method == 'POST':
        payload = request.get_json(force=True, silent=True) or {}
        conf = data.setdefault("config", {})
        if "showcase_channel_id" in payload: conf["showcase_channel_id"] = str(payload["showcase_channel_id"])
        if "log_channel_id" in payload: conf["log_channel_id"] = str(payload["log_channel_id"])
        if "support_url" in payload: conf["support_url"] = str(payload["support_url"])
        save_json(data)
        return jsonify({"success": True, "config": conf})
    return jsonify({"config": data.get("config", {})})

@app.route('/api/backup', methods=['POST'])
def api_backup():
    """Triggers an instant database snapshot file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"web_backup_{timestamp}.json")
    try:
        shutil.copyfile(DATA_FILE, backup_path)
        return jsonify({"success": True, "file": backup_path, "timestamp": timestamp})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================================================
# BOT CORE INITIALIZATION
# =========================================================

class NullBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=["!", "null ", "NULL "],
            intents=intents,
            help_command=None
        )
        self.initialized = False
        global bot_instance
        bot_instance = self

    async def setup_hook(self):
        print("🔄 [NULL] Initializing bot subsystems...")
        try:
            await self.add_cog(ProductBot(self))
            print("✅ [NULL] ProductBot Cog initialized.")
        except Exception as e:
            print(f"❌ [NULL] Cog error: {e}")
            traceback.print_exc()

        # Register persistent views for all known products so buttons NEVER expire
        try:
            data = load_json()
            products = data.get("products", {})
            for pid, p in products.items():
                self.add_view(ProductCardView(pid, p, self))
            self.add_view(CustomMessageView(self, buy_enabled=True))
            print(f"✅ [NULL] Registered persistent button listeners for {len(products)} products.")
        except Exception as e:
            print(f"⚠️ [NULL] Failed to register persistent views: {e}")

        try:
            synced = await self.tree.sync()
            print(f"✅ [NULL] Synchronized {len(synced)} slash commands.")
        except Exception as e:
            print(f"❌ [NULL] Slash sync error: {e}")

        self.initialized = True
        self.status_rotator.start()
        print("✅ [NULL] Core engine ready!")

    async def on_interaction(self, interaction: discord.Interaction):
        # Global fallback listener for any component interaction so buttons respond instantly
        if interaction.type == discord.InteractionType.component and not interaction.response.is_done():
            cid = interaction.data.get("custom_id", "")
            if cid:
                try:
                    if cid == "null_custom_buy":
                        modal = OrderModal(product_name="In-Store Plan", product_id="custom_plan", bot_ref=self)
                        await interaction.response.send_modal(modal)
                        return

                    if cid.startswith("null_"):
                        parts = cid.split(":", 1)
                        action = parts[0]
                        pid = parts[1] if len(parts) > 1 else ""
                        data = load_json()
                        p = data.get("products", {}).get(pid, {})
                        pname = p.get("name") or pid

                        if action == "null_buy":
                            modal = OrderModal(product_name=pname, product_id=pid, bot_ref=self)
                            await interaction.response.send_modal(modal)
                            return
                        elif action == "null_feats":
                            feats = p.get("features", [])
                            ftext = "\n".join([f"🔹 **{f}**" for f in feats]) if feats else "No detailed features specified."
                            embed = discord.Embed(description=f"## ✨ Features: {pname}\n\n{ftext}", color=discord.Color.from_rgb(239, 68, 68))
                            embed.set_footer(text=f"NULL Systems • {pid}")
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                            return
                        elif action == "null_price":
                            embed = discord.Embed(description=f"## 💰 Pricing (INR): {pname}", color=discord.Color.from_rgb(239, 68, 68))
                            embed.add_field(name="⏱️ 1 Day Access", value=f"**`{p.get('price_1d', '₹100')}`**", inline=True)
                            embed.add_field(name="📅 7 Days Access", value=f"**`{p.get('price_7d', '₹500')}`**", inline=True)
                            embed.add_field(name="🗓️ 30 Days Access", value=f"**`{p.get('price_30d', '₹1,200')}`**", inline=True)
                            embed.add_field(name="♾️ Lifetime Access", value=f"**`{p.get('price_lifetime', '₹2,500')}`**", inline=True)
                            embed.set_footer(text="Prices in INR (₹) • Click 'Buy / Order' to purchase")
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                            return
                        elif action == "null_status":
                            embed = discord.Embed(description=f"## 🛡️ Status: {pname}", color=discord.Color.from_rgb(239, 68, 68))
                            embed.add_field(name="Detection Status", value=f"**{p.get('status', '🟢 Undetected')}**", inline=True)
                            embed.add_field(name="Stock Level", value=f"**`{p.get('stock', 'In Stock')}`**", inline=True)
                            embed.add_field(name="System Compatibility", value=f"**`{p.get('compatibility', 'Windows 10 / 11 | Intel & AMD')}`**", inline=False)
                            embed.set_footer(text="Maintained by NULL Dev Team")
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                            return
                    else:
                        # Old random button ID from before persistent update
                        embed = discord.Embed(
                            title="⚠️ Outdated Message",
                            description="This message was sent before the bot update. Please click **🚀 Send** on the website to post an updated card, or use `/catalog`!",
                            color=discord.Color.from_rgb(239, 68, 68)
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                except Exception as e:
                    print(f"⚠️ on_interaction fallback error: {e}")

    async def on_ready(self):
        port = int(os.environ.get("PORT") or os.environ.get("SERVER_PORT") or 10000)
        print("\n" + "="*60)
        print("         ∅ NULL - ADVANCED PRODUCT WEB SYSTEM")
        print("="*60)
        print(f"✅ Bot User:    {self.user.name}#{self.user.discriminator} ({self.user.id})")
        print(f"📊 Guilds:      {len(self.guilds)}")
        print(f"📝 Commands:    {len(self.tree.get_commands())}")
        print(f"🌐 Web Control: http://localhost:{port}")
        print("="*60 + "\n")

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"@NULL for products | Web Dashboard"
        )
        await self.change_presence(activity=activity)

    @tasks.loop(minutes=5)
    async def status_rotator(self):
        """Dynamic rotating activity status"""
        try:
            if self.initialized:
                server_count = len(self.guilds)
                data = load_json()
                product_count = len(data.get("products", {}))
                activity = discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"{product_count} Products | {server_count} Servers | /catalog"
                )
                await self.change_presence(activity=activity)
        except Exception as e:
            print(f"⚠️ Activity error: {e}")

    @status_rotator.before_loop
    async def before_status_rotator(self):
        await self.wait_until_ready()

# =========================================================
# MAIN RUNNER
# =========================================================

if __name__ == "__main__":
    try:
        # Start Flask dashboard in background daemon thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        port = int(os.environ.get("PORT") or os.environ.get("SERVER_PORT") or 10000)
        print(f"🚀 [NULL] Cyberpunk Web Dashboard running on port {port}")

        bot = NullBot()
        bot.run(TOKEN)

    except discord.errors.LoginFailure:
        print("❌ [NULL] Authentication Error: Invalid Discord bot token in .env")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 [NULL] Process terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ [NULL] Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)