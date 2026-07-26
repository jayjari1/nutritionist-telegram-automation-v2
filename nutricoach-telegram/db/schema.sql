-- =====================================================================
-- NutriCoach — Supabase Database Schema
-- =====================================================================
-- Run this entire file in the Supabase SQL Editor to create all tables.
-- Go to: https://supabase.com → Your Project → SQL Editor → New Query
-- Paste this → Click Run
-- =====================================================================

-- Enable UUID extension (Supabase has this by default, just in case)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ─────────────────────────────────────────────────────────────────────
-- Table 1: admins
-- The platform super-admin (you). Only one record needed.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admins (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       TEXT UNIQUE NOT NULL,
  password    TEXT NOT NULL,              -- bcrypt hashed password
  created_at  TIMESTAMPTZ DEFAULT now()
);


-- ─────────────────────────────────────────────────────────────────────
-- Table 2: nutritionists
-- Each nutritionist who signs up on the platform.
-- Must be approved by admin before they get access.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nutritionists (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name         TEXT NOT NULL,
  clinic_name       TEXT,
  email             TEXT UNIQUE NOT NULL,
  password          TEXT NOT NULL,        -- bcrypt hashed password
  telegram_user_id  BIGINT UNIQUE,        -- their personal Telegram account ID
  status            TEXT DEFAULT 'pending'
                    CHECK (status IN ('pending', 'active', 'paused', 'expired')),
  access_expiry     DATE,                 -- when platform access expires (set by admin)
  created_at        TIMESTAMPTZ DEFAULT now(),
  approved_at       TIMESTAMPTZ,
  approved_by       UUID REFERENCES admins(id)
);

-- Index for fast lookup by Telegram ID (used on every message)
CREATE INDEX IF NOT EXISTS idx_nutritionists_telegram_id ON nutritionists(telegram_user_id);


-- ─────────────────────────────────────────────────────────────────────
-- Table 3: clients
-- Each patient managed by a nutritionist.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nutritionist_id     UUID REFERENCES nutritionists(id) ON DELETE CASCADE,
  full_name           TEXT NOT NULL,
  telegram_user_id    BIGINT,             -- set after client joins the group
  telegram_phone      TEXT,               -- used to send invite link
  telegram_group_id   BIGINT UNIQUE,      -- the Telegram group created for this client
  program_type        TEXT,               -- e.g. "Weight Management", "PCOS"
  program_duration    INTEGER,            -- number of days
  program_start       DATE,
  program_end         DATE,               -- auto-computed: start + duration
  checkin_time        TIME DEFAULT '19:00:00',  -- daily check-in time (IST)
  diet_chart          TEXT,               -- plain text / markdown diet plan
  diet_chart_file_id  TEXT,               -- Telegram file_id if PDF was sent
  status              TEXT DEFAULT 'active'
                      CHECK (status IN ('active', 'paused', 'expired', 'completed')),
  caretaker_name      TEXT,
  caretaker_telegram  BIGINT,
  created_at          TIMESTAMPTZ DEFAULT now()
);

-- Indexes for fast lookups (used constantly)
CREATE INDEX IF NOT EXISTS idx_clients_nutritionist ON clients(nutritionist_id);
CREATE INDEX IF NOT EXISTS idx_clients_group_id ON clients(telegram_group_id);
CREATE INDEX IF NOT EXISTS idx_clients_telegram_user ON clients(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_clients_checkin_time ON clients(checkin_time);
CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);


-- ─────────────────────────────────────────────────────────────────────
-- Table 4: checkins
-- One record per client per day.
-- Tracks what the client said, what AI replied, and adherence status.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS checkins (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID REFERENCES clients(id) ON DELETE CASCADE,
  checkin_date      DATE NOT NULL,
  client_message    TEXT,                 -- what the client sent
  ai_reply          TEXT,                 -- what AI responded
  adherence_status  TEXT DEFAULT 'no_response'
                    CHECK (adherence_status IN ('on_track', 'partial', 'off_track', 'no_response')),
  -- Nutritionist can manually override the AI's classification
  override_status   TEXT CHECK (override_status IN ('on_track', 'partial', 'off_track', 'no_response', 'paused')),
  override_by       UUID REFERENCES nutritionists(id),
  override_at       TIMESTAMPTZ,
  caretaker_note    TEXT,                 -- observation logged by caretaker
  energy_level      INTEGER CHECK (energy_level BETWEEN 1 AND 5),
  created_at        TIMESTAMPTZ DEFAULT now(),
  -- Prevent duplicate checkins for the same day
  UNIQUE(client_id, checkin_date)
);

CREATE INDEX IF NOT EXISTS idx_checkins_client_date ON checkins(client_id, checkin_date DESC);


-- ─────────────────────────────────────────────────────────────────────
-- Table 5: pending_queries
-- Created when AI escalates a client message to the nutritionist.
-- Cleared when nutritionist resolves it.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pending_queries (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID REFERENCES clients(id) ON DELETE CASCADE,
  nutritionist_id   UUID REFERENCES nutritionists(id),
  client_message    TEXT NOT NULL,        -- the exact message that triggered escalation
  ai_assessment     TEXT,                 -- AI's reason for escalating
  ai_interim_reply  TEXT,                 -- interim message AI already sent to client
  doctor_reply      TEXT,                 -- nutritionist's response
  status            TEXT DEFAULT 'pending'
                    CHECK (status IN ('pending', 'resolved', 'ai_handled')),
  resolved_at       TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_queries_nutritionist_status ON pending_queries(nutritionist_id, status);
CREATE INDEX IF NOT EXISTS idx_queries_client ON pending_queries(client_id, status);


-- ─────────────────────────────────────────────────────────────────────
-- Table 6: messages
-- Full chat history for every client group.
-- Used by the web app to show the conversation timeline.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id       UUID REFERENCES clients(id) ON DELETE CASCADE,
  sender_role     TEXT NOT NULL
                  CHECK (sender_role IN ('client', 'ai', 'nutritionist', 'caretaker', 'system')),
  sender_name     TEXT,
  content         TEXT NOT NULL,
  telegram_msg_id BIGINT,                -- Telegram's internal message ID
  sent_at         TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_client_sent ON messages(client_id, sent_at DESC);


-- ─────────────────────────────────────────────────────────────────────
-- Table 7: ai_rules
-- Custom AI behavior instructions set by the nutritionist.
-- client_id = NULL means master rule (applies to all clients).
-- client_id = specific UUID means rule for that client only.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_rules (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nutritionist_id   UUID REFERENCES nutritionists(id) ON DELETE CASCADE,
  client_id         UUID REFERENCES clients(id) ON DELETE CASCADE,
                    -- NULL = master rule (all clients)
  category          TEXT CHECK (category IN ('tone', 'language', 'medical', 'caretaker', 'other')),
  rule_text         TEXT NOT NULL,
  is_active         BOOLEAN DEFAULT true,
  created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_rules_nutritionist ON ai_rules(nutritionist_id, is_active);
CREATE INDEX IF NOT EXISTS idx_ai_rules_client ON ai_rules(client_id, is_active);


-- ─────────────────────────────────────────────────────────────────────
-- Table 8: notification_log
-- Tracks all automated notifications sent (expiry, escalations, etc.)
-- Prevents duplicate notifications from being sent.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_log (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recipient_id  UUID,
  type          TEXT,   -- 'expiry_7d', 'expiry_3d', 'pending_query', 'checkin_sent', etc.
  reference_id  UUID,   -- related client_id or query_id
  message       TEXT,
  sent_at       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notif_log_recipient_type ON notification_log(recipient_id, type, sent_at DESC);


-- ─────────────────────────────────────────────────────────────────────
-- Table 9: app_config
-- Stores all app configuration (editable from admin UI).
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_config (
  key           TEXT PRIMARY KEY,
  value         TEXT NOT NULL,
  category      TEXT DEFAULT 'general',
  description   TEXT,
  is_secret     BOOLEAN DEFAULT false,
  updated_at    TIMESTAMPTZ DEFAULT now()
);

-- Insert default config values
INSERT INTO app_config (key, value, category, description, is_secret) VALUES
  ('TELEGRAM_BOT_TOKEN', '', 'telegram', 'Telegram Bot API Token', true),
  ('TELEGRAM_BOT_USERNAME', '@Test_nutritionist_bot', 'telegram', 'Bot username', false),
  ('SUPABASE_URL', '', 'supabase', 'Supabase project URL', true),
  ('SUPABASE_ANON_KEY', '', 'supabase', 'Supabase anonymous key', true),
  ('SUPABASE_SERVICE_KEY', '', 'supabase', 'Supabase service role key', true),
  ('GEMINI_API_KEY', '', 'ai', 'Google Gemini API key', true),
  ('GEMINI_MODEL', 'gemini-2.0-flash', 'ai', 'Gemini model name', false),
  ('JWT_SECRET', '', 'auth', 'JWT signing secret', true),
  ('JWT_EXPIRY_HOURS', '72', 'auth', 'Token expiry in hours', false),
  ('ADMIN_EMAIL', 'admin@nutricoach.in', 'admin', 'Admin login email', false),
  ('ADMIN_PASSWORD_HASH', '', 'admin', 'Admin password hash', true),
  ('APP_ENV', 'development', 'general', 'Environment (development/production)', false),
  ('WEBHOOK_URL', '', 'general', 'Production webhook URL', false),
  ('PORT', '8000', 'general', 'API server port', false)
ON CONFLICT (key) DO NOTHING;


-- =====================================================================
-- Done! All 9 tables created.
-- Next step: Go back to the project and fill in your .env file.
-- =====================================================================
