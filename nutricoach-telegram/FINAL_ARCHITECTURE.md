# 🏗️ NutriCoach — Final System Architecture
### Hybrid: Telegram Group (Client) + Web App (Nutritionist + Admin)

> **This is the definitive architecture document.**
> Every feature from NUTRITIONIST_APP_VISION.md is mapped here — showing exactly where it lives
> (Telegram or Web App) and exactly how the full flow works end-to-end.

---

## 🧩 The Big Picture — Two Surfaces, One Backend

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ONE SHARED BACKEND                           │
│              (Python + Supabase Database + Gemini AI)               │
│                                                                     │
│  Stores: clients, check-ins, adherence, queries, chat history,      │
│          AI rules, nutritionist accounts, admin settings            │
└────────────────────┬────────────────────────────┬───────────────────┘
                     │                            │
          ┌──────────▼──────────┐      ┌──────────▼──────────┐
          │   TELEGRAM GROUP    │      │      WEB APP         │
          │  (Client Surface)   │      │ (Nutritionist +      │
          │                     │      │  Admin Surface)      │
          │ • Client chats here │      │                      │
          │ • Caretaker here    │      │ • Dashboard          │
          │ • Nutritionist here │      │ • Client profiles    │
          │ • Bot sends here    │      │ • AI configuration   │
          │ • AI replies here   │      │ • Analytics          │
          └─────────────────────┘      │ • Admin panel        │
                                       │ • Sign in / Sign up  │
                                       └─────────────────────┘
```

**Key principle:** Client never uses the web app. Nutritionist uses web app primarily, can also use Telegram group secondarily. Admin (you) uses web app only.

---

## 👥 Who Is Where

| Person | Primary Interface | What They See / Do |
|---|---|---|
| **Client** | Telegram Group | Daily check-ins, AI replies, diet chart sent as file, weekly progress |
| **Caretaker** | Telegram Group | Same as client — logs observations, sees all messages |
| **Nutritionist** | Web App (primary) + Telegram Group (secondary) | Full dashboard, client management, AI config, can also reply from Telegram |
| **Admin (You)** | Web App only | Super admin panel, approve/pause nutritionists, platform stats |

---

## 🗂️ How Every Feature Maps to the System

### Feature 1: 🏠 Nutritionist Dashboard
**Lives in: Web App**

The nutritionist logs into the web app and sees:
- All client cards showing: name, program type, days remaining, today's adherence status (✅ / ⚠️ / ❌ / ❓)
- Priority alert badges on cards (missed check-ins, pain reported, expiry soon)
- Filter tabs: All / At Risk / Active / Completed
- Subscription warning banner if their own account is expiring

**How data gets there:**
Every time a client sends a message in Telegram → bot processes it → AI classifies adherence → stores result in database → web app reads it and shows on dashboard in real time.

---

### Feature 2: 🚀 Client Onboarding (Adding a New Client)
**Lives in: Web App (form) → Telegram (delivery)**

**Step-by-step:**
1. Nutritionist opens web app → clicks `➕ Add Client`
2. Fills form: client name, Telegram phone number, program duration, check-in time, diet plan, caretaker details
3. Nutritionist saves → backend does the following automatically:
   - Creates a **new Telegram Group**
   - Adds the bot to that group
   - Invites the **client** via Telegram invite link (sent to their phone number)
   - Invites the **caretaker** via a separate invite link (if provided)
   - Adds the **nutritionist's Telegram account** to the group (so they can see and reply too)
   - Sends the **welcome message** in the group with the diet chart attached as a file
4. Client opens Telegram → sees the group → taps the invite link → they're in

> ⚠️ Note: The nutritionist must link their personal Telegram account once (during signup) so they can be added to each client group.

**What client sees in Telegram group:**
```
🌿 Welcome Ananya!

Dr. Priya Mehta has set up your 60-day Weight Management program.

I'm NutriCoach AI — your daily check-in companion!
I'll message you every evening at 7:00 PM.

📋 Your diet plan is attached below.
Any questions? Just ask here anytime!
```
*(Bot immediately sends the diet chart PDF as a Telegram file attachment)*

---

### Feature 3: 👥 Caretaker Multi-User Access
**Lives in: Telegram Group**

- Caretaker is added to the same Telegram group as the client
- They see all messages — AI replies, check-ins, doctor messages
- They can type observations directly in the group (e.g., *"She had a light dinner, seemed tired"*)
- Bot recognises caretaker messages and labels them differently in the database (stored as `role: caretaker`)
- On the web app, nutritionist sees caretaker messages marked with 💜 in the chat history

---

### Feature 4: 🤖 Daily Check-in (Automated)
**Lives in: Telegram Group (bot sends it)**

At the scheduled time (e.g., 7:00 PM):
- Bot sends the check-in message to the client's Telegram group
- Client replies naturally in the group
- Bot reads the reply and sends it to AI for processing
- AI classifies adherence and sends a warm reply back in the same group
- All of this is visible to the nutritionist and caretaker who are also in the group

**Telegram group looks like:**
```
[7:00 PM - Bot]
🌙 Good evening Ananya! How was your diet today?
Tell me everything — what did you eat?

[7:22 PM - Ananya]
Had breakfast and lunch properly, skipped dinner
because headache tha

[7:22 PM - Bot/AI]
✅ Good effort today Ananya! Breakfast and lunch
on track. Rest well — drink water before sleeping.
Dr. Priya will see your update! 🌟
```

---

### Feature 5: 🤖 AI Confidence Routing & Pending Queries
**Lives in: Telegram (AI reply) + Web App (alert to nutritionist)**

When client asks something that needs doctor attention:

**In Telegram group:**
```
[Ananya]
Can I replace my evening walk with whey protein?
Knees are hurting today

[Bot/AI - immediately]
I understand your knees are hurting! 🙏
This change affects your specific plan rules.
I've informed Dr. Priya — she will reply shortly! 👩‍⚕️
```

**Simultaneously, on nutritionist's web app:**
- A red alert badge appears on the client's card
- An `⚠️ Pending Query` notification appears at top of Alerts screen
- Inside the client's chat view on web app: a yellow banner shows the exact question and AI's assessment

**Nutritionist resolves it from web app:**
- Clicks `✅ Approve & Reply` → web app pre-fills a response → nutritionist edits → hits Send
- Message goes to the Telegram group instantly, appearing as a message from the nutritionist

**OR** Nutritionist can just type their reply directly in the Telegram group — both methods work. Web app marks the query as resolved automatically when it detects a doctor message in the group.

---

### Feature 6: 💬 Full-Screen Chat (Nutritionist's Web App View)
**Lives in: Web App**

The nutritionist's web app shows the full chat history of each client's Telegram group — identical to the Telegram conversation but inside the web app dashboard:
- All client messages, AI replies, caretaker observations, doctor replies — all visible
- Full-screen layout, no navigation bar during chat
- Nutritionist can type and send from web app → message appears in Telegram group
- AI Escalation Banner pinned at top when there's a pending query
- `✅ Approve & Reply` and `🤖 Let AI Handle` buttons on the banner

---

### Feature 7: 🧠 AI Instructions Per Client
**Lives in: Web App (configuration)**

Inside each client's profile on the web app, the nutritionist sets:
- **Master System Prompt** — base personality of the AI (applies to all this nutritionist's clients)
- **Per-Client Rules** — individual instructions:
  - 🗣️ Tone: *"Always be gentle, she gets anxious easily"*
  - 🌐 Language: *"Hinglish preferred"*
  - 🚫 Medical: *"Type 2 Diabetic — no fruit juices"*
  - 👨‍👩‍👧 Caretaker: *"Her father Ramesh logs dinner — thank him"*
- Rules take effect immediately on next message

**How it flows to Telegram:** Every time a client sends a message in Telegram → bot reads it → **injects all their rules into the AI prompt** → AI responds accordingly.

---

### Feature 8: 👤 Client Profile & Manual Override
**Lives in: Web App**

The nutritionist opens a client's profile on web app and sees:
- Client info, program type, days remaining, today's status
- **5 override buttons:** `✅ On Track` / `⚠️ Partial` / `❌ Off Track` / `❓ No Response` / `⏸️ Pause Plan`
- Tapping any button overrides the AI's classification and updates the dashboard immediately
- `⏸️ Pause Plan` stops the daily check-in bot from messaging the client in Telegram until unpaused

---

### Feature 9: 🚨 Alerts & Flags (Nutritionist's Inbox)
**Lives in: Web App**

A dedicated Alerts screen on the web app shows:
1. **Pending Queries** — client questions AI escalated, need doctor's reply
2. **No Response Flags** — client hasn't replied to check-in for 2+ days
3. **Consistency Drops** — adherence falling week over week
4. **Subscription Expiry** — client's program ending in 3–7 days (remind to renew)

All of these are computed by the backend and surfaced as alerts on the web app. The nutritionist does not need to monitor Telegram for these — the web app acts as the clinical priority inbox.

---

### Feature 10: 📊 Analytics & Progress Tracking
**Lives in: Web App**

Inside each client's profile:
- Adherence trend chart (7-week line graph — On Track vs Partial days)
- Consistency rate percentage
- Energy level bar chart (extracted from check-in messages by AI)

Every Sunday:
- Backend auto-generates weekly summary
- **Sends it to the Telegram group** (client sees their own progress)
- Also shows on web app under the client's Analytics tab

---

### Feature 11: 🗓️ Client Subscription & Timeline
**Lives in: Web App (management) + Telegram (expiry alerts)**

| Status | Web App Shows | Telegram Action |
|---|---|---|
| ✅ Active | Green badge, days remaining | Nothing — normal daily check-ins |
| ⚠️ Expiring Soon | Yellow badge, 1-click reminder button | Bot sends gentle reminder in group |
| 🔴 Expired | Red badge, plan paused | Bot stops sending daily check-ins |
| 🔄 Renewed | Green badge, new end date | Bot resumes sending check-ins |

---

### Feature 12: 📁 Past Clients & Archive
**Lives in: Web App**

- When client plan expires → moved to Past Clients tab on web app
- Full chat history, all check-ins, adherence graphs — all preserved
- Nutritionist can review everything
- `1-Click Reactivate` → restores the client, bot resumes check-ins in the Telegram group

---

### Feature 13: 👑 Multi-Tenant SaaS — Multiple Nutritionists
**Lives in: Web App (Admin Panel)**

You (the admin) log into the admin section of the web app:
- See all nutritionists: status, deadline, client count
- Pending verification requests queue
- 1-click Verify → nutritionist gets full access
- 1-click Pause → nutritionist's dashboard shows warning, bot stops for ALL their clients
- 1-click Reactivate → everything resumes
- Expiry notifications sent automatically

---

### Feature 14: 🔐 Authentication
**Lives in: Web App**

**Nutritionist:**
- Sign up → enters pending verification
- You approve from admin panel → they get access
- Sign in with email + password
- Forgot password → OTP sent to email → 6-digit code → reset password

**Client:**
- Client does NOT log into the web app at all
- Client only uses Telegram (no passwords, no login)

**Admin (You):**
- Separate admin login section on web app
- Protected by a secret admin password only you know

---

### Feature 15: 🌗 Dark Mode & Themes
**Lives in: Web App**

- Nutritionist can toggle between Light and Dark mode in Settings
- Uses CSS design tokens — entire dashboard switches cleanly
- No impact on Telegram (Telegram has its own dark mode setting)

---

### Feature 16: 📋 Diet Chart Sharing
**Lives in: Telegram (delivery) + Web App (upload/edit)**

- Nutritionist uploads or writes diet chart on web app (inside client profile)
- When client is first added → bot sends the diet chart as a PDF/image file attachment to the Telegram group
- Client can scroll up in the group anytime to find it
- If nutritionist updates the diet chart on web app → bot sends updated version to group automatically

---

## 🔄 Complete End-to-End Flow — One Example

```
1. You (Admin) approve Dr. Priya's account on the web app

2. Dr. Priya logs into the web app, goes to Add Client

3. She fills in: Ananya Sharma, Telegram: +91 98765 43210, 
   60-day Weight Management, 7pm daily, uploads diet chart

4. She saves — backend:
   → Creates a Telegram group "Ananya × NutriCoach"
   → Adds the bot + Dr. Priya's Telegram + Ananya's Telegram
   → Bot sends welcome message + diet chart PDF in group

5. Ananya opens Telegram → sees group invite → joins → sees welcome

6. Every day at 7pm → bot sends check-in question in group

7. Ananya replies in Telegram group → AI processes → replies warmly
   → Dr. Priya can see the conversation in her web app too

8. One day Ananya asks about changing her workout
   → AI escalates → sends interim reply in group
   → Web app shows Pending Query alert to Dr. Priya
   → Dr. Priya opens web app → sees escalation banner
   → Clicks Approve & Reply → edits → sends
   → Message appears in Telegram group from Dr. Priya

9. Every Sunday → backend generates weekly summary
   → Sends summary in Telegram group
   → Also visible in web app analytics

10. After 60 days → program expires
    → Bot stops check-ins
    → Web app shows client as Expired
    → Dr. Priya can reactivate anytime
```

---

## 🛠️ Tech Stack (Final Decision)

| Layer | Technology | Purpose |
|---|---|---|
| **Telegram Bot** | Python + python-telegram-bot | Manages all Telegram groups, sends/receives messages |
| **AI** | Google Gemini API | Processes client messages, classifies adherence, decides escalation |
| **Database** | Supabase (PostgreSQL) | Stores everything — clients, messages, check-ins, rules, accounts |
| **Web App Frontend** | Next.js (React) | Nutritionist & Admin dashboard |
| **Web App Backend** | Next.js API Routes | Handles web app requests, talks to database |
| **Scheduling** | APScheduler (Python) | Sends daily check-ins at scheduled time per client |
| **Hosting — Bot** | Railway or Render | Runs Python bot 24/7 |
| **Hosting — Web App** | Vercel | Hosts Next.js web app |
| **Authentication** | Supabase Auth | Handles nutritionist login, OTP, password reset |

---

## 📁 Project Folder Structure

```
nutricoach-telegram/           ← New project (this folder)
  ├── bot/
  │   ├── main.py              ← Starts the bot
  │   ├── handlers.py          ← Handles all incoming Telegram messages
  │   ├── group_manager.py     ← Creates groups, adds members
  │   └── scheduler.py         ← Sends daily check-ins
  ├── ai/
  │   ├── gemini.py            ← Gemini API connection
  │   └── router.py            ← Decides: handle or escalate?
  ├── db/
  │   ├── models.py            ← Table definitions
  │   └── queries.py           ← All read/write functions
  ├── config.py                ← API keys, settings
  └── requirements.txt

nutricoach-webapp/             ← Web app (separate folder, built later)
  ├── pages/                   ← Next.js pages
  │   ├── index.js             ← Nutritionist dashboard
  │   ├── clients/[id].js      ← Client profile
  │   ├── admin/               ← Admin panel
  │   └── auth/                ← Login, signup, forgot password
  ├── components/              ← Reusable UI components
  ├── lib/                     ← Database helpers, API calls
  └── styles/                  ← CSS / design tokens
```

---

## 🚀 Build Order

### Phase 1 — Telegram Bot Core (Build First)
- [ ] Supabase database setup (all tables)
- [ ] Bot: receive messages, reply via AI
- [ ] AI router: handle vs escalate
- [ ] Daily scheduler: send check-ins at right time
- [ ] Group creation when new client is added

### Phase 2 — Web App (After Bot Works)
- [ ] Nutritionist login / signup / forgot password
- [ ] Dashboard with client cards and adherence
- [ ] Client profile with manual override
- [ ] AI rules configuration
- [ ] Chat view (reads from Telegram, can send to Telegram)
- [ ] Alerts & Pending Queries inbox

### Phase 3 — Admin & Scale
- [ ] Admin panel (approve/pause nutritionists)
- [ ] Multi-nutritionist support
- [ ] Analytics & charts
- [ ] Weekly auto-digest
- [ ] Subscription expiry tracking

---

*Document created: July 2026*
*Status: ✅ Architecture Finalized — Ready to Build Phase 1*
