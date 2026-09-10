# NULL Bot 🚀

An advanced Discord product showcase bot and cyberpunk management web dashboard built with Python (`discord.py 2.x`), Flask, and modern cyber-themed UI.

---

## ✨ Features

- **🎮 Discord Bot Integration**:
  - Interactive product showcases with order modals, dynamic buttons, and features preview.
  - Channel auto-detection and persistence per product.
  - Slash commands (`/product_send`, `/catalog_send`, `/showcase_publish`, etc.) with autocomplete.
  - Audit logging channel for administrative tracking.
  - Status tracking with rotating Discord activity.

- **🌐 Cyberpunk Web Dashboard**:
  - Live product editing, real-time Discord preview, and direct broadcast to selected channels.
  - Aligned, responsive 4-tier pricing grid (1 Day, 7 Days, 30 Days, Lifetime).
  - Continuous animated GIF and video (`.mp4`, `.webm`, `.mov`) upload and playback with muted auto-looping.
  - Drag-and-drop file dropzone + `Ctrl+V` clipboard image/video paste support.
  - Custom announcement sender with audience pings (`@everyone`, `@here`).

---

## 📁 Project Structure

```
NULL-BOT/
├── main.py              # Discord bot + Flask backend server
├── index.html           # Cyberpunk Web Dashboard UI
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore file (secures .env and cache)
├── uploads/             # Media storage (images, GIFs, videos)
└── backups/             # Automatic JSON backups
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 installed.
- Git installed.

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd NULL-BOT

# Create virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

Set your bot credentials:
- `TOKEN`: Your Discord Bot Token (from Discord Developer Portal)
- `ADMIN_ROLE_ID`: Role ID allowed to manage products
- `OWNER_ID`: Your Discord User ID
- `SHOWCASE_CHANNEL_ID`: Default channel for announcements
- `LOG_CHANNEL_ID`: Audit logging channel ID
- `PORT`: Web dashboard port (defaults to 10000 or WispByte SERVER_PORT)

### 4. Run the Bot & Dashboard
```bash
python main.py
```
Open `http://localhost:10000` (or your configured `PORT`) in your browser to access the dashboard.

---

## 🌐 Hosting Guide

### Hosting on WispByte (Pterodactyl Panel)
1. Compress your project files into a `.zip` (exclude `__pycache__` and `venv`).
2. Go to your **WispByte Panel** → **Files** → Upload and extract the zip.
3. Edit `.env` with your bot token and channel IDs.
4. Go to **Network** / **Allocations** and check your assigned port.
5. In **Startup**, ensure `main.py` is the main file and Python 3.10+ is selected.
6. Click **Start** in the **Console**. The dashboard will be live at `http://YOUR_WISPBYTE_IP:YOUR_PORT`.

---

## 🔒 Security Note
Never commit your `.env` file or Discord Bot Token to any public git repository. The `.gitignore` file is already configured to protect your sensitive tokens and credentials.

---

## 📜 License
All Rights Reserved © 2026 NULL
