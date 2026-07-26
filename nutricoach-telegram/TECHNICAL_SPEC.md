# ⚙️ NutriCoach — Full Technical Specification
### Complete Developer Reference: Database · Bot · AI · Web App · Deployment

> **This is the technical implementation document.**
> Read FINAL_ARCHITECTURE.md first for the "what and why."
> This document covers the "how" — every table, every function, every API, every file.

---

## 📁 Complete Folder & File Structure

```
nutricoach-telegram/
│
├── bot/
│   ├── __init__.py
│   ├── main.py                   ← Entry point — starts the bot
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── message_handler.py    ← Handles all incoming Telegram messages
│   │   ├── command_handler.py    ← Handles /start /diet /progress /help
│   │   └── member_handler.py     ← Handles members joining/leaving groups
│   ├── group_manager.py          ← Creates Telegram groups, adds members
│   └── scheduler.py              ← Sends daily check-ins at scheduled times
│
├── ai/
│   ├── __init__.py
│   ├── gemini.py                 ← Gemini API client & prompt builder
│   ├── router.py                 ← Decides: AI handles OR escalate to doctor
│   └── classifier.py             ← Classifies adherence: on_track/partial/off_track
│
├── db/
│   ├── __init__.py
│   ├── client.py                 ← Supabase client setup
│   ├── nutritionists.py          ← CRUD for nutritionist accounts
│   ├── clients.py                ← CRUD for client records
│   ├── checkins.py               ← CRUD for daily check-in records
│   ├── queries.py                ← CRUD for pending queries (escalations)
│   ├── messages.py               ← CRUD for chat message history
│   └── ai_rules.py               ← CRUD for AI instruction rules per client
│
├── api/
│   ├── __init__.py
│   └── webhook.py                ← FastAPI server exposing endpoints for web app
│
├── config.py                     ← All environment variables, constants
├── requirements.txt              ← Python dependencies
├── .env                          ← Secret keys (never commit this)
├── .env.example                  ← Template for .env
└── README.md                     ← Setup instructions

nutricoach-webapp/                ← (Built in Phase 2 — separate folder)
```

---

## 🗄️ Database Schema (Supabase / PostgreSQL)

### Table 1: `admins`
```sql
CREATE TABLE admins (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       TEXT UNIQUE NOT NULL,
  password    TEXT NOT NULL,              -- bcrypt hashed
  created_at  TIMESTAMPTZ DEFAULT now()
);
```

---

### Table 2: `nutritionists`
```sql
CREATE TABLE nutritionists (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name         TEXT NOT NULL,
  clinic_name       TEXT,
  email             TEXT UNIQUE NOT NULL,
  password          TEXT NOT NULL,        -- bcrypt hashed
  telegram_user_id  BIGINT UNIQUE,        -- nutritionist's Telegram account ID
  status            TEXT DEFAULT 'pending'
                    CHECK (status IN ('pending', 'active', 'paused', 'expired')),
  access_expiry     DATE,                 -- when their platform access expires
  created_at        TIMESTAMPTZ DEFAULT now(),
  approved_at       TIMESTAMPTZ,
  approved_by       UUID REFERENCES admins(id)
);
```

**Status values:**
- `pending` → signed up, waiting for admin approval
- `active` → approved, full access
- `paused` → admin manually paused (bot stops for all their clients)
- `expired` → access date passed (auto-set by scheduler)

---

### Table 3: `clients`
```sql
CREATE TABLE clients (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nutritionist_id     UUID REFERENCES nutritionists(id) ON DELETE CASCADE,
  full_name           TEXT NOT NULL,
  telegram_user_id    BIGINT,             -- client's Telegram account ID (set after they join)
  telegram_phone      TEXT,               -- used to send invite
  telegram_group_id   BIGINT,             -- the group chat ID created for this client
  program_type        TEXT,               -- e.g. "Weight Management", "PCOS", "Post-Pregnancy"
  program_duration    INTEGER,            -- in days
  program_start       DATE,
  program_end         DATE,               -- auto-computed: start + duration
  checkin_time        TIME DEFAULT '19:00:00',  -- 7:00 PM default
  diet_chart          TEXT,               -- plain text or markdown diet plan
  diet_chart_file_id  TEXT,               -- Telegram file_id if PDF uploaded
  status              TEXT DEFAULT 'active'
                      CHECK (status IN ('active', 'paused', 'expired', 'completed')),
  caretaker_name      TEXT,
  caretaker_telegram  BIGINT,
  created_at          TIMESTAMPTZ DEFAULT now()
);
```

---

### Table 4: `checkins`
```sql
CREATE TABLE checkins (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID REFERENCES clients(id) ON DELETE CASCADE,
  checkin_date      DATE NOT NULL,
  client_message    TEXT,                 -- what the client replied
  ai_reply          TEXT,                 -- what AI responded
  adherence_status  TEXT DEFAULT 'no_response'
                    CHECK (adherence_status IN ('on_track', 'partial', 'off_track', 'no_response')),
  override_status   TEXT,                 -- set by nutritionist manually (same values)
  override_by       UUID REFERENCES nutritionists(id),
  override_at       TIMESTAMPTZ,
  caretaker_note    TEXT,                 -- observation logged by caretaker that day
  energy_level      INTEGER CHECK (energy_level BETWEEN 1 AND 5),
  created_at        TIMESTAMPTZ DEFAULT now()
);
```

**Active status = override_status if set, otherwise adherence_status**

---

### Table 5: `pending_queries`
```sql
CREATE TABLE pending_queries (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID REFERENCES clients(id) ON DELETE CASCADE,
  nutritionist_id   UUID REFERENCES nutritionists(id),
  client_message    TEXT NOT NULL,        -- exact message from client that triggered escalation
  ai_assessment     TEXT,                 -- AI's reason for escalating
  ai_interim_reply  TEXT,                 -- what AI already told the client
  doctor_reply      TEXT,                 -- nutritionist's response (filled when resolved)
  status            TEXT DEFAULT 'pending'
                    CHECK (status IN ('pending', 'resolved', 'ai_handled')),
  resolved_at       TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT now()
);
```

---

### Table 6: `messages`
```sql
CREATE TABLE messages (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id     UUID REFERENCES clients(id) ON DELETE CASCADE,
  sender_role   TEXT NOT NULL
                CHECK (sender_role IN ('client', 'ai', 'nutritionist', 'caretaker', 'system')),
  sender_name   TEXT,
  content       TEXT NOT NULL,
  telegram_msg_id BIGINT,                -- Telegram's own message ID (for editing/pinning)
  sent_at       TIMESTAMPTZ DEFAULT now()
);
```

---

### Table 7: `ai_rules`
```sql
CREATE TABLE ai_rules (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nutritionist_id   UUID REFERENCES nutritionists(id) ON DELETE CASCADE,
  client_id         UUID REFERENCES clients(id) ON DELETE CASCADE,
                    -- NULL means it's a master rule for all this nutritionist's clients
  category          TEXT CHECK (category IN ('tone', 'language', 'medical', 'caretaker', 'other')),
  rule_text         TEXT NOT NULL,
  is_active         BOOLEAN DEFAULT true,
  created_at        TIMESTAMPTZ DEFAULT now()
);
```

---

### Table 8: `notification_log`
```sql
CREATE TABLE notification_log (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recipient_id  UUID,                    -- nutritionist or client id
  type          TEXT,                    -- 'expiry_warning', 'pending_query', 'checkin_sent', etc.
  message       TEXT,
  sent_at       TIMESTAMPTZ DEFAULT now()
);
```

---

## 🤖 Bot Architecture — How Every Piece Works

### How the Bot Receives Messages

The bot uses `python-telegram-bot` in **polling mode** (for development) and **webhook mode** (for production).

Every message from a Telegram group goes through this chain:

```
Telegram Group Message
        ↓
message_handler.py — receives raw message
        ↓
Identify sender role:
  • Is sender_id == client.telegram_user_id? → role = 'client'
  • Is sender_id == nutritionist.telegram_user_id? → role = 'nutritionist'
  • Is sender_id == client.caretaker_telegram? → role = 'caretaker'
  • Is sender_id == bot itself? → ignore (our own message)
        ↓
If role == 'nutritionist':
  → Save message to messages table (sender_role = 'nutritionist')
  → Check if there's a pending_query for this client → mark as resolved
  → Done (no AI processing for doctor messages)
        ↓
If role == 'caretaker':
  → Save message to messages table (sender_role = 'caretaker')
  → Save caretaker_note to today's checkin record
  → Done (no AI reply to caretaker)
        ↓
If role == 'client':
  → Save message to messages table (sender_role = 'client')
  → Send to AI router for processing
```

---

### AI Router Logic (`ai/router.py`)

```python
def route_message(client_id, message_text):
    """
    Returns: ('handle', ai_reply) OR ('escalate', interim_reply, assessment)
    """
    
    # Step 1: Load client context
    client = db.clients.get(client_id)
    nutritionist = db.nutritionists.get(client.nutritionist_id)
    
    # Step 2: Load AI rules for this client
    master_rules = db.ai_rules.get_master_rules(nutritionist.id)
    client_rules = db.ai_rules.get_client_rules(client_id)
    all_rules = master_rules + client_rules
    
    # Step 3: Load recent chat history (last 10 messages for context)
    history = db.messages.get_recent(client_id, limit=10)
    
    # Step 4: Build the full prompt and send to Gemini
    result = gemini.evaluate(
        client=client,
        rules=all_rules,
        history=history,
        new_message=message_text
    )
    
    # Step 5: Gemini returns a structured response:
    # {
    #   "action": "handle" OR "escalate",
    #   "adherence": "on_track" / "partial" / "off_track" / null,
    #   "energy_level": 1-5 or null,
    #   "reply": "the warm reply to send to client",
    #   "escalation_reason": "clinical reason if action=escalate"
    # }
    
    return result
```

---

### Gemini Prompt Structure (`ai/gemini.py`)

Every time a client sends a message, this is what we send to Gemini:

```
SYSTEM PROMPT (built dynamically):
───────────────────────────────────
You are NutriCoach AI, the clinical nutrition assistant for {nutritionist.full_name}.

MASTER RULES:
{master_rules joined as bullet points}

RULES SPECIFIC TO {client.full_name}:
{client_rules joined as bullet points}

CLIENT CONTEXT:
• Name: {client.full_name}
• Program: {client.program_type} ({days_remaining} days remaining)
• Diet Plan: {client.diet_chart}

RECENT CONVERSATION HISTORY:
{last 10 messages formatted as: [Role]: message}

YOUR TASK:
Read the client's new message and respond with a JSON object:
{
  "action": "handle" OR "escalate",
  "adherence": "on_track" / "partial" / "off_track" / null,
  "energy_level": 1 to 5 or null,
  "reply": "your warm response to the client",
  "escalation_reason": "why you are escalating (only if action=escalate)"
}

ESCALATION RULES — You MUST escalate (action=escalate) if:
1. Client reports physical pain, dizziness, nausea, or any symptom
2. Client asks to substitute a major meal or change macros
3. Client asks a medication-related question
4. Client reports an emergency

For escalation, reply with an interim message only:
"I understand! I've shared this with {nutritionist.full_name} — 
she will respond shortly. 👩‍⚕️"
───────────────────────────────────

USER MESSAGE:
{client.full_name}: {message_text}
```

---

### After AI Router Returns (`message_handler.py` continued)

```python
if result.action == 'handle':
    # 1. Send AI reply to Telegram group
    bot.send_message(group_id, result.reply)
    
    # 2. Save AI message to messages table
    db.messages.save(client_id, 'ai', result.reply)
    
    # 3. Update today's checkin record
    db.checkins.update_today(
        client_id,
        adherence=result.adherence,
        energy=result.energy_level,
        ai_reply=result.reply,
        client_message=message_text
    )

elif result.action == 'escalate':
    # 1. Send interim reply to Telegram group
    bot.send_message(group_id, result.reply)
    
    # 2. Save to pending_queries table
    query_id = db.queries.create(
        client_id=client_id,
        client_message=message_text,
        ai_assessment=result.escalation_reason,
        ai_interim_reply=result.reply
    )
    
    # 3. Save interim message to messages table
    db.messages.save(client_id, 'ai', result.reply)
    
    # 4. Web app will pick up the new pending_query and show alert
```

---

### Daily Check-in Scheduler (`bot/scheduler.py`)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def send_daily_checkins():
    """
    Runs every minute. Checks which clients need a check-in right now.
    """
    current_time = datetime.now().strftime('%H:%M')
    
    # Get all active clients whose check-in time matches current time
    due_clients = db.clients.get_due_for_checkin(current_time)
    
    for client in due_clients:
        # Don't send if client's nutritionist is paused/expired
        nutritionist = db.nutritionists.get(client.nutritionist_id)
        if nutritionist.status != 'active':
            continue
        
        # Don't send if client's plan is paused/expired
        if client.status != 'active':
            continue
        
        # Don't send if already sent today
        if db.checkins.sent_today(client.id):
            continue
        
        # Build personalised check-in message
        message = build_checkin_message(client)
        
        # Send to client's Telegram group
        bot.send_message(client.telegram_group_id, message)
        
        # Create empty checkin record for today
        db.checkins.create_today(client.id)

# Run every minute
scheduler.add_job(send_daily_checkins, 'interval', minutes=1)
```

---

### Group Manager (`bot/group_manager.py`)

Called when nutritionist adds a new client via the web app.

```python
async def create_client_group(client_id):
    """
    1. Create a new Telegram group
    2. Add bot to group
    3. Invite client via phone number
    4. Add nutritionist to group
    5. Send welcome message
    6. Send diet chart as file
    """
    client = db.clients.get(client_id)
    nutritionist = db.nutritionists.get(client.nutritionist_id)
    
    # Step 1: Create group via Telegram API
    group = await bot.create_group(
        title=f"{client.full_name} × NutriCoach"
    )
    group_id = group.id
    
    # Step 2: Invite client using their phone number
    # (Telegram API: invite_by_phone or generate invite link)
    invite_link = await bot.create_invite_link(group_id)
    await bot.send_message(
        chat_id=client.telegram_phone,   # send to client directly first
        text=f"🌿 {client.full_name}, Dr. {nutritionist.full_name} "
             f"has set up your NutriCoach program!\n\n"
             f"Join your personal group here:\n{invite_link}"
    )
    
    # Step 3: Add nutritionist to group (they must have Telegram)
    await bot.add_member(group_id, nutritionist.telegram_user_id)
    
    # Step 4: Add caretaker if exists
    if client.caretaker_telegram:
        await bot.add_member(group_id, client.caretaker_telegram)
    
    # Step 5: Save group_id to client record
    db.clients.update(client_id, telegram_group_id=group_id)
    
    # Step 6: Send welcome message
    await bot.send_message(group_id, build_welcome_message(client, nutritionist))
    
    # Step 7: Send diet chart as file attachment
    if client.diet_chart_file_id:
        await bot.send_document(group_id, client.diet_chart_file_id)
    else:
        await bot.send_message(group_id, f"📋 Your Diet Plan:\n\n{client.diet_chart}")
```

---

## 🌐 Web App API Endpoints (`api/webhook.py`)

The Python backend exposes a FastAPI server that the Next.js web app calls.

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Nutritionist login → returns JWT token |
| `POST` | `/auth/signup` | New nutritionist registration → status = pending |
| `POST` | `/auth/forgot-password` | Send OTP to email |
| `POST` | `/auth/reset-password` | Verify OTP + set new password |
| `GET` | `/auth/me` | Get current logged-in nutritionist |

### Nutritionist Dashboard
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/clients` | Get all clients for this nutritionist |
| `GET` | `/clients/:id` | Get single client full profile |
| `POST` | `/clients` | Add new client → triggers group creation |
| `PATCH` | `/clients/:id` | Update client info, diet chart, status |
| `DELETE` | `/clients/:id` | Archive/deactivate client |

### Check-ins & Chat
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/clients/:id/messages` | Get full chat history for a client |
| `POST` | `/clients/:id/messages` | Send message from nutritionist → goes to Telegram group |
| `GET` | `/clients/:id/checkins` | Get all check-in records with adherence |
| `PATCH` | `/clients/:id/checkins/today` | Override today's adherence status |

### Pending Queries
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/queries` | Get all pending queries for this nutritionist |
| `POST` | `/queries/:id/resolve` | Mark query resolved + optionally send reply to Telegram |

### AI Rules
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/rules` | Get master rules for this nutritionist |
| `GET` | `/clients/:id/rules` | Get client-specific rules |
| `POST` | `/rules` | Add master rule |
| `POST` | `/clients/:id/rules` | Add client-specific rule |
| `DELETE` | `/rules/:id` | Remove a rule |

### Admin Endpoints (protected by admin token)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/nutritionists` | Get all nutritionists across platform |
| `PATCH` | `/admin/nutritionists/:id/approve` | Approve pending nutritionist |
| `PATCH` | `/admin/nutritionists/:id/pause` | Pause nutritionist access |
| `PATCH` | `/admin/nutritionists/:id/reactivate` | Reactivate paused nutritionist |
| `GET` | `/admin/stats` | Platform-wide stats |

---

## 🔑 Environment Variables (`.env`)

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=@NutriCoachBot

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Gemini AI
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash

# JWT Auth
JWT_SECRET=your_super_secret_key
JWT_EXPIRY_HOURS=72

# Admin
ADMIN_EMAIL=jay@yourdomain.com
ADMIN_PASSWORD_HASH=bcrypt_hash_here

# App
APP_ENV=development
WEBHOOK_URL=https://your-domain.com/webhook
PORT=8000
```

---

## 📦 `requirements.txt`

```
python-telegram-bot==21.5
google-generativeai==0.7.2
supabase==2.5.0
fastapi==0.111.0
uvicorn==0.30.1
apscheduler==3.10.4
python-dotenv==1.0.1
bcrypt==4.1.3
python-jose==3.3.0
httpx==0.27.0
```

---

## 🚀 How to Run (Development)

```bash
# 1. Navigate to project folder
cd nutricoach-telegram

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy .env.example to .env and fill in keys
copy .env.example .env

# 5. Run the bot
python bot/main.py
```

---

## 🏗️ Build Order — Phase by Phase

### ✅ Phase 1: Foundation (Start Here)
- [ ] Set up Supabase project, create all tables
- [ ] Set up `.env` with all keys
- [ ] `db/client.py` — Supabase connection
- [ ] `db/clients.py` — client CRUD
- [ ] `db/checkins.py` — checkin CRUD
- [ ] `db/messages.py` — message CRUD
- [ ] `ai/gemini.py` — Gemini connection + prompt builder
- [ ] `ai/classifier.py` — basic adherence classification
- [ ] `ai/router.py` — handle vs escalate logic
- [ ] `bot/handlers/message_handler.py` — receive + route messages
- [ ] `bot/handlers/command_handler.py` — /start /diet /progress /help
- [ ] `bot/main.py` — start the bot
- [ ] **Test:** Manual test with one real Telegram group

### 📋 Phase 2: Scheduling & Groups
- [ ] `bot/scheduler.py` — daily check-in at right time per client
- [ ] `bot/group_manager.py` — create group when client added
- [ ] `db/ai_rules.py` — rules CRUD
- [ ] Weekly summary auto-generation
- [ ] **Test:** Full end-to-end with one test client

### 🌐 Phase 3: Web App API
- [ ] `api/webhook.py` — FastAPI server
- [ ] All auth endpoints
- [ ] All client endpoints
- [ ] All query endpoints
- [ ] All AI rules endpoints
- [ ] Admin endpoints
- [ ] **Test:** Postman/curl all endpoints

### 🖥️ Phase 4: Web App Frontend (Next.js)
- [ ] Nutritionist login / signup screens
- [ ] Dashboard with client cards
- [ ] Client profile + manual override
- [ ] Chat view (reads from DB, sends via API)
- [ ] Pending queries inbox
- [ ] AI rules editor
- [ ] Admin panel
- [ ] Analytics charts

### 🚢 Phase 5: Deployment
- [ ] Deploy Python bot to Railway
- [ ] Deploy Next.js web app to Vercel
- [ ] Configure Telegram webhook (production mode)
- [ ] Set up Supabase production project

---

*Document created: July 2026*
*Status: ✅ Technical Spec Complete — Ready for Phase 1 Build*
