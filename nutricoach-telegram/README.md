# 🤖 NutriCoach Telegram Bot

Hybrid system: Telegram Group (clients) + Web App (nutritionists + admin)

## Project Structure

```
nutricoach-telegram/
├── bot/
│   ├── main.py              ← START HERE — runs the bot
│   ├── scheduler.py         ← Daily check-ins, weekly summaries, expiry
│   └── handlers/
│       ├── message_handler.py  ← Handles all Telegram group messages
│       └── command_handler.py  ← /start /diet /progress /help /pause /resume
├── ai/
│   ├── gemini.py            ← Gemini AI integration + prompt builder
│   └── router.py            ← Full message processing pipeline
├── db/
│   ├── client.py            ← Supabase connection
│   ├── schema.sql           ← Run this in Supabase to create all tables
│   ├── nutritionists.py     ← Nutritionist account operations
│   ├── clients.py           ← Client record operations
│   ├── checkins.py          ← Daily check-in tracking
│   ├── messages.py          ← Chat message history
│   ├── queries.py           ← Pending query (escalation) management
│   └── ai_rules.py          ← AI instruction rules per client
├── config.py                ← All environment variables (import from here)
├── requirements.txt         ← Python dependencies
├── .env.example             ← Template — copy to .env and fill in keys
└── TECHNICAL_SPEC.md        ← Full technical documentation
```

## Setup Instructions

### Step 1: Set Up Supabase Database
1. Go to [supabase.com](https://supabase.com) and create a free project
2. Go to **SQL Editor** → **New Query**
3. Copy the entire contents of `db/schema.sql`
4. Paste and click **Run**
5. All 8 tables will be created

### Step 2: Get Your API Keys
- **Telegram Bot Token:** Go to [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token
- **Supabase Keys:** Your Supabase project → Settings → API → copy URL + anon key + service_role key
- **Gemini API Key:** [Google AI Studio](https://aistudio.google.com) → Get API Key

### Step 3: Configure .env
```bash
copy .env.example .env
# Open .env and fill in all the values
```

### Step 4: Install Dependencies
```bash
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Step 5: Run the Bot
```bash
python bot/main.py
```

You should see:
```
✅ Config validated — all required keys present.
✅ All handlers registered.
✅ Scheduler started — daily check-ins, weekly summaries, expiry checks active.
🔄 Development mode — starting polling...
   Bot is running. Press Ctrl+C to stop.
```

## Architecture
See `TECHNICAL_SPEC.md` for the complete technical documentation.
See `../FINAL_ARCHITECTURE.md` for the system-level vision.
