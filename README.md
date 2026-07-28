# 🇲🇾 Pro Clubs Malaysia Matchday Schedule Tracker & Poster Generator

Automated matchday schedule tracking and graphic poster generator for **Virtua CF** across **VPL Malaysia**, **VPG Malaysia**, and **LPM Malaysia**.

---

## 🚀 How to Run (No Antigravity Required!)

This project is 100% standalone and works on any **Mac, Windows, or Linux** machine with **Python 3.9+**.

### 1. Quick Setup (One-Time)

Open your Terminal or Command Prompt in this folder and run:

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

---

### 2. Running the Schedule Tracker & Poster Generator

Simply run:

```bash
python main.py
```

### What Happens Automatically:
1. **Fetches Fixtures**: Connects to VPL, VPG, and LPM APIs/websites in parallel.
2. **Filters Matchday Window**:
   - Running **Mon – Wed**: Generates the schedule & poster for **Current Week**.
   - Running **Thu – Sun**: Automatically shifts and generates the schedule & poster for **Next Week**.
3. **Downloads & Caches Crests**: Resolves official high-res team shields into `logo_cache/vpl_logos.json`.
4. **Generates Poster Graphic**: Renders a 1080x1080 Kickly-style matchday poster image (`matchday_poster.png`).
5. **Posts to Discord**: Automatically posts the text schedule and graphic poster payload to your Discord Webhook.

---

### 3. Running the Discord Slash Command Bot (`/schedule`)

If you want the bot running in the background so anyone in your Discord server can type `/schedule`:

```bash
python bot.py
```

---

## 🛠 Configuration (`.env`)

You can edit the `.env` file to customize settings or update tokens:

```env
CLUB_NAME=Virtua CF
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DISCORD_BOT_TOKEN=...
```

---

## 📦 Windows `.exe` Compilation

### Method A: Automated GitHub Cloud Build (Easiest)
We set up a free GitHub Actions workflow at [.github/workflows/build_windows.yml](file:///Users/brokepc/Library/Mobile%20Documents/com~apple~CloudDocs/Pro%20Clubs/.github/workflows/build_windows.yml).
1. Push your repository to GitHub.
2. Go to the **Actions** tab on GitHub.
3. Download the compiled **`pro_clubs_tracker-windows-exe.zip`** containing `pro_clubs_tracker.exe`!

---

### Method B: Building Directly on a Windows PC
On any Windows PC, open Command Prompt in this folder and run:

```cmd
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --name "pro_clubs_tracker" --add-data "assets;assets" --add-data "logo_cache;logo_cache" main.py
```

The compiled **`pro_clubs_tracker.exe`** will be created inside the `dist\` folder!
