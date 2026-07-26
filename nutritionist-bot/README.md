# 🥗 Nutritionist Telegram Bot — V2

An AI-powered Telegram bot that acts as a nutrition accountability assistant inside private group chats. Built with Python + Gemini AI.

---

## How It Works

Each client gets a private Telegram group with 4 members:
1. **The Client** — the person following the nutrition plan
2. **The Caretaker** — family member who prepares food and provides support
3. **The Nutritionist** — can type directly in any group; bot detects and saves her messages but stays silent so she can speak directly
4. **The Bot** — sends daily/weekly check-ins, replies warmly, tracks everything

---

## Setup Guide (One-Time)

### Step 1 — Get a Bot Token

1. Open Telegram → message **@BotFather**
2. Type `/newbot` → follow prompts → copy the **token**
3. Still in @BotFather → `/setprivacy` → select your bot → choose **Disable**

> ⚠️ **Critical:** Without disabling privacy mode, the bot only sees messages that @mention it — not the free conversation. You MUST disable it.

> ⚠️ **Important:** If you already added the bot to a group BEFORE disabling privacy, remove it and re-add it. The setting only applies on re-join.

---

### Step 2 — Get Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**
3. Copy the key

---

### Step 3 — Set Up the Project

```bash
# Clone / navigate to the project
cd nutritionist-bot

# Create a virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env template
copy .env.example .env   # Windows
# or: cp .env.example .env  (Mac/Linux)
```

---

### Step 4 — Fill In `.env`

Open `.env` and fill in all values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash
COACH_NAME=Dr. Priya                    # Nutritionist's name
COACH_TELEGRAM_ID=123456789             # Nutritionist's Telegram user ID
DAILY_CHECKIN_HOUR=19                   # 7 PM check-in (24h format)
WEEKLY_CHECKIN_DAY=sun                  # Sunday weekly check-in
WEEKLY_CHECKIN_HOUR=18                  # 6 PM
TIMEZONE=Asia/Kolkata
```

**How to find your own Telegram user ID:**
- Message **@userinfobot** on Telegram → it will reply with your user ID

---

### Step 5 — Create Telegram Groups

For each client:
1. Create a new Telegram group
2. Add the client and caretaker
3. Add your bot (search by its username)

**Get the group chat ID:**
1. Send any message in the group
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find the message → look at `"chat": {"id": -100XXXXXXXXX}` (it's a negative number)

**Get user IDs** (client and caretaker):
- From the same `getUpdates` response → look at `"from": {"id": XXXXXXXXX}`

---

### Step 6 — Add Clients to the Database

**Option A: Using seed.py (recommended for demo)**

Open `seed.py` and fill in the placeholder values:

```python
DEMO_CLIENTS = [
    {
        "name": "Ananya Sharma",
        "telegram_group_id": "-1001234567890",    # ← your real group ID
        "customer_telegram_id": "987654321",       # ← client's user ID
        "caretaker_telegram_id": "111222333",      # ← caretaker's user ID
        "plan_summary": "Weight loss: 1400 kcal...",
    },
    ...
]
```

Then run:
```bash
python seed.py
```

**Option B: Using the /addclient command**

Once the bot is running, message it directly (DM):
```
/addclient -1001234567890 Ananya Sharma | Weight loss: 1400 kcal/day, no sugar, 3L water...
```

---

### Step 7 — Start the Bot

```bash
python main.py
```

You should see:
```
============================================================
  🥗  Nutritionist Telegram Bot  —  V2 (Python)
============================================================
  Coach     : Dr. Priya
  AI Model  : gemini-2.5-flash
  ...
✅ Bot is running! Press Ctrl+C to stop.
```

---

## Demo Script (What to Show the Client)

1. **Trigger an instant check-in** — DM the bot: `/testdaily`
   - Bot sends a personalised question to all active groups immediately

2. **Reply as the client** — In the group, type something realistic:
   > "Had 2 of 3 meals today, skipped lunch because of a meeting"

3. **Reply as the caretaker** — Add new information:
   > "She seemed very tired in the evening, barely ate dinner"

4. **Watch the bot** — It acknowledges both replies, connects them, and responds warmly

5. **Check stored data:**
   ```bash
   # Install DB Browser for SQLite (GUI)
   # Or use command line:
   sqlite3 data/nutrition_bot.db "SELECT name, adherence, energy_level, summary, needs_attention FROM checkins JOIN clients ON checkins.client_id = clients.id;"
   ```

6. **Check the /status command** — DM the bot: `/status`

---

## Available Commands (Nutritionist Only)

| Command | Description |
|---|---|
| `/testdaily` | Send daily check-in to all active groups NOW |
| `/testweekly` | Send weekly check-in to all active groups NOW |
| `/status` | View all active clients and their last check-in |
| `/addclient <group_id> <name> \| <plan>` | Add a new client |
| `/help` | Show all commands |

---

## Nutritionist Override (Manual Reply)

The nutritionist can type directly in any client group at any time.

- Bot **detects** her messages using her Telegram ID from `.env`
- Bot **saves** her message as `sender_role = 'nutritionist'` in the database
- Bot **stays silent** — it does not reply to her (so she can speak directly to the client)
- Her messages **become part of the AI's context** for that client's future responses

This means the AI always knows what the nutritionist has said, and will align its tone accordingly.

---

## Project Structure

```
nutritionist-bot/
├── main.py              # Entry point
├── config.py            # Environment variable loader
├── seed.py              # Demo data seeder
├── requirements.txt
├── .env.example
│
├── bot/
│   ├── handlers.py      # Core message handler
│   ├── commands.py      # Slash commands
│   └── scheduler.py     # Daily/weekly cron jobs
│
├── ai/
│   ├── gemini.py        # All Gemini API calls
│   └── prompts.py       # Prompt templates + extraction schema
│
├── db/
│   ├── database.py      # SQLAlchemy engine + sessions
│   ├── models.py        # ORM models (Client, Message, CheckIn)
│   └── queries.py       # Query helpers
│
└── data/
    └── nutrition_bot.db # SQLite file (auto-created, gitignored)
```

---

## Next Steps (After Demo)

- [ ] **PostgreSQL migration** — for 200+ concurrent clients
- [ ] **Coach dashboard** — web UI to view all client data and flags
- [ ] **Escalation alerts** — DM/email the coach when `needs_attention = True`
- [ ] **Automated onboarding** — guided flow to add new clients
- [ ] **Analytics** — weekly trend reports, adherence charts
- [ ] **Multi-language NLP** — richer Hindi/Hinglish support
