/* ============================================================
   JS/DATA.JS — All Mock Data for the Demo
   ============================================================ */

const APP_DATA = {
  nutritionist: {
    name: "Dr. Priya Mehta",
    initials: "PM",
    specialty: "Clinical Nutritionist",
    avatar_color: "avatar",
  },

  clients: [
    {
      id: 1,
      name: "Ananya Sharma",
      initials: "AS",
      avatar_color: "avatar",
      plan_type: "Weight Management",
      plan_summary: "1400 kcal/day · No sugar · 3L water · High protein breakfast · Evening walk 30 mins",
      start_date: "2026-06-04",
      end_date: "2026-08-03",
      duration_days: 60,
      days_used: 33,
      days_left: 28,
      status: "active",         // active | expiring | expired | paused
      adherence_today: "on_track",
      energy_today: "high",
      last_checkin: "2 hrs ago",
      streak: 14,
      consistency: 87,
      needs_attention: false,
      caretaker: "Sunita Sharma (Mother)",
      ai_instructions: [
        { label: "Tone", text: "Be extra gentle — she gets anxious easily" },
        { label: "Language", text: "Hinglish is okay, she prefers it" },
        { label: "Avoid", text: "Don't mention exact calorie numbers directly" },
      ],
      history: [
        { date: "Jul 7", adherence: "on_track",  energy: "high",   mood: "Positive", summary: "Had all 3 meals, felt energetic. Evening walk completed." },
        { date: "Jul 6", adherence: "on_track",  energy: "medium", mood: "Calm",     summary: "Good adherence. Skipped afternoon snack but compensated with dinner." },
        { date: "Jul 5", adherence: "partial",   energy: "low",    mood: "Tired",    summary: "Skipped lunch due to meeting. Caretaker noted she seemed tired." },
        { date: "Jul 4", adherence: "on_track",  energy: "high",   mood: "Happy",    summary: "Perfect day — all meals, lots of water, walk done." },
        { date: "Jul 3", adherence: "partial",   energy: "medium", mood: "Okay",     summary: "Had 2 of 3 meals. Dinner was late but healthy." },
        { date: "Jul 2", adherence: "off_track", energy: "low",    mood: "Stressed", summary: "Skipped breakfast and lunch. Only had dinner. Caretaker noted stress at work." },
        { date: "Jul 1", adherence: "on_track",  energy: "high",   mood: "Motivated", summary: "Great start to the week. All targets met." },
      ],
      weekly_data: {
        adherence: [60, 71, 82, 78, 87, 91, 87],
        energy:    [3, 4, 3, 5, 4, 5, 4],
        labels:    ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7"],
      },
      pending_query: {
        id: "q1",
        time: "7:35 PM",
        question: "Can I take 1 scoop whey protein after dinner instead of evening walk? Knees hurting today.",
        status: "pending", // pending | resolved
        ai_reason: "Outside standard plan rules (calorie/macro substitution & pain reported). Clinical approval required."
      },
      todays_chat: [
        { role: "bot",        text: "Hey Ananya! 🌿 Kya aaj ke teeno meals ho gaye? I know evenings can get hectic — how did it go today?", time: "7:00 PM" },
        { role: "client",     text: "Haan, breakfast aur dinner accha raha! Lunch skip ho gaya tha meeting ki wajah se 😅", time: "7:24 PM" },
        { role: "caretaker",  text: "She seemed a bit tired in the evening but finished her dinner well. Had some salad too!", time: "7:31 PM" },
        { role: "bot",        text: "2 out of 3 is still really good progress! 💪 Glad dinner went well. Tomorrow, try to keep something small ready for lunch — even a quick snack counts. Rest well tonight!", time: "7:31 PM" },
        { role: "client",     text: "Also Dr. Priya / AI, can I take 1 scoop whey protein after dinner instead of evening walk? Knees hurting today.", time: "7:35 PM" },
        { role: "bot",        text: "I understand your knees are hurting, Ananya! 🌿 However, replacing an evening walk with whey protein changes both your calorie expenditure and protein intake in your specific Weight Management plan. Since this is a medical and dietary adjustment, **I have escalated this question to Dr. Priya for review.** She will reply to you here shortly! 👩‍⚕️", time: "7:35 PM" },
      ],
    },

    {
      id: 2,
      name: "Meera Patel",
      initials: "MP",
      avatar_color: "avatar-orange",
      plan_type: "Diabetic Management",
      plan_summary: "1600 kcal/day · Low GI foods · No refined sugar · 6 small meals · Regular glucose monitoring",
      start_date: "2026-06-01",
      end_date: "2026-07-10",
      duration_days: 40,
      days_used: 37,
      days_left: 3,
      status: "expiring",
      adherence_today: "off_track",
      energy_today: "low",
      last_checkin: "No response today",
      streak: 2,
      consistency: 58,
      needs_attention: true,
      flag_reason: "No response for 2 days + reported dizziness on Jul 5",
      caretaker: "Rajesh Patel (Husband)",
      ai_instructions: [
        { label: "Medical", text: "She has Type 2 diabetes — any symptom must immediately flag the nutritionist" },
        { label: "Tone", text: "Be very warm and non-judgmental — she is sensitive about her condition" },
      ],
      history: [
        { date: "Jul 7", adherence: "unclear",   energy: "not_mentioned", mood: "—",        summary: "No response received today." },
        { date: "Jul 6", adherence: "unclear",   energy: "not_mentioned", mood: "—",        summary: "No response received." },
        { date: "Jul 5", adherence: "off_track", energy: "low",           mood: "Unwell",   summary: "Reported dizziness and skipped 3 meals. ⚠️ Flagged." },
        { date: "Jul 4", adherence: "partial",   energy: "medium",        mood: "Okay",     summary: "Had 4 of 6 meals. Glucose reading high in the evening." },
        { date: "Jul 3", adherence: "on_track",  energy: "medium",        mood: "Positive", summary: "All meals on time. Husband confirmed good adherence." },
        { date: "Jul 2", adherence: "partial",   energy: "low",           mood: "Tired",    summary: "Skipped morning snack. Felt weak." },
        { date: "Jul 1", adherence: "on_track",  energy: "high",          mood: "Good",     summary: "Good day overall. All targets met." },
      ],
      weekly_data: {
        adherence: [70, 65, 72, 68, 60, 55, 45],
        energy:    [4, 3, 4, 3, 2, 2, 1],
        labels:    ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7"],
      },
      todays_chat: [
        { role: "bot", text: "Hi Meera! 🌸 Checking in for today — how are your meals going? Hope you're feeling better than yesterday.", time: "7:00 PM" },
      ],
    },
    {
      id: 3,
      name: "Riya Shah",
      initials: "RS",
      avatar_color: "avatar-purple",
      plan_type: "Post-Pregnancy Recovery",
      plan_summary: "1800 kcal/day · Iron-rich foods · Omega-3 focus · No crash dieting · Gentle movement only",
      start_date: "2026-05-25",
      end_date: "2026-08-22",
      duration_days: 90,
      days_used: 45,
      days_left: 45,
      status: "active",
      adherence_today: "partial",
      energy_today: "medium",
      last_checkin: "5 hrs ago",
      streak: 7,
      consistency: 74,
      needs_attention: false,
      caretaker: "Amit Shah (Husband)",
      ai_instructions: [
        { label: "Context", text: "New mother — be extra understanding about missed meals due to baby care" },
        { label: "Focus", text: "Always celebrate consistency, even partial adherence" },
      ],
      history: [
        { date: "Jul 7", adherence: "partial",  energy: "medium", mood: "Okay",     summary: "Had 2 of 3 meals. Baby kept her up at night — tired but trying." },
        { date: "Jul 6", adherence: "on_track", energy: "high",   mood: "Happy",    summary: "Great day! Husband helped with cooking. All meals done." },
        { date: "Jul 5", adherence: "partial",  energy: "low",    mood: "Tired",    summary: "Skipped lunch. Baby very fussy. Managed dinner." },
        { date: "Jul 4", adherence: "on_track", energy: "medium", mood: "Calm",     summary: "Good adherence. Iron-rich meal in the morning." },
        { date: "Jul 3", adherence: "partial",  energy: "medium", mood: "Stressed", summary: "2 meals only. Running low on sleep." },
        { date: "Jul 2", adherence: "on_track", energy: "high",   mood: "Motivated", summary: "Husband cooked, all meals on plan. Feeling strong!" },
        { date: "Jul 1", adherence: "partial",  energy: "low",    mood: "Tired",    summary: "Rough night. Managed breakfast only." },
      ],
      weekly_data: {
        adherence: [55, 62, 70, 68, 72, 74, 74],
        energy:    [2, 3, 4, 3, 4, 4, 3],
        labels:    ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7"],
      },
      todays_chat: [
        { role: "bot",       text: "Hey Riya! 💚 How's the little one today? And more importantly — how are YOU? Did you get a chance to eat today?", time: "7:00 PM" },
        { role: "client",    text: "Baby was a bit fussy today so lunch got skipped 😅 But had a good breakfast and dinner was nice!", time: "2:15 PM" },
        { role: "caretaker", text: "She's doing better in the evenings now. I'm making sure dinner is always ready. Iron daal is on the menu regularly!", time: "2:22 PM" },
        { role: "bot",       text: "Amit you're a star! 🌟 And Riya — 2 solid meals with iron-rich food is a win when you're managing a baby! Keep it up. Tomorrow, try to keep something small handy for lunch — even a quick fruit + nuts counts 🍎", time: "2:23 PM" },
      ],
    },
    {
      id: 4,
      name: "Kavita Joshi",
      initials: "KJ",
      avatar_color: "avatar-blue",
      plan_type: "PCOS Management",
      plan_summary: "1500 kcal/day · Anti-inflammatory foods · No processed carbs · Intermittent fasting 14:10 · Stress management",
      start_date: "2026-04-01",
      end_date: "2026-06-30",
      duration_days: 90,
      days_used: 90,
      days_left: 0,
      status: "expired",
      adherence_today: null,
      energy_today: null,
      last_checkin: "7 days ago",
      streak: 0,
      consistency: 81,
      needs_attention: false,
      caretaker: "None",
      ai_instructions: [],
      final_note: "Completed 90-day PCOS program. Excellent adherence — 81% consistency. Hormonal symptoms improved by week 6. Recommended to continue anti-inflammatory diet independently. Ready for Phase 2 program if she re-enrolls.",
      history: [
        { date: "Jun 30", adherence: "on_track", energy: "high",   mood: "Accomplished", summary: "Final day! All targets met. Great finish to the program." },
        { date: "Jun 29", adherence: "on_track", energy: "high",   mood: "Happy",        summary: "Strong finish. Intermittent fasting maintained perfectly." },
        { date: "Jun 28", adherence: "on_track", energy: "medium", mood: "Calm",         summary: "Good adherence. Anti-inflammatory meal prep done for the week." },
      ],
      weekly_data: {
        adherence: [65, 72, 78, 80, 82, 84, 81],
        energy:    [3, 4, 4, 5, 5, 5, 5],
        labels:    ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7"],
      },
      todays_chat: [],
    },
  ],

  alerts: [
    {
      client_id: 2,
      client_name: "Meera Patel",
      type: "danger",
      title: "No response for 2 days",
      detail: "Meera has not responded to daily check-ins on Jul 6 or Jul 7. Last flagged on Jul 5 for dizziness.",
      time: "Today, 7:00 PM",
      actions: ["Send Message", "Mark Reviewed", "Call Client"],
    },
    {
      client_id: 2,
      client_name: "Meera Patel",
      type: "warning",
      title: "Subscription expiring in 3 days",
      detail: "Meera's 40-day program ends on July 10, 2026. Follow up for renewal.",
      time: "Today",
      actions: ["Renew Plan", "Contact Client"],
    },
    {
      client_id: 3,
      client_name: "Riya Shah",
      type: "warning",
      title: "Consistency dropped this week",
      detail: "Riya's meal adherence dropped to 60% this week compared to 80% last week — baby routine disruption.",
      time: "Yesterday",
      actions: ["Send Encouragement", "Mark Reviewed"],
    },
  ],

  settings: {
    daily_checkin_time: "7:00 PM",
    weekly_checkin_day: "Sunday",
    weekly_checkin_time: "6:00 PM",
    timezone: "Asia/Kolkata (IST)",
    ai_tone: "Warm & Encouraging",
    language: "Auto-detect",
    expiry_alert_days: 7,
    notifications: {
      flag_alerts: true,
      no_response: true,
      daily_digest: true,
      expiry_reminders: true,
    },
  },

  // Client-side data (what the client sees)
  client_self: {
    id: 1,
    name: "Ananya",
    full_name: "Ananya Sharma",
    nutritionist: "Dr. Priya Mehta",
    plan_type: "Weight Management",
    plan_summary: "1400 kcal/day • No sugar • 3L water daily • High protein breakfast • Evening walk",
    start_date: "Jun 4, 2026",
    end_date: "Aug 3, 2026",
    days_left: 28,
    streak: 14,
    consistency: 87,
    caretaker: "Sunita (Mom)",
    todays_question: "Hey Ananya! 🌿 Kya aaj ke teeno meals ho gaye? I know evenings can get hectic — how did it go today?",
    todays_replied: true,
    week_data: {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      adherence: [1, 1, 0.5, 1, 1, 0.5, 1],
    },
    history: [
      { date: "Mon, Jul 7", adherence: "on_track", summary: "Had 2 of 3 meals. Evening walk done!", reply: "Haan, breakfast aur dinner accha raha! Lunch skip ho gaya tha 😅" },
      { date: "Sun, Jul 6", adherence: "on_track", summary: "Great day — all targets met!", reply: "Aaj sab kuch perfect raha! Teen meals, paani bhi 3 litre 💪" },
      { date: "Sat, Jul 5", adherence: "partial",  summary: "Tired day — missed lunch.", reply: "Lunch nahi ho paya, meeting thi. Dinner mein compensate kiya." },
      { date: "Fri, Jul 4", adherence: "on_track", summary: "Perfect adherence!", reply: "Best day this week! Everything on track 🎉" },
    ],
  },
};

// Helpers
function getClient(id) {
  return APP_DATA.clients.find(c => c.id === id);
}

function getAdherenceBadge(adherence) {
  const map = {
    on_track:  { cls: "badge-green",  text: "✅ On Track" },
    partial:   { cls: "badge-yellow", text: "⚠️ Partial" },
    off_track: { cls: "badge-red",    text: "❌ Off Track" },
    unclear:   { cls: "badge-gray",   text: "❓ No Response" },
  };
  return map[adherence] || map.unclear;
}

function getEnergyText(e) {
  const map = { high: "🔋 High", medium: "⚡ Medium", low: "🪫 Low", not_mentioned: "— Energy" };
  return map[e] || "—";
}

function getStatusBadge(status) {
  const map = {
    active:   { cls: "badge-green",  text: "✅ Active" },
    expiring: { cls: "badge-yellow", text: "⚠️ Expiring Soon" },
    expired:  { cls: "badge-red",    text: "🔴 Expired" },
    paused:   { cls: "badge-gray",   text: "⏸ Paused" },
  };
  return map[status] || map.active;
}
