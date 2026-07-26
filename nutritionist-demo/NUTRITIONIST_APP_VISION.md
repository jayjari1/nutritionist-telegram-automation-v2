# 🥗 Nutritionist App — Complete Feature & Vision Document

> **Purpose**: This document describes every feature, every screen, and every workflow of the Nutritionist App — from the moment a new client joins to the moment the nutritionist reviews their weekly progress. No technical jargon. Just the full picture.

---

## 👥 Who Uses This App?

There are **3 types of users**:

| User | Who They Are | What They Do |
|---|---|---|
| **Nutritionist (Admin / Coach)** | The clinical expert & coach | Manages clients, reviews adherence, resolves AI escalations, adjusts diet plans |
| **Client** | The person on the diet plan | Receives automated daily check-ins, chats naturally, asks dietary questions |
| **Caretaker** | Family member / partner | Monitors client's progress, logs observations (e.g., mood, dinner intake) |

---

## 🗺️ Big Picture — How Everything Connects

```
Nutritionist creates client profile & sets custom AI Instructions (Tone, Rules, Language)
          ↓
Client & Caretaker receive onboarding invite via WhatsApp / Telegram
          ↓
AI sends scheduled daily check-in questions (e.g., 7:00 PM)
          ↓
Client replies in natural language (English, Hindi, or Hinglish)
          ↓
AI evaluates confidence & adherence in background:
 ├─► Routine Check-in / High Confidence: AI replies warmly & classifies adherence (✅ On Track / ⚠️ Partial / ❌ Off Track)
 └─► Dietary Modification / Pain Reported: AI sends interim reply & ESCALATES query to Dr. Priya (❓ Pending Query)
          ↓
Nutritionist Dashboard updates in real-time:
 ├─► Scans client adherence cards & priority flags
 ├─► Resolves AI Escalations with 1-click (Approve & Reply / Let AI Handle)
 └─► Messages client in full-screen WhatsApp/Instagram style chat view
          ↓
Weekly auto-generated progress reports & trend charts (Adherence, Consistency, Mood)
```

---

## 📱 Core App Sections & Workflows

### 1. 🏠 Home / Dashboard (Nutritionist View)
This is the mission control center where the nutritionist scans all clients at a glance.

**Key Dashboard Indicators:**
- **Client Summary Cards:** Displays avatar, name, program type, days remaining, and active status.
- **Real-time Adherence Status:** Automatically computed by AI after each daily check-in:
  - ✅ **On Track:** Followed all planned meals and activities.
  - ⚠️ **Partial:** Completed some meals/habits, skipped others (e.g., "Had breakfast and dinner, skipped lunch").
  - ❌ **Off Track:** Significantly missed planned nutrition or routines.
  - ❓ **No Response:** Client hasn't replied to the check-in yet.
  - *(Note: The nutritionist can manually override this status from the client profile at any time).*
- **Priority Flags & Alert Badges:** Highlights clients who missed check-ins for 2+ days, reported physical symptoms (dizziness, pain), or have subscription expiries approaching.

---

### 2. 🚀 Client Onboarding & 1-Click Access Workflow (Frictionless Access)
To maximize client engagement and eliminate drop-offs, the app utilizes a **zero-friction onboarding model** without requiring App Store downloads, passwords, or complex sign-ups:

#### Step 1: Nutritionist Submits "Add Client" Form
Inside the Admin Dashboard (`➕ Add Client`), the nutritionist inputs basic details:
- Client's Full Name & WhatsApp/Telegram contact number.
- Caretaker details (optional).
- Program Duration (e.g., 60 days) & Check-in Schedule (e.g., 7:00 PM daily).
- Diet Plan text & Custom AI Guidance (Tone, Language, Medical rules).

#### Step 2: Automated Instant WhatsApp / Telegram Invitation
Upon saving, the system automatically generates a **Unique Secure Magic Link** and sends a personalized welcome message to the client via WhatsApp or Telegram:
> 🌿 **Welcome to your Personal Nutrition Program, Ananya!**
> Dr. Priya Mehta has created your customized 60-day Weight Management plan. Meet **NutriCoach AI**, your daily companion who will check in with you every evening and keep Dr. Priya updated!
> 👉 **Click below to access your personal dashboard instantly (No download or password required):**
> 🔗 `https://app.nutricoach.in/client/access?token=ananya_secure_token_8849`

#### Step 3: 1-Click Magic Link Access & PWA "Add to Home Screen"
When the client clicks the invitation link on their mobile device:
- **Instant Auto-Login:** The token securely authenticates them into their personal Home Screen (`#screen-c-home`).
- **Progressive Web App (PWA) Install:** A prompt offers to **`📲 Add NutriCoach to Home Screen`**. With one tap, an app icon is added to their phone.
- **Native App Experience:** Launching from the home screen opens the app fullscreen without browser address bars, feeling identical to a native iOS or Android application.

#### Step 4: Caretaker Multi-User Access
If a caretaker (husband, parent, cook) was added, they receive a separate secure link granting them caretaker privileges to view the diet chart and log meal observations in purple bubbles (`💜 Caretaker`).

#### Step 5: Daily Automated Engagement
At the scheduled time, the AI sends check-in prompts via WhatsApp/Telegram or push notification. Clients can reply directly in their chat app or open the full-screen web app view—both sync seamlessly in real-time.

---

### 3. 🤖 AI Confidence Routing & Escalation (The "Pending Queries" System)
To ensure patient safety and clinical integrity, the AI does not blindly answer every medical or dietary substitution question. It acts as an intelligent first line of defense with **Confidence Routing**:

#### How It Works:
1. **Routine Questions (High Confidence):** If a client asks simple adherence or general motivation questions (e.g., *"How much water should I drink after workout?"*), the AI responds instantly.
2. **Clinical / Dietary Substitutions (Low Confidence / Rule Override):** If a client asks to change macros or reports physical discomfort (e.g., *"Can I take 1 scoop whey protein after dinner instead of evening walk? Knees hurting today."*), the AI recognizes that this alters calorie/protein expenditure and requires clinical judgment.
3. **Automated Escalation Workflow:**
   - **To Client:** AI sends a supportive interim reply: *"I understand your knees are hurting! However, replacing an evening walk with whey protein changes your specific plan rules. I have escalated this question to Dr. Priya for review. She will reply here shortly! 👩‍⚕️"*
   - **To Nutritionist:** Creates an urgent **"❓ AI Escalation (Pending Query)"** alert at the very top of the **Alerts & Flags** screen and pins an **AI Escalation Banner** inside the doctor's chat.

---

### 4. 💬 Full-Screen Messaging (WhatsApp / Instagram Style)
To provide a distraction-free, modern messaging experience, both the Client Check-in and Nutritionist Messaging screens use a dedicated **Full-Screen Layout**:

#### Layout Architecture:
- **No Bottom Navigation Interference:** When inside a chat screen, the app's bottom navigation bar completely disappears, maximizing vertical screen real estate just like WhatsApp or Instagram DMs.
- **Top Header Bar:** Displays back arrow (`←`), client avatar, client name, program badge, and active status (`● Online / Active Plan`).
- **Independent Scrollable Message Area:** Only the chat history scrolls; the header and input bar remain fixed in place.
- **Pinned Bottom Input Bar:** Features an auto-resizing text area (grows up to 3 lines as you type), file attachment placeholder, and a filled send arrow button.

#### The Doctor's Escalation Banner (Inside `#screen-n-chat`):
When the doctor opens a chat with a pending query, a yellow/orange pinned banner appears above the messages:
- **Displays the Exact Client Question:** e.g., *"Can I take 1 scoop whey protein after dinner instead of evening walk? Knees hurting today."*
- **Displays AI Clinical Rationale:** e.g., *"🤖 AI Note: Outside standard plan rules (calorie/macro substitution & pain reported). Clinical approval required."*
- **1-Click Resolution Action Buttons:**
  - **`✅ Approve & Reply`**: Pre-fills the doctor's text box with a drafted clinical approval message (*"Yes Ananya, you can take 1 scoop whey protein after dinner instead of your walk today since your knees are hurting..."*). Doctor can edit and hit Send.
  - **`🤖 Let AI Handle`**: Triggers a polite AI rule enforcement reply (*"Dr. Priya reviewed your note: Please try a gentle 15-min indoor walk or skip today without adding whey protein to keep calories on track."*) and marks the query resolved.

---

### 5. 🧠 Multiple Personalized AI Instructions (Per Client)
Every client has unique personality traits, medical conditions, and communication preferences. The nutritionist can configure **multiple categorized instructions** in the client's profile (`Plan & AI Guidance` tab):

- **Multi-Note Support:** Instead of a single text box, the nutritionist can add, edit, or remove multiple distinct guidance cards.
- **Categorized Controls:**
  - 🗣️ **Tone & Style:** e.g., *"Client gets anxious easily — always be extra gentle and encouraging. Celebrate small wins."*
  - 🌐 **Language Preference:** e.g., *"Reply in conversational Hinglish (Latin script). Keep vocabulary simple."*
  - 🚫 **Medical & Dietary Constraints:** e.g., *"Type 2 Diabetic — strictly warn against any hidden sugars or fruit juice substitutions."*
  - 👨‍👩‍👧 **Caretaker Engagement:** e.g., *"Her father Ramesh logs dinner observations — always acknowledge and thank the caretaker."*
- **Instant Effect:** Any modification to these instructions is immediately applied to the AI's system prompt for the next check-in cycle.

---

### 6. 🚨 Alerts & Flags Management
The **Alerts & Flags screen** serves as the nutritionist's prioritized clinical inbox:
1. **Urgent AI Escalations:** Client dietary questions requiring doctor judgment (Pending Queries).
2. **No Response Flags:** Clients who missed daily check-ins for 2+ consecutive days.
3. **Consistency Drops:** Noticeable weekly declines in adherence (e.g., dropping from 85% to 60%).
4. **Subscription Expiry Notices:** Alerts for plans ending in 7 days or 3 days, with 1-click renewal flows.

---

### 7. 📊 Analytics, Charts & Progress Tracking
The app tracks both daily micro-metrics and weekly macro-trends without overwhelming the UI:
- **Consistency Rate:** Percentage of scheduled check-ins completed.
- **Adherence Trend Chart:** Visual line graph tracking ✅ On Track vs ⚠️ Partial days over a 7-week cycle.
- **Energy Level Bar Chart:** Tracked in the background from client check-in text (1 to 5 scale) and displayed on the weekly progress tab (removed from the daily summary card for simplicity).
- **Auto-Generated Weekly Digest:** Every Sunday evening, AI compiles a comprehensive summary of wins, adherence percentage, and recommendations for the nutritionist to review or export as PDF/CSV.

---

### 8. 🗓️ Subscription & Timeline Management

| Badge | Meaning | Nutritionist Action |
|---|---|---|
| ✅ **Active** | Program running normally | Continue routine monitoring |
| ⚠️ **Expiring Soon** | Plan ends within 3–7 days | Trigger 1-click WhatsApp renewal reminder |
| 🔴 **Expired** | Program period completed | Read-only archive mode; can be reactivated anytime |
| 🔄 **Renewed** | Program extended | New end date set; all historical data preserved |

---

### 9. 📁 Past Clients & Data Archive
- **Zero Data Loss:** When a client's plan expires, they move to the "Past Clients" archive.
- **Full History Access:** Nutritionists can review past chat timelines, diet charts, symptom logs, and adherence graphs at any time.
- **1-Click Reactivation:** If a client returns after months, tapping "Reactivate" restores their profile with all previous context intact.

---

## 👑 Multi-Tenant B2B SaaS Architecture & Zero-Money Status Management

To scale NutriCoach from a single clinic tool into an enterprise-grade SaaS platform licensing software to multiple independent nutritionists, the architecture incorporates three distinct tiers of control without price-tag clutter:

```
┌─────────────────────────────────────────────────────────────┐
│                 👑 PLATFORM SUPER-ADMIN                     │
│         (SaaS Creator / Platform Owner Command Center)        │
│  • Manages all doctor accounts across the platform          │
│  • Approves "Pending Verification" registrations            │
│  • Monitors platform status (Active / Paused / Expired)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
             ┌─────────────────┴─────────────────┐
             ▼                                   ▼
┌──────────────────────────┐       ┌──────────────────────────┐
│   🩺 NUTRITIONIST 1       │       │   🩺 NUTRITIONIST 2       │
│   (Dr. Priya Mehta)      │       │   (Dr. Rahul Sharma)     │
│  • Independent clinic    │       │  • Sports nutrition      │
│  • Manages 4 clients     │       │  • Manages 18 clients    │
└────────────┬─────────────┘       └────────────┬─────────────┘
             │                                   │
             ▼                                   ▼
┌──────────────────────────┐       ┌──────────────────────────┐
│ 👩 CLIENTS & CARETAKERS  │       │ 👩 CLIENTS & CARETAKERS  │
│  • Daily AI check-ins    │       │  • Athlete meal logging  │
│  • Fullscreen chat UI    │       │  • Performance tracking  │
└──────────────────────────┘       └──────────────────────────┘
```

### 1. 🚫 Zero-Money / Pure Status-Based SaaS Model
To maintain maximum operational flexibility and privacy, the platform eliminates hardcoded pricing tiers, payment gateways, and invoice clutter:
- **Status Overview:** The Super-Admin dashboard tracks pure operational metrics: **Active Doctors**, **Pending Approvals**, and **Paused / Expired Accounts**.
- **Deadline Tracking:** Each doctor account is tied to an explicit access deadline (e.g., *Aug 31, 2026 - 55 days left*).
- **Manual Override Controls:** The Super-Admin has instant 1-click override switches (`⏸️ Pause Access` / `▶️ Reactivate Access`). Pausing a doctor immediately suspends automated AI check-ins and client onboarding across their clinic, displaying a persistent read-only warning banner on their dashboard.

### 2. ⏳ The "Pending Verification" Approval Workflow
Because NutriCoach is a private, clinical-grade platform, unverified registrations cannot be granted instant access to AI tools:
1. **Doctor Sign-Up Submission:** When a new nutritionist submits their credentials on the Sign Up tab (`#screen-n-login`), their account enters **`⏳ Pending Verification`** mode.
2. **Admin Verification Queue:** Inside the Super-Admin dashboard (`#screen-admin`), the registration appears in a dedicated **"⏳ Pending Verifications (Requires Action)"** inbox, displaying clinic brand name, specialty, work email, and requested client volume.
3. **1-Click Account Activation:** Only when the Super-Admin clicks **`✅ Verify & Activate Account`** is the doctor's status upgraded to `✅ Verified & Active`, unlocking their dashboard and granting full access to client onboarding and AI automation.

---

## 🔐 Secure Authentication & Universal Forgot Password Flow

To ensure data security for both doctors and patients, the platform features dedicated authentication portals and an interactive OTP password recovery system:

### 1. Dedicated Role Portals
- **🩺 Nutritionist Portal (`#screen-n-login`):** Dual-tab authentication allowing doctors to Sign In or register a New Account. Includes subscription awareness checks upon login.
- **👩 Client Portal (`#screen-c-login`):** Distraction-free mobile login screen where clients enter their registered phone number/WhatsApp and access PIN.
- **⚡ Instant Demo Access:** Both portals feature 1-click quick login buttons (*Dr. Priya Mehta* and *Ananya Sharma*) for instant investor or client presentations.

### 2. Universal OTP Password Recovery (`#forgot-password-modal`)
When any user clicks **`Forgot Password?`**, the app triggers a standardized 2-step OTP recovery workflow:
- **Step 1 (Request Verification Code):** User selects their account type (*🩺 Nutritionist / Doctor* or *👩 Client / Patient*) and inputs their registered email address or WhatsApp mobile number. Clicking **`📨 Send 6-Digit Reset Code`** initiates verification.
- **Step 2 (OTP & PIN Reset):** A dynamic confirmation badge displays where the code was sent. The user enters their 6-digit OTP across interactive verification boxes, sets a new password/PIN, and taps **`🔒 Reset & Sign In`**. The system validates the credentials and redirects them to their respective dashboard.

---

## 💻 Frontend SPA Architecture & Complete DOM Reference (Zero Conflict Guarantee)

To ensure **100% architectural alignment** between design, prototyping, and final development, this section serves as the definitive reference for the Single Page Application (SPA) structure. There is zero ambiguity: every screen, modal, and button in our interactive demo (`index.html`) maps precisely to the DOM IDs and state handlers listed below.

### 1. 👤 Client Profile & Manual Adherence Override (`#screen-n-profile`)
While the AI automatically evaluates and classifies daily check-ins, clinical judgment always supersedes AI automation. The Client Profile screen features a dedicated **Manual Adherence Override Section**:
- **5 One-Click Clinical Override Buttons:** Located immediately below the client header bar, allowing the nutritionist to override the AI status instantly:
  - **`✅ On Track`**: Marks the client as fully compliant for the day.
  - **`⚠️ Partial`**: Notes partial adherence (e.g., followed meals but skipped evening workout).
  - **`❌ Off Track`**: Flags significant deviation from the diet chart.
  - **`❓ No Response`**: Manually resets status if check-in was missed.
  - **`⏸️ Pause Plan`**: Temporarily pauses automated check-ins (e.g., during client travel or illness).
- **Instant UI Synchronization:** Tapping any override button immediately updates the status badge on the profile header and reflects across the main Nutritionist Dashboard (`#screen-n-dashboard`).

### 2. 🌗 Theme Management & Dark Mode Support (`#screen-n-settings`)
The platform incorporates native CSS token-based theming to support diverse clinical and patient environments:
- **Light & Dark Mode Toggle:** Available inside **Settings (`#screen-n-settings`)**, allowing users to switch between a crisp, high-contrast Light Theme and a sleek, eye-saving Dark Theme (emerald & charcoal palette).
- **CSS Custom Properties (Design Tokens):** The UI avoids hardcoded colors, utilizing global tokens (`--bg-primary`, `--bg-card`, `--text-primary`, `--accent-green`, `--border-color`) to ensure all components, chat bubbles, and modals adapt seamlessly without visual flicker.

### 3. Complete SPA Screen & Modal ID Reference Table
Developers building the backend APIs and frontend routing must adhere strictly to this 1-to-1 DOM mapping:

| Screen / Modal Name | HTML DOM ID | Primary Purpose & Key Features | Associated JS Handlers / State |
|---|---|---|---|
| **Role Selector** | `#screen-role` | Entry portal allowing users to select their persona (Nutritionist Portal, Super-Admin, Client App Demo). | `goTo('screen-role')` |
| **Nutritionist Login / Sign Up** | `#screen-n-login` | Dual-tab authentication for clinic staff. Includes Sign In, New Account registration, Quick Demo access, and Forgot Password link. | `switchAuthTab('signin'/'signup')`<br>`doNutritionistLogin()`<br>`submitDoctorSignup()` |
| **Client Login Portal** | `#screen-c-login` | Distraction-free mobile login screen for patients using registered phone/WhatsApp and access PIN. | `doClientLogin()`<br>`goTo('screen-c-login')` |
| **Super-Admin Dashboard** | `#screen-admin` | Platform Owner command center. Tracks active/paused doctors, manages access deadlines, and verifies pending registrations. | `toggleDoctorStatus(docId)`<br>`approveDoctorPending()` |
| **Nutritionist Dashboard** | `#screen-n-dashboard` | Clinical mission control. Displays real-time client adherence cards, priority flags, filter tabs, and subscription warnings. | `filterClients(status)`<br>`drPriyaStatus` check |
| **Client Profile / Details** | `#screen-n-profile` | Deep-dive clinical view. Features Manual Adherence Overrides, Diet Chart editor, Master LLM prompt, and Custom AI Rules list. | `openClient(id)`<br>`setClientStatus(status)` |
| **Nutritionist Messaging** | `#screen-n-chat` | Full-screen WhatsApp-style chat interface. Includes AI Escalation Resolution Banner with 1-click action buttons. | `openDoctorChat(name)`<br>`resolveEscalation(action)` |
| **Add New Client Form** | `#screen-n-add` | Frictionless onboarding form. Captures contact details, diet chart, check-in time, and generates magic access link. | `saveNewClient()`<br>`goTo('screen-n-add')` |
| **Nutritionist Settings** | `#screen-n-settings` | Clinic profile and subscription management card (shows access tier, remaining days, renewal links, and theme toggle). | `goTo('screen-n-settings')` |
| **Client Home / Check-in** | `#screen-c-home`<br>`#screen-c-checkin` | Patient PWA experience. Displays automated daily check-in prompts, natural language chat, and PWA install instructions. | `sendClientMessage()`<br>`goTo('screen-c-home')` |
| **AI Prompt Config Modal** | `#ai-prompt-modal` | Floating overlay to edit Master System Persona and manage categorized AI behavior rules for individual clients. | `openAIPromptModal()`<br>`closeAIPromptModal()` |
| **Forgot Password Modal** | `#forgot-password-modal` | Universal 2-step OTP password recovery overlay for both doctor and client accounts with interactive verification inputs. | `openForgotPasswordModal(role)`<br>`sendResetCode()`<br>`confirmPasswordReset()` |

---

## 📝 Meeting Notes & Future Extensions (Reserved Space)
> [!IMPORTANT]
> **This section is explicitly reserved for your upcoming meeting with your nutritionist / partner!**
> As you discuss the demo and workflows, use the placeholders below to document new feature requests, specific clinical rules, or UI adjustments.

### 🔹 1. Clinical Meeting Notes (To Be Added After Meeting)
*Use this space to record feedback, new requirements, or custom workflows discussed during your presentation:*
- **Note 1:** `[e.g., Specific blood report tracking fields required...]`
- **Note 2:** `[e.g., Custom notification sound for urgent AI escalations...]`
- **Note 3:** `[e.g., Special breakfast/lunch/dinner checkbox layout...]`
- **Note 4:** `[e.g., Integration with external fitness bands / Apple Health...]`

### 🔹 2. Diet Chart Attachments & File Sharing (Planned Phase 2)
- **PDF Diet Plan Viewer:** Allow nutritionist to attach official clinical PDF/image diet charts directly inside the client profile.
- **Quick Download / Share:** Client can view or download their diet chart directly from the top bar of their chat interface.

### 🔹 3. Advanced Communication & Calling Features (Planned Phase 2)
- **In-App Voice Notes:** Allow clients to reply to daily check-ins using voice recordings; AI transcribes and classifies adherence automatically.
- **Emergency / Direct Call Button:** Option for nutritionist to initiate a direct WhatsApp/phone call from the client's header bar for urgent clinical interventions.

### 🔹 4. Custom Recipe & Meal Substitution Library (Planned Phase 2)
- **Approved Snack Database:** A searchable library of pre-approved healthy snacks and Indian meal substitutes that the AI can automatically recommend without escalating to the doctor.

---

## ✅ Summary — Complete System Alignment

```
SUPER-ADMIN COMMAND VIEW     NUTRITIONIST CLINICAL VIEW     CLIENT & CARETAKER VIEW
────────────────────────     ──────────────────────────     ───────────────────────
Platform status & deadlines  Dashboard (Clients overview)   Daily automated check-in
Pending doctor verifications Full-Screen WhatsApp Chat      Distraction-free chat UI
1-Click active/pause toggle  AI Escalation Banner / alerts  Caretaker observations
Universal OTP recovery       AI Guidance prompts & rules    Weekly progress charts
Zero pricing/money clutter   Subscription deadline tracking Zero technical complexity
```
