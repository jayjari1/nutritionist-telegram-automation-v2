"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiGet, apiPatch, apiDelete, apiPost } from "@/lib/api";
import Navbar from "@/components/Navbar";

interface Checkin {
  id: string;
  checkin_date: string;
  adherence_status: string;
  override_status: string | null;
  client_message: string | null;
  ai_reply: string | null;
  energy_level: number | null;
}

interface AiRule {
  id: string;
  category: string;
  rule_text: string;
  is_active: boolean;
}

interface ClientData {
  client: {
    id: string;
    full_name: string;
    program_type: string;
    program_duration: number;
    program_start: string;
    program_end: string;
    checkin_time: string;
    diet_chart: string;
    status: string;
    telegram_group_id: number | null;
    caretaker_name: string | null;
    caretaker_telegram: number | null;
  };
  today_checkin: Checkin | null;
  pending_queries_count: number;
}

function daysRemaining(endDate: string): number {
  const end = new Date(endDate);
  const now = new Date();
  return Math.max(0, Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)));
}

function AdherenceBadge({ status }: { status: string | null }) {
  const s = status || "no_response";
  const styles: Record<string, string> = {
    on_track: "bg-emerald-100 text-emerald-700",
    partial: "bg-amber-100 text-amber-700",
    off_track: "bg-red-100 text-red-700",
    no_response: "bg-gray-100 text-gray-500",
  };
  const labels: Record<string, string> = {
    on_track: "On Track",
    partial: "Partial",
    off_track: "Off Track",
    no_response: "No Response",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${styles[s]}`}>
      {labels[s]}
    </span>
  );
}

function getInviteCode(clientId: string): string {
  const clean = clientId.replace(/-/g, "").slice(0, 8).toUpperCase();
  return `NC-${clean}`;
}

const RULE_CATEGORIES = [
  { value: "tone", label: "Tone" },
  { value: "language", label: "Language" },
  { value: "medical", label: "Medical" },
  { value: "other", label: "Other" },
];

export default function ClientProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<ClientData | null>(null);
  const [checkins, setCheckins] = useState<Checkin[]>([]);
  const [rules, setRules] = useState<AiRule[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [editingDiet, setEditingDiet] = useState(false);
  const [dietText, setDietText] = useState("");
  const [editingCheckinTime, setEditingCheckinTime] = useState(false);
  const [checkinTime, setCheckinTime] = useState("");
  const [newRuleCategory, setNewRuleCategory] = useState("tone");
  const [newRuleText, setNewRuleText] = useState("");
  const [activeTab, setActiveTab] = useState<"overview" | "checkins" | "rules">("overview");

  useEffect(() => {
    if (!loading && !token) router.push("/auth/login");
  }, [loading, token, router]);

  useEffect(() => {
    if (token && id) {
      Promise.all([
        apiGet(`/clients/${id}`, token),
        apiGet(`/clients/${id}/checkins`, token),
        apiGet(`/rules/client/${id}`, token),
      ])
        .then(([clientData, checkinData, rulesData]) => {
          setData(clientData);
          setCheckins(checkinData);
          setRules(rulesData);
          setDietText(clientData.client.diet_chart || "");
          setCheckinTime(clientData.client.checkin_time || "19:00");
        })
        .catch(console.error)
        .finally(() => setLoadingData(false));
    }
  }, [token, id]);

  const handleOverride = async (status: string) => {
    if (!token) return;
    try {
      await apiPatch(`/clients/${id}/checkins/today`, { adherence_status: status }, token);
      const fresh = await apiGet(`/clients/${id}`, token);
      setData(fresh);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSaveDiet = async () => {
    if (!token) return;
    try {
      await apiPatch(`/clients/${id}`, { diet_chart: dietText }, token);
      setData((prev) => prev ? { ...prev, client: { ...prev.client, diet_chart: dietText } } : prev);
      setEditingDiet(false);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSaveCheckinTime = async () => {
    if (!token) return;
    try {
      const timeStr = checkinTime.length === 5 ? checkinTime + ":00" : checkinTime;
      await apiPatch(`/clients/${id}`, { checkin_time: timeStr }, token);
      setData((prev) => prev ? { ...prev, client: { ...prev.client, checkin_time: timeStr } } : prev);
      setEditingCheckinTime(false);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDeleteClient = async () => {
    if (!token) return;
    if (!confirm("Delete this client?")) return;
    try {
      await apiDelete(`/clients/${id}`, token);
      router.push("/dashboard");
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleAddRule = async () => {
    if (!token || !newRuleText.trim()) return;
    try {
      const result = await apiPost(`/rules/client/${id}`, {
        category: newRuleCategory,
        rule_text: newRuleText.trim(),
      }, token);
      setRules((prev) => [result.rule, ...prev]);
      setNewRuleText("");
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!token) return;
    try {
      await apiDelete(`/rules/${ruleId}`, token);
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleToggleRule = async (ruleId: string) => {
    if (!token) return;
    try {
      await apiPatch(`/rules/${ruleId}/toggle`, {}, token);
      setRules((prev) => prev.map((r) => (r.id === ruleId ? { ...r, is_active: !r.is_active } : r)));
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading || !token || loadingData) {
    return (
      <>
        <Navbar />
        <main className="pb-20 px-4 py-4">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-200 rounded w-1/3" />
            <div className="h-24 bg-gray-200 rounded-2xl" />
            <div className="h-12 bg-gray-200 rounded-xl" />
            <div className="h-12 bg-gray-200 rounded-xl" />
          </div>
        </main>
      </>
    );
  }

  if (!data) {
    return (
      <>
        <Navbar />
        <main className="pb-20 px-4 py-8 text-center">
          <p className="text-gray-500">Client not found</p>
        </main>
      </>
    );
  }

  const { client, today_checkin } = data;

  return (
    <>
      <Navbar />
      <main className="pb-20">
        {/* Header */}
        <div className="bg-white border-b border-gray-100 px-4 py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="p-2 -ml-2 text-gray-500"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div className="flex-1 min-w-0">
              <h1 className="text-lg font-bold text-gray-900 truncate">{client.full_name}</h1>
              <p className="text-sm text-gray-500">
                {client.program_type} · {daysRemaining(client.program_end)} days left
              </p>
            </div>
            <button
              onClick={handleDeleteClient}
              className="p-2 text-red-400 hover:text-red-600"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        <div className="px-4">
          {/* Quick Info */}
          <div className="grid grid-cols-2 gap-3 mt-4">
            <button
              onClick={() => {
                navigator.clipboard.writeText(`/join ${getInviteCode(client.id)}`);
                alert("Copied!");
              }}
              className="bg-blue-50 border border-blue-100 rounded-xl p-3 text-left active:bg-blue-100"
            >
              <p className="text-xs text-blue-600 mb-0.5">Setup</p>
              <p className="text-xs font-mono text-blue-800 truncate">/join {getInviteCode(client.id)}</p>
            </button>
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-3">
              <p className="text-xs text-gray-500 mb-0.5">Check-in</p>
              {editingCheckinTime ? (
                <div className="flex items-center gap-1">
                  <input
                    type="time"
                    value={checkinTime}
                    onChange={(e) => setCheckinTime(e.target.value)}
                    className="border rounded-lg px-1 py-0.5 text-xs w-20"
                  />
                  <button onClick={handleSaveCheckinTime} className="text-emerald-600 text-xs">Save</button>
                </div>
              ) : (
                <p
                  className="text-xs font-medium text-gray-900 truncate"
                  onClick={() => setEditingCheckinTime(true)}
                >
                  {client.checkin_time}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-3">
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-3">
              <p className="text-xs text-gray-500 mb-0.5">Telegram</p>
              <p className="text-xs font-medium text-gray-900">
                {client.telegram_group_id ? "Linked" : "Not linked"}
              </p>
            </div>
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-3">
              <p className="text-xs text-gray-500 mb-0.5">Caretaker</p>
              <p className="text-xs font-medium text-gray-900 truncate">
                {client.caretaker_name || "None"}
              </p>
            </div>
          </div>

          {/* Pending Alert */}
          {data.pending_queries_count > 0 && (
            <div className="bg-red-50 border border-red-100 text-red-700 px-3 py-2 rounded-xl text-xs mt-4">
              {data.pending_queries_count} pending query
            </div>
          )}

          {/* Tabs */}
          <div className="flex bg-gray-100 rounded-xl p-1 mt-4">
            {(["overview", "checkins", "rules"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors ${
                  activeTab === tab
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500"
                }`}
              >
                {tab === "overview" ? "Overview" : tab === "checkins" ? "Check-ins" : "Rules"}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="mt-4">
            {activeTab === "overview" && (
              <div className="space-y-4">
                {/* Today's Check-in */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                  <h3 className="font-semibold text-gray-900 text-sm mb-3">Today</h3>
                  {today_checkin ? (
                    <div>
                      <div className="mb-3">
                        <AdherenceBadge status={today_checkin.override_status || today_checkin.adherence_status} />
                      </div>
                      {today_checkin.client_message && (
                        <div className="bg-gray-50 p-3 rounded-xl text-sm mb-2">
                          <p className="text-xs text-gray-500 mb-1">Client</p>
                          <p className="text-gray-800">{today_checkin.client_message}</p>
                        </div>
                      )}
                      {today_checkin.ai_reply && (
                        <div className="bg-emerald-50 p-3 rounded-xl text-sm mb-3">
                          <p className="text-xs text-emerald-600 mb-1">AI</p>
                          <p className="text-gray-800">{today_checkin.ai_reply}</p>
                        </div>
                      )}
                      <div className="flex flex-wrap gap-2">
                        {["on_track", "partial", "off_track", "no_response"].map((s) => (
                          <button
                            key={s}
                            onClick={() => handleOverride(s)}
                            className={`text-xs px-3 py-1.5 rounded-lg border ${
                              (today_checkin.override_status || today_checkin.adherence_status) === s
                                ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                                : "border-gray-200 text-gray-600"
                            }`}
                          >
                            {s === "on_track" ? "On Track" : s === "partial" ? "Partial" : s === "off_track" ? "Off Track" : "No Response"}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No check-in yet</p>
                  )}
                </div>

                {/* Diet Chart */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-900 text-sm">Diet Chart</h3>
                    <button
                      onClick={() => setEditingDiet(!editingDiet)}
                      className="text-xs text-emerald-600 font-medium"
                    >
                      {editingDiet ? "Cancel" : "Edit"}
                    </button>
                  </div>
                  {editingDiet ? (
                    <div>
                      <textarea
                        value={dietText}
                        onChange={(e) => setDietText(e.target.value)}
                        className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm bg-gray-50"
                        rows={5}
                      />
                      <button
                        onClick={handleSaveDiet}
                        className="mt-2 bg-emerald-600 text-white px-4 py-2 rounded-xl text-sm font-medium w-full"
                      >
                        Save
                      </button>
                    </div>
                  ) : (
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-3 rounded-xl max-h-48 overflow-y-auto">
                      {client.diet_chart || "No diet chart"}
                    </pre>
                  )}
                </div>
              </div>
            )}

            {activeTab === "checkins" && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                {checkins.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">No check-ins yet</p>
                ) : (
                  <div className="space-y-2">
                    {checkins.slice(0, 14).map((c) => (
                      <div key={c.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900">{c.checkin_date}</p>
                          {c.client_message && (
                            <p className="text-xs text-gray-500 truncate">{c.client_message.slice(0, 60)}</p>
                          )}
                        </div>
                        <AdherenceBadge status={c.override_status || c.adherence_status} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "rules" && (
              <div className="space-y-3">
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                  <h3 className="font-semibold text-gray-900 text-sm mb-3">Add Rule</h3>
                  <div className="flex gap-2 mb-3">
                    <select
                      value={newRuleCategory}
                      onChange={(e) => setNewRuleCategory(e.target.value)}
                      className="border border-gray-200 rounded-lg px-2 py-2 text-xs bg-gray-50"
                    >
                      {RULE_CATEGORIES.map((cat) => (
                        <option key={cat.value} value={cat.value}>{cat.label}</option>
                      ))}
                    </select>
                    <input
                      type="text"
                      value={newRuleText}
                      onChange={(e) => setNewRuleText(e.target.value)}
                      placeholder="Rule text..."
                      className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-xs bg-gray-50"
                      onKeyDown={(e) => e.key === "Enter" && handleAddRule()}
                    />
                  </div>
                  <button
                    onClick={handleAddRule}
                    className="w-full bg-emerald-600 text-white py-2 rounded-xl text-xs font-medium"
                  >
                    Add Rule
                  </button>
                </div>

                {rules.length > 0 && (
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                    <h3 className="font-semibold text-gray-900 text-sm mb-3">Active Rules</h3>
                    <div className="space-y-2">
                      {rules.map((rule) => (
                        <div
                          key={rule.id}
                          className={`p-3 rounded-xl ${rule.is_active ? "bg-gray-50" : "bg-gray-100 opacity-60"}`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              <span className="text-xs bg-gray-200 px-2 py-0.5 rounded-lg">{rule.category}</span>
                              <p className="text-sm text-gray-700 mt-1">{rule.rule_text}</p>
                            </div>
                            <div className="flex gap-1 flex-shrink-0">
                              <button
                                onClick={() => handleToggleRule(rule.id)}
                                className={`text-xs px-2 py-1 rounded-lg ${rule.is_active ? "text-amber-600" : "text-emerald-600"}`}
                              >
                                {rule.is_active ? "Off" : "On"}
                              </button>
                              <button
                                onClick={() => handleDeleteRule(rule.id)}
                                className="text-xs text-red-500 px-2 py-1 rounded-lg"
                              >
                                Del
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
